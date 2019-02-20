from aws_clients import AWSClients
import getpass
import os
import yaml


def test_constructor():
    cred_file = getpass.getuser() + ".credentials.yaml"
    is_cred_file_exist = os.path.isfile(cred_file)
    print(is_cred_file_exist)
    if is_cred_file_exist:
        with open(cred_file, "r") as cred_file:
            cred_config = yaml.load(cred_file)
            aws_clients = AWSClients(profile_name=cred_config["ProfileName"], region_name=cred_config["RegionName"])
    else:
        aws_clients = AWSClients()
