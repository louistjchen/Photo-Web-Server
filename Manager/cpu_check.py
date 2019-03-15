import boto3
import time

from datetime import datetime, timedelta

target_group = 'arn:aws:elasticloadbalancing:us-east-1:560806999447:targetgroup/a2targetgroup/2f5dcca03fdf3575'

max_threshold = 70
min_threshold = 20

increase_ratio = 2
decrease_ratio = 2

while True:

    # create connection to ec2
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

    average_cpu_utilization = sum(cpu_utilization) / len(cpu_utilization)

    print("Cpu Utilization: "+ str(cpu_utilization))
    print("Avg Cpu Utilization: "+average_cpu_utilization)
    print("IDs: "+ids)
    print("------------------------------------------")

    num_ins = len(instances)

    if average_cpu_utilization > max_threshold:

        num_ins_after_add =  num_ids * increase_ratio

        num_of_ins_to_add = num_ins - num_ins_after_add

        print("Condition: average_cpu_utilization > max_threshold")
        print("Num of instances: "+num_ins)
        print("Num of instances after expand: "+num_ins_after_add)
        print("Increase Ratio: "+increase_ratio)
        print("Num of instances to add: "+num_of_ins_to_add)
        print("------------------------------------------")

        for i in range(num_of_ins_to_add):
            print("Adding instance...")
            ts = calendar.timegm(time.gmtime())
            instances = ec2.create_instances(ImageId=config.ami_id,
                                             InstanceType='t2.small',
                                             MinCount=1,
                                             MaxCount=1,
                                             Monitoring={'Enabled': True},
                                             Placement={'AvailabilityZone': 'us-east-1'},
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
            print(instance.id)
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

            print(instance.id)
            client = boto3.client('elbv2')
            client.register_targets(
                TargetGroupArn=target_group,
                Targets=[
                    {
                        'Id': instance.id,
                    },
                ]
            )

            waiter = client.get_waiter('target_in_service')
            waiter.wait(
                TargetGroupArn=target_group,
                Targets=[
                    {
                        'Id': instance.id,
                    },
                ],
            )

    if average_cpu_utilization < min_threshold:

        num_ins_after_shrink = num_ids / decrease_ratio

        num_of_ins_to_remove = num_ins - num_ins_after_shrink


        print("Condition: average_cpu_utilization < min_threshold")
        print("Num of instances: "+num_ins)
        print("Num of instances after shrink: "+num_ins_after_shrink)
        print("Decrease Ratio: "+decrease_ratio)
        print("Num of instances to remove: "+num_of_ins_to_remove)
        print("------------------------------------------")

        if num_of_ins_to_remove > 0 and num_ins_after_shrink > 0:
            ids_to_remove = ids[:num_ins_after_shrink]

            for id in ids_to_remove:
                print("Removing instance...")
                print(id)
                ec2.instances.filter(InstanceIds=[id]).terminate()

    time.sleep(5)
