from flask import render_template, redirect, url_for, request
from app import webapp

import boto3

AWSAccessKeyId = 'AKIAJJ3IQ3G2KAR3UR7Q'
AWSSecretKey = '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'

@webapp.route('/s3_bucket', methods=['GET'])
# Display an HTML list of all s3 buckets.
def s3_list():
    # Let's use Amazon S3
    s3 = boto3.resource('s3')

    # Print out bucket names
    bucket = s3.Bucket('photo-web-server')

    for key in bucket.objects.all():
        k = key
        print(k)

    keys = bucket.objects.all()

    return render_template("s3_examples/list.html", title="S3 Bucket Contents", bucket=bucket, keys=keys)


