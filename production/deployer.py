import json
import zipfile
import os
import yaml
from aws_clients import AWSClients
import hashlib
from botocore.exceptions import ClientError


class DeploymentConfig:
    def __init__(self, template_config_file, deployment_config_file):
        self.template_config_file = template_config_file
        self.deployment_config_file = deployment_config_file
        with open(template_config_file, "r") as template_config_fp:
            self.template_config = json.load(template_config_fp)
        with open(deployment_config_file, "r") as deployment_config_fp:
            self.deployment_config = yaml.load(deployment_config_fp)


class CfnDeployer:
    aws_clients = None

    def __init__(self, deployment_config: DeploymentConfig):
        self.deployment_config = deployment_config
        self.aws_clients = AWSClients()

    def package(self):
        for each_function in self.deployment_config.deployment_config["Functions"]:
            curr_dir = os.path.abspath(os.curdir)
            zip_path = self._zip_it(curr_dir, each_function)
            artifact_bucket, s3_key, s3_version_id = self._check_existing_package(zip_path, each_function)
            self._update_deployment_config(artifact_bucket, s3_key, s3_version_id)

    def _zip_it(self, curr_dir, each_function):
        dist_root = os.path.abspath(each_function["DistRoot"])
        os.chdir(dist_root)
        zip_path = os.path.join(curr_dir, each_function["LogicalResourceName"] + ".zip")
        with zipfile.ZipFile(zip_path, "w") as function_package_file:
            for root, sub_folders, files in os.walk("."):
                for a_file in files:
                    function_package_file.write(os.path.join(root, a_file))
        os.chdir(curr_dir)
        return zip_path

    def _check_existing_package(self, zip_path, each_function):
        s3_client = self.aws_clients.get_client("s3")
        project_name = self.deployment_config.deployment_config["ProjectName"]
        zip_s3_key = "lambda_artifacts/" + project_name + "/" + each_function["LogicalResourceName"] + ".zip"
        artifact_bucket = self.deployment_config.deployment_config["ArtifactBucket"]
        with open(zip_path, "r+b") as zipped_package:
            hash_md5 = hashlib.md5()
            for chunk in iter(lambda: zipped_package.read(4096), b""):
                hash_md5.update(chunk)
            new_file_hash = hash_md5.hexdigest()
        try:
            existing_object = s3_client.head_object(
                Bucket=artifact_bucket,
                Key=zip_s3_key
            )
            if existing_object["Metadata"]["md5sum"] == new_file_hash:
                print("ignore new package, use existing version")
                version_id = existing_object["VersionId"]
            else:
                version_id = self._do_upload(s3_client, zip_path, zip_s3_key, new_file_hash)
        except ClientError as ce:
            print(ce)
            print("assuming that object does not exist.")
            version_id = self._do_upload(s3_client, zip_path, zip_s3_key, new_file_hash)
        return artifact_bucket, zip_s3_key, version_id

    def _do_upload(self, s3_client, zip_path, zip_s3_key, new_file_hash):
        with open(zip_path, "r+b") as zipped_package:
            s3_client_upload = s3_client.put_object(
                Body=zipped_package,
                Bucket=self.deployment_config.deployment_config["ArtifactBucket"],
                Key=zip_s3_key,
                SSEKMSKeyId="a159e190-2bfb-4c2c-ad2d-246ef71050da",
                ServerSideEncryption="aws:kms",
                Metadata={
                    "md5sum": new_file_hash
                }
            )
        print(s3_client_upload)
        print(s3_client_upload["VersionId"])
        return s3_client_upload["VersionId"]

    def _update_deployment_config(self, bucket, key, id1):
        pass


class CmdLineInterface:
    pass
