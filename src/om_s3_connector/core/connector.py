# File: connectors/s3/connector.py
# A simple helper class to interact with S3-compatible storage.

class S3Connector:
    """
    A wrapper class for the boto3 S3 client to simplify interactions.
    """
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, endpoint_url=None):
        """
        Initializes the boto3 client.
        """
        import boto3
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            endpoint_url=endpoint_url
        )

    def connect(self):
        """
        Tests the connection to the S3 endpoint by attempting to list buckets.
        """
        try:
            self.s3_client.list_buckets()
            return True
        except Exception as e:
            self.log_error(f"Connection failed: {e}")
            return False

    def list_objects(self, bucket_name):
        """
        Lists ALL objects in a bucket, automatically handling pagination
        for buckets containing more than 1000 objects.
        """
        all_objects = []
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name)
            for page in pages:
                if "Contents" in page:
                    all_objects.extend(page['Contents'])
        except Exception as e:
            self.log_error(f"Failed to list objects in bucket {bucket_name}: {e}")
        return all_objects
    
    def get_object_body(self, bucket_name, object_key):
        """
        Retrieves the content of an S3 object as bytes.
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=object_key)
            return response['Body'].read()
        except Exception as e:
            self.log_error(f"Failed to get object body for {object_key} in bucket {bucket_name}: {e}")
            return None

    def close(self):
        """
        Closes any open resources. (boto3 client does not require an explicit close).
        """
        pass

    def log_error(self, message):
        """
        Placeholder for a more robust error logging mechanism.
        """
        print(f"ERROR: {message}")
