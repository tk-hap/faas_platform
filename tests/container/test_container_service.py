import boto3
import tarfile
import io

from moto import mock_aws

@mock_aws
def test_create_build_context():
    from faas.container.service import create_build_context

    bucket = "unittest"
    s3_client = boto3.client(service_name="s3", region_name="ap-southeast-2")
    # We need to create the bucket since this is all in Moto's 'virtual' AWS account
    s3_client.create_bucket(Bucket=bucket, CreateBucketConfiguration={
    'LocationConstraint': 'ap-southeast-2'})

    obj = create_build_context(s3_client=s3_client, tag="unittest", body="unittest", bucket=bucket)
    obj_bucket, obj_key = obj.strip("s3://").split("/", 1)

    # Assert the tarball contains handler.py
    response = s3_client.get_object(Bucket=obj_bucket, Key=obj_key)
    tar_bytes = response['Body'].read()
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tar:
        assert "handler.py" in tar.getnames()