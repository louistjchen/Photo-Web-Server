import boto3
import time

from datetime import datetime, timedelta

target_group = 'arn:aws:elasticloadbalancing:us-east-1:560806999447:targetgroup/a2targetgroup/2f5dcca03fdf3575'


max_threshold = 70
min_threshold = 20

increase_rate = 1.25
decrease_rate = 0.75

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

    cpu_stats_1 = []
    ids = []

    for instance in instances:

        ids.append(instance.id)

        client = boto3.client('cloudwatch')

        cpu_1 = client.get_metric_statistics(
            Period=60,
            StartTime=datetime.utcnow() - timedelta(seconds=3 * 60),
            EndTime=datetime.utcnow() - timedelta(seconds=1 * 60),
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',
            Unit='Percent',
            Statistics=['Average'],
            Dimensions=[{'Name': 'InstanceId',
                         'Value': instance.id}]
        )

        for point in cpu_1['Datapoints']:
            print(point)
            load = point['Average']
            cpu_stats_1.append(load)

    average_load = sum(cpu_stats_1) / len(cpu_stats_1)

    print(cpu_stats_1)
    print(average_load)
    print(ids)

#     if average_load > max_threshold:
#         # the number of new ec2 instances
#         add_instance_num = int(len(cpu_stats_1) * (increase_rate-1)+1)
#         print("average_load > max_threshold")
#         print(add_instance_num)
#
#         # add instances
#         for i in range(add_instance_num) :
#             print("adding instance...")
#             ts = calendar.timegm(time.gmtime())
#             instances = ec2.create_instances(ImageId=config.ami_id, InstanceType='t2.small', MinCount=1, MaxCount=1,
#                                              Monitoring={'Enabled': True},
#                                              Placement={'AvailabilityZone': 'us-east-1'},
#                                              SecurityGroups=[
#                                                  'ece1779',
#                                              ],
#                                              KeyName='ece1779',
#                                              TagSpecifications=[
#                                                  {
#                                                      'ResourceType': 'instance',
#                                                      'Tags': [
#                                                          {
#                                                              'Key': 'Group',
#                                                              'Value': 'User Instance'
#                                                          },
#                                                          {
#                                                              'Key': 'Name',
#                                                              'Value': str(ts)
#                                                          },
#                                                      ]
#                                                  },
#                                              ]
#                                              )
#
#
#         # resize ELB
#         for instance in instances:
#             print(instance.id)
#             ec2 = boto3.resource('ec2')
#             instance.wait_until_running(
#                 Filters=[
#                     {
#                         'Name': 'instance-id',
#                         'Values': [
#                             instance.id,
#                         ]
#                     },
#                 ],
#             )
#
#             print(instance.id)
#             client = boto3.client('elbv2')
#             client.register_targets(
#                 TargetGroupArn=target_group,
#                 Targets=[
#                     {
#                         'Id': instance.id,
#                     },
#                 ]
#             )
#
#
#             # wait until finish
#             waiter = client.get_waiter('target_in_service')
#             waiter.wait(
#                 TargetGroupArn=target_group,
#                 Targets=[
#                     {
#                         'Id': instance.id,
#                     },
#                 ],
#             )
#
#
# # option 2
#     if average_load < min_threshold:
#         minus_instance_num = int(len(cpu_stats_1) * (1-decrease_rate))
#         print("average_load < max_threshold")
#         print(minus_instance_num)
#
#         if minus_instance_num > 0:
#             ids_to_delete = ids[:minus_instance_num]
#             print(ids_to_delete)
#
#             #resize ELB
#             for id in ids_to_delete:
#                 print("deleting instance...")
#                 print(id)
#                 client = boto3.client('elbv2')
#                 client.deregister_targets(
#                     TargetGroupArn=target_group,
#                     Targets=[
#                         {
#                             'Id': id,
#                         },
#                     ]
#                 )
#
#                 # wait until finish
#                 waiter = client.get_waiter('target_deregistered')
#                 waiter.wait(
#                     TargetGroupArn=target_group,
#                     Targets=[
#                         {
#                             'Id': id,
#                         },
#                     ],
#
#                 )
#
#             # drop instances
#             for id in ids_to_delete:
#                 print(id)
#                 ec2.instances.filter(InstanceIds=[id]).terminate()

    # wait for 1 minute
    time.sleep(5)
