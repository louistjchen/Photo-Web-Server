import boto3
import time
import mysql.connector

from datetime import datetime, timedelta
import calendar


target_group = 'arn:aws:elasticloadbalancing:us-east-1:560806999447:targetgroup/a2targetgroup/2f5dcca03fdf3575'
ami_id = 'ami-09af13d8385ef9965'

db_config = {'user': 'master',
             'password': 'ece1779pass',
             'host': 'ece1779.c3z9wvey8adq.us-east-2.rds.amazonaws.com',
             'database': 'a2'}


def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db


cnx = get_db()
cursor = cnx.cursor()

cursor.execute("SELECT * FROM scale_params WHERE id = '{}';".format(1))

for row in cursor:
    max_threshold = row[1]
    min_threshold = row[2]
    increase_ratio = row[3]
    decrease_ratio = row[4]

print("Max threshold:"+ str(max_threshold))
print("Min threshold:"+ str(min_threshold))
print("Increase ratio:"+ str(max_threshold))
print("Decrease ratio:"+ str(max_threshold))


while 0:

    ec2 = boto3.resource('ec2')

    instances = ec2.instances.filter(
        Filters=[
            {'Name': 'tag:Group',
             'Values': ['User Instance']
             },

            {'Name': 'instance-state-name',
             'Values': ['running']
             },
        ])

    cpu_utilization = []
    ids = []

    for instance in instances:

        ids.append(instance.id)

        client = boto3.client('cloudwatch')

        cpu_1 = client.get_metric_statistics(
            Period=60,
            StartTime=datetime.utcnow() - timedelta(seconds=2 * 60),
            EndTime=datetime.utcnow() - timedelta(seconds=1 * 60),
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',
            Unit='Percent',
            Statistics=['Average'],
            Dimensions=[{'Name': 'InstanceId',
                         'Value': instance.id}]
        )

        for point in cpu_1['Datapoints']:
            load = point['Average']
            cpu_utilization.append(load)

    if len(cpu_utilization) != 0:

        average_cpu_utilization = sum(cpu_utilization) / len(cpu_utilization)

        print("Cpu Utilization: "+ str(cpu_utilization))
        print("Avg Cpu Utilization: "+str(average_cpu_utilization))
        print("IDs: "+str(ids))
        print("------------------------------------------")

        num_ins = len(ids)

        if average_cpu_utilization > max_threshold:

            num_ins_after_add = int(num_ins * increase_ratio)

            if num_ins_after_add > 19:
                print("Reach the max number of instances")
                print("------------------------------------------")
                num_ins_after_add = 19

            num_of_ins_to_add = num_ins_after_add - num_ins

            print("Condition: average_cpu_utilization > max_threshold")
            print("Num of instances: "+str(num_ins))
            print("Num of instances after expand: "+str(num_ins_after_add))
            print("Increase Ratio: "+str(increase_ratio))
            print("Max Threshold: "+str(max_threshold))
            print("Num of instances to add: "+str(num_of_ins_to_add))
            print("------------------------------------------")

            ts = calendar.timegm(time.gmtime())
            if num_of_ins_to_add > 0:
                try:
                    print("Adding instances...")
                    instances = ec2.create_instances(ImageId=ami_id,
                                                     InstanceType='t2.small',
                                                     MinCount = num_of_ins_to_add,
                                                     MaxCount = num_of_ins_to_add,
                                                     Monitoring={'Enabled': True},
                                                     SecurityGroups=[
                                                         'ece1779',
                                                     ],
                                                     KeyName='ece1779',
                                                     TagSpecifications=[
                                                         {
                                                             'ResourceType': 'instance',
                                                             'Tags': [
                                                                 {
                                                                     'Key': 'Group',
                                                                     'Value': 'User Instance'
                                                                 },
                                                                 {
                                                                     'Key': 'Name',
                                                                     'Value': str(ts)
                                                                 },
                                                             ]
                                                         },
                                                     ]
                                                     )

                    for instance in instances:
                        ec2 = boto3.resource('ec2')
                        instance.wait_until_running(
                            Filters=[
                                {
                                    'Name': 'instance-id',
                                    'Values': [
                                        instance.id,
                                    ]
                                },
                            ],
                        )

                        print("Registering instance with id:"+str(instance.id))
                        client = boto3.client('elbv2')
                        client.register_targets(
                            TargetGroupArn=target_group,
                            Targets=[
                                {
                                    'Id': instance.id,
                                },
                            ]
                        )

                        print("Waiting for instance with id:"+str(instance.id))
                        waiter = client.get_waiter('target_in_service')
                        waiter.wait(
                            TargetGroupArn=target_group,
                            Targets=[
                                {
                                    'Id': instance.id,
                                },
                            ],
                        )
                        print("Finished Registering for instance with id:"+str(instance.id))
                        print("------------------------------------------")
                except:
                        print("Failed to create instances due to reaching the max limit")
                        print("------------------------------------------")


        if average_cpu_utilization < min_threshold:

            num_ins_after_shrink = int(num_ins / decrease_ratio)

            num_of_ins_to_remove = num_ins - num_ins_after_shrink


            print("Condition: average_cpu_utilization < min_threshold")
            print("Num of instances: "+str(num_ins))
            print("Num of instances after shrink: "+str(num_ins_after_shrink))
            print("Decrease Ratio: "+str(decrease_ratio))
            print("Min Threshold: "+str(min_threshold))
            print("Num of instances to remove: "+str(num_of_ins_to_remove))
            print("------------------------------------------")

            if num_ins_after_shrink <=0:
                print("No need to remove the instance")
                print("------------------------------------------")

            if num_of_ins_to_remove > 0 and num_ins_after_shrink > 0:
                ids_to_remove = ids[:num_ins_after_shrink]

                for id in ids_to_remove:
                    print("Removing instance...")
                    ec2.instances.filter(InstanceIds=[id]).terminate()
                    print("Removed instance: "+ str(id))
    else:
        print("No CPU results")
        print("------------------------------------------")

    time.sleep(5)
