import json
import zipfile
import os
import yaml
from .aws_clients import AWSClients
import hashlib
from botocore.exceptions import ClientError


class DeploymentConfig:
    def __init__(self, template_config_file, deployment_config_file):
        self.template_config_file = template_config_file
        self.deployment_config_file = deployment_config_file
        print(template_config_file)
        print(deployment_config_file)
        with open(template_config_file, "r") as template_config_fp:
            self.template_config = json.load(template_config_fp)
        with open(deployment_config_file, "r") as deployment_config_fp:
            self.deployment_config = yaml.load(deployment_config_fp)


class CfnDeployer:
    aws_clients = None

    def __init__(self, deployment_config: DeploymentConfig, aws_clients: AWSClients = None):
        self.deployment_config = deployment_config
        if not AWSClients:
            self.aws_clients = AWSClients()
        else:
            self.aws_clients = aws_clients

    def package(self):
        for each_function in self.deployment_config.deployment_config["Functions"]:
            curr_dir = os.path.abspath(os.curdir)
            zip_path = self._zip_it(curr_dir, each_function)
            artifact_bucket, s3_key, s3_version_id = self._check_existing_package(zip_path, each_function)
            self._update_deployment_config(each_function, artifact_bucket, s3_key, s3_version_id)

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
            existing_obj_hash = existing_object["Metadata"]["md5sum"]
            if existing_obj_hash == new_file_hash:
                print(
                    "No change to function " +
                    each_function["LogicalResourceName"] +
                    ". Will use existing version " +
                    existing_obj_hash
                )
                version_id = existing_object["VersionId"]
            else:
                version_id = self._do_upload(s3_client, zip_path, zip_s3_key, new_file_hash)
        except ClientError as ce:
            print(ce)
            print("Lambda function package zip does not exist. Will upload for the first time.")
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

    def _update_deployment_config(self, function_config, bucket, key, version_id):
        self.deployment_config.template_config["Parameters"][function_config["S3KeyParamName"]] = key
        self.deployment_config.template_config["Parameters"][function_config["S3ObjectVersionParamName"]] = version_id
        with open(self.deployment_config.template_config_file, "w") as template_config_file:
            json.dump(self.deployment_config.template_config, template_config_file)


class CmdLineInterface:
    pass


def run():
    import sys
    template_config_file_path = sys.argv[1]
    deployment_config_file_path = sys.argv[2]
    if len(sys.argv) > 4:
        credential_profile_name = sys.argv[3]
        credential_region_name = sys.argv[4]
        aws_clients = AWSClients(credential_profile_name, credential_region_name)
    else:
        aws_clients = AWSClients()
    deployment_config = DeploymentConfig(template_config_file_path, deployment_config_file_path)
    CfnDeployer(deployment_config, aws_clients).package()
