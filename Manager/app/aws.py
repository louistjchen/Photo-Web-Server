import boto3
import calendar
import mysql.connector
import time
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, request, g
from operator import itemgetter
from threading import Thread

from app import config
from app import webapp
from app.db import *


def register_lb(instances):
    for instance in instances:
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
        elbv2 = boto3.client('elbv2')
        elbv2.register_targets(
            TargetGroupArn=config.target_group,
            Targets=[
                {
                    'Id': instance.id,
                },
            ]
        )

        waiter = elbv2.get_waiter('target_in_service')
        waiter.wait(
            TargetGroupArn=config.target_group,
            Targets=[
                {
                    'Id': instance.id,
                },
            ],
        )


@webapp.route('/workers/create', methods=['POST'])
def ec2_create():
    ec2 = boto3.resource('ec2')
    ts = calendar.timegm(time.gmtime())

    instances = ec2.create_instances(ImageId=config.ami_id,
                                     InstanceType='t2.small',
                                     MinCount=1,
                                     MaxCount=1,
                                     Monitoring={'Enabled': True},
                                     SecurityGroups=[
                                         'ece1779',
                                     ],
                                     KeyName='ece1779',
                                     TagSpecifications=[{
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
    thr = Thread(target=register_lb, args=[instances])
    thr.start()

    return redirect(url_for('ec2_list'))


@webapp.route('/workers/delete/<id>', methods=['POST'])
def ec2_delete(id):
    ec2 = boto3.resource('ec2')

    ec2.instances.filter(InstanceIds=[id]).terminate()

    # delete http request rate
    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("SELECT * FROM requests WHERE instanceid = '{}';".format(id))
    delete = []
    for row in cursor:
        delete.append(row[0])

    thr = Thread(target=delete_outdated, args=[delete])
    thr.start()

    return redirect(url_for('ec2_list'))


@webapp.route('/workers', methods=['GET'])
def ec2_list():
    ec2 = boto3.resource('ec2')

    instances = ec2.instances.filter(Filters=[{'Name': 'tag:Group', 'Values': ['User Instance']}])

    # for instance in instances:
    #
    #     print(instance.id, instance.image_id, instance.key_name, instance.tags)

    return render_template("ec2_list.html", instances=instances)


@webapp.route('/workers/<id>', methods=['GET'])
def ec2_details(id):
    ec2 = boto3.resource('ec2')

    instance = ec2.Instance(id)

    cloudwatch = boto3.client('cloudwatch')

    cpu = cloudwatch.get_metric_statistics(
        Period=60,
        StartTime=datetime.utcnow() - timedelta(seconds=60 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
        MetricName='CPUUtilization',
        Namespace='AWS/EC2',
        Unit='Percent',
        Statistics=['Average'],
        Dimensions=[{'Name': 'InstanceId',
                     'Value': id}]
    )

    print(cpu)
    cpu_stats = []

    for point in cpu['Datapoints']:
        time = point['Timestamp'].hour * 60 + point['Timestamp'].minute

        cpu_stats.append([time, point['Average']])

    cpu_stats = sorted(cpu_stats, key=itemgetter(0))

    cpu_labels = []
    cpu_values = []
    for cpu in cpu_stats:
        cpu_labels.append(str(int(cpu[0] / 60)) + ":" + str(cpu[0] % 60))
        cpu_values.append(cpu[1])

    requests = retrieve_http_request_rate(id)
    labels = []
    values = []
    for request in requests:
        labels.append(request[0])
        values.append(request[1])

    labels.reverse()
    values.reverse()

    return render_template("ec2_details.html", title="Instance Info",
                           instance=instance,
                           cpu_labels=cpu_labels,
                           cpu_values=cpu_values,
                           labels=labels,
                           values=values)


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


@webapp.route('/s3_list/delete', methods=['POST'])
def s3_delete():
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('photo-web-server')
    objects = bucket.objects.all()

    for object in objects:
        image_name = object.key
        s3.Object(config.s3_bucket, image_name).delete()

    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("""TRUNCATE TABLE users""")
    cnx.commit()

    cursor.execute("""TRUNCATE TABLE photos""")
    cnx.commit()

    return redirect(url_for('s3_list'))


@webapp.route('/s3_list', methods=['GET'])
def s3_list():
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(config.s3_bucket)

    objects = bucket.objects.all()

    return render_template("s3_list.html", bucket=bucket, objects=objects)

@webapp.route('/scale_params', methods=['GET'])
def show_scale_params():
    cnx = get_db()
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM scale_params WHERE id = '{}';".format(1))
    for row in cursor:
        max_threshold = float(row[1])
        min_threshold = float(row[2])
        increase_ratio = float(row[3])
        decrease_ratio = float(row[4])

    return render_template("scale_params.html", max_threshold = max_threshold,min_threshold=min_threshold,increase_ratio=increase_ratio,decrease_ratio=decrease_ratio, hidden="hidden")

@webapp.route('/scale_params', methods=['POST'])
def set_scale_params():
    max_threshold = float(request.form.get('max_threshold', ""))
    min_threshold = float(request.form.get('min_threshold', ""))
    increase_ratio = float(request.form.get('increase_ratio', ""))
    decrease_ratio = float(request.form.get('decrease_ratio', ""))

    ret_msg = ""
    if decrease_ratio <= 1:
        ret_msg = "Error: Decrease rato must be greater than 1"

    if increase_ratio <= 1:
        ret_msg = "Error: Increase rato must be greater than 1"

    if min_threshold <0 or min_threshold>100:
        ret_msg = "Error: Min Threshold must be between 0 and 100"

    if max_threshold <0 or max_threshold>100:
        ret_msg = "Error: Max Threshold must be between 0 and 100"

    if ret_msg != "":
        return render_template("scale_params.html", hidden="visible", ret_msg=ret_msg, max_threshold = max_threshold,min_threshold=min_threshold,increase_ratio=increase_ratio,decrease_ratio=decrease_ratio)
    else:

        cnx = get_db()
        cursor = cnx.cursor()
        cursor.execute('''UPDATE scale_params 
        SET max_threshold='{}',min_threshold='{}',increase_ratio='{}',decrease_ratio='{}' 
        WHERE id = '{}';'''.format(max_threshold,min_threshold,increase_ratio,decrease_ratio,1))
        cnx.commit()
        return render_template("scale_params.html", hidden="visible", ret_msg="Settings are updated", max_threshold = max_threshold,min_threshold=min_threshold,increase_ratio=increase_ratio,decrease_ratio=decrease_ratio)
