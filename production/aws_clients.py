import boto3


class AWSClients:
    session = boto3.Session()
    dynamo_db_client = session.client("dynamodb")
    dynamo_db_resource = session.resource("dynamodb")
    s3_client = session.client("s3")
    lambda_client = session.client("lambda")

    def __init__(self, profile_name: str = "default", region_name: str = "us-east-1"):

        if not profile_name == "default" or not region_name == "us-east-1":
            self.session = boto3.Session(
                profile_name=profile_name,
                region_name=region_name
            )
        else:
            self.session = boto3.Session()

    def get_client(self, service_name):
        return self.session.client(service_name)

    def get_resource(self, service_name):
        return self.session.resource(service_name)

# def set_credential_profile(profile_name):
#     session = boto3.Session(profile_name=profile_name)
#     dynamodb_client = session.client("dynamodb")
#     s3_client = session.client("s3")
#     lambda_client = session.client("lambda")
#     dynamodb_resource = session.resource("dynamodb")
#     table = dynamodb_resource.Table("AlarmsTriageState")
#     name = table.item_count
#     print(name)
# dynamodb = "session.client(\"dynamodb\")"
# s3 = "session.client(\"s3\")"
# lambda_client = "session.client(\"lambda\")"
