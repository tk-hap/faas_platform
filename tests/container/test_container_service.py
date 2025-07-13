import boto3
import tarfile
import io

from moto import mock_aws
from faas.container import models


@mock_aws
def test_create_build_context():
    from faas.container.service import create_build_context

    # Setup test values
    bucket = "unittest"
    s3_client = boto3.client(service_name="s3", region_name="ap-southeast-2")
    # We need to create the bucket since this is all in Moto's 'virtual' AWS account
    s3_client.create_bucket(
        Bucket=bucket,
        CreateBucketConfiguration={"LocationConstraint": "ap-southeast-2"},
    )

    # Call function to test
    obj = create_build_context(
        s3_client=s3_client, tag="unittest", body="unittest", bucket=bucket
    )
    obj_bucket, obj_key = obj.strip("s3://").split("/", 1)

    # Assert the tarball contains handler.py
    response = s3_client.get_object(Bucket=obj_bucket, Key=obj_key)
    tar_bytes = response["Body"].read()
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tar:
        assert "handler.py" in tar.getnames()


def test_build_kaniko_pod_manifest():
    from faas.container.service import build_kaniko_pod_manifest

    # Setup test values
    build_context = "s3://unittest/unittest.tar.gz"
    container = models.ContainerImage(
        language="python", tag="kaniko-unittest-tag", registry="docker.io"
    )

    # Call function to test
    manifest = build_kaniko_pod_manifest(container, build_context)

    build_args = manifest["spec"]["containers"][0]["args"]

    # Check name has been updated
    assert manifest["metadata"]["name"] == container.tag

    # Check the build arguments have been updated
    assert build_args[1] == f"--context={build_context}"
    assert build_args[2] == f"--destination={container.registry}:{container.tag}"
