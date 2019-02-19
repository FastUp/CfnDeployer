import json
import zipfile
import os
import yaml


class DeploymentConfig:
    def __init__(self, template_config_file, deployment_config_file):
        self.template_config_file = template_config_file
        self.deployment_config_file = deployment_config_file
        with open(template_config_file, "r") as template_config_fp:
            self.template_config = json.load(template_config_fp)
        with open(deployment_config_file, "r") as deployment_config_fp:
            self.deployment_config = yaml.load(deployment_config_fp)


class CfnDeployer:
    def __init__(self, deployment_config: DeploymentConfig):
        self.template = deployment_config

    def package(self):
        curr_dir = os.path.abspath(os.curdir)
        for each_function in self.template.deployment_config["Functions"]:
            os.chdir(curr_dir)
            dist_root = os.path.abspath(each_function["DistRoot"])
            os.chdir(dist_root)
            zip_path = os.path.join(curr_dir, each_function["LogicalResourceName"] + ".zip")
            with zipfile.ZipFile(zip_path, "w") as function_package_file:
                for root, sub_folders, files in os.walk("."):
                    for a_file in files:
                        function_package_file.write(os.path.join(root, a_file))


class CmdLineInterface:
    pass
