import pytest
from deployer import CfnDeployer
from deployer import *


def test_cfn_deployer_package():
    template = DeploymentConfig("./test_data/test_template_config_file.json", "./test_data/test_deployment_config.yaml")
    cfn_deployer = CfnDeployer(template)
    cfn_deployer.package()
