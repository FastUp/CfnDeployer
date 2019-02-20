import boto3


class AWSClients:
    def __init__(self, profile_name: str = None, region_name: str = None):

        if profile_name and region_name:
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

