import pytest
from deployer import *
import getpass


@pytest.fixture
def aws_clients():
    cred_file = getpass.getuser() + ".credentials.yaml"
    is_cred_file_exist = os.path.isfile(cred_file)
    print(is_cred_file_exist)
    if is_cred_file_exist:
        with open(cred_file, "r") as cred_file:
            cred_config = yaml.load(cred_file)
            aws_clients = AWSClients(profile_name=cred_config["ProfileName"], region_name=cred_config["RegionName"])
    else:
        aws_clients = AWSClients()

    def _get_test_data():
        return aws_clients

    yield _get_test_data


def test_cfn_deployer_package(aws_clients):
    template = DeploymentConfig("./test_data/test_template_config_file.json", "./test_data/test_deployment_config.yaml")
    cfn_deployer = CfnDeployer(template)
    cfn_deployer.aws_clients = aws_clients()
    cfn_deployer.package()


def test_cfn_deployer__upload(aws_clients):
    template = DeploymentConfig("./test_data/test_template_config_file.json", "./test_data/test_deployment_config.yaml")
    cfn_deployer = CfnDeployer(template)
    cfn_deployer.aws_clients = aws_clients()
    cfn_deployer._check_existing_package()
