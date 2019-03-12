from flask import render_template, redirect, url_for, request, g
from app import webapp
from app.db import *

import boto3
import calendar
import time

from app import config
from app.config import db_config, target_group

from datetime import datetime, timedelta
from operator import itemgetter
import mysql.connector


@webapp.route('/ec2_worker/create', methods=['POST'])
# Start a new EC2 instance
def ec2_create():
    # create connection to ec2
    ec2 = boto3.resource('ec2',region_name='us-east-1')
    ts = calendar.timegm(time.gmtime())

    instances = ec2.create_instances(ImageId=config.ami_id, InstanceType='t2.small', MinCount=1, MaxCount=1,
                         Monitoring={'Enabled': True},
                         SecurityGroups=[
                             'ece1779',
                         ],
                         KeyName='ece1779', TagSpecifications=[
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
                            }, ])

    # resize ELB
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
            TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:560806999447:targetgroup/a2targetgroup/2f5dcca03fdf3575',
            Targets=[
                {
                    'Id': instance.id,
                },
            ]
        )

        # wait until finish
        waiter = client.get_waiter('target_in_service')
        waiter.wait(
            TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:560806999447:targetgroup/a2targetgroup/2f5dcca03fdf3575',
            Targets=[
                {
                    'Id': instance.id,
                },
            ],
        )

    return redirect(url_for('ec2_list'))


@webapp.route('/ec2_worker/delete/<id>', methods=['POST'])
# Terminate a EC2 instance
def ec2_destroy(id):

    ec2 = boto3.resource('ec2')

    ec2.instances.filter(InstanceIds=[id]).terminate()

    return redirect(url_for('ec2_list'))


@webapp.route('/ec2_worker', methods=['GET'])
# Display an HTML list of all ec2 instances
def ec2_list():

    # create connection to ec2
    ec2 = boto3.resource('ec2')

    instances = ec2.instances.filter(
      Filters=[{'Name': 'tag:Group', 'Values': ['User Instance']}])

    for instance in instances:

        print(instance.id, instance.image_id, instance.key_name, instance.tags)

    return render_template("workers/list.html", title="EC2 Instances", instances=instances)


@webapp.route('/ec2_worker/<id>', methods=['GET'])
# Display details about a specific instance.
def ec2_view(id):

    print(id)
    ec2 = boto3.resource('ec2')

    # acquire an EC2 instance
    instance = ec2.Instance(id)

    # Create CloudWatch client
    client = boto3.client('cloudwatch')

    metric_name = 'CPUUtilization'
    namespace = 'AWS/EC2'
    statistic = 'Average'  # could be Sum,Maximum,Minimum,SampleCount,Average

    # request syntax / get cpu statistics
    cpu = client.get_metric_statistics(
        Period=60,
        StartTime=datetime.utcnow() - timedelta(seconds=61 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=1 * 60),
        MetricName=metric_name,
        Namespace=namespace,  # Unit='Percent',
        Statistics=[statistic],
        Dimensions=[{'Name': 'InstanceId',
                     'Value': id}]

    )

    # print(cpu)

    # gather return statistics
    cpu_stats = []

    for point in cpu['Datapoints']:
        hour = point['Timestamp'].hour
        # print(hour)
        minute = point['Timestamp'].minute
        # print(minute)
        time = hour + minute/60
        # print(time)
        # print(point)
        cpu_stats.append([time, point['Average']])

    # print(cpu_stats)

    cpu_stats = sorted(cpu_stats, key=itemgetter(0))
    print(cpu_stats)

    requests = retrieve_http_request_rate(id)

    return render_template("workers/view.html", title="Instance Info",
                           instance=instance,
                           cpu_stats=cpu_stats,
                           http_req=requests)


# connect the database
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


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@webapp.route('/s3/delete', methods=['POST'])
# delete all files in s3 bucket and the data in RDS
def delete():

    s3 = boto3.resource('s3')
    bucket = s3.Bucket('photo-web-server')

    keys = bucket.objects.all()

    for k in keys:
        image_name = k.key
        s3.Object('photo-web-server', image_name).delete()

    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("""TRUNCATE TABLE users""")
    cnx.commit()

    cursor.execute("""TRUNCATE TABLE photos""")
    cnx.commit()

    return redirect(url_for('s3_list'))

