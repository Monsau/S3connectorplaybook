"""
Security management for S3 connector.
"""

from typing import Optional, Dict, Any
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class S3SecurityManager:
    """
    Manages security configurations and credentials for S3 connections.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize security manager with configuration.
        
        Args:
            config: Security configuration dictionary
        """
        self.config = config
        self.aws_access_key_id = config.get('awsAccessKeyId')
        self.aws_secret_access_key = config.get('awsSecretAccessKey')
        self.aws_session_token = config.get('awsSessionToken')
        self.aws_region = config.get('awsRegion', 'us-east-1')
        self.endpoint_url = config.get('endPointURL')
        self.verify_ssl = config.get('verifySSL', True)
        
    def get_boto3_session(self) -> boto3.Session:
        """
        Create and return a boto3 session with configured credentials.
        
        Returns:
            boto3.Session: Configured session
        """
        return boto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_session_token=self.aws_session_token,
            region_name=self.aws_region
        )
    
    def get_s3_client(self) -> boto3.client:
        """
        Create and return an S3 client with security configurations.
        
        Returns:
            boto3.client: Configured S3 client
        """
        session = self.get_boto3_session()
        
        # Create client configuration
        config = Config(
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        client_kwargs = {
            'config': config,
            'verify': self.verify_ssl
        }
        
        # Add custom endpoint URL if provided (for MinIO compatibility)
        if self.endpoint_url:
            client_kwargs['endpoint_url'] = self.endpoint_url
            
        return session.client('s3', **client_kwargs)
    
    def validate_credentials(self) -> bool:
        """
        Validate S3 credentials by attempting to list buckets.
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        try:
            client = self.get_s3_client()
            client.list_buckets()
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ['InvalidAccessKeyId', 'SignatureDoesNotMatch', 'TokenRefreshRequired']:
                return False
            raise
        except Exception:
            return False
    
    def test_bucket_access(self, bucket_name: str) -> bool:
        """
        Test access to a specific bucket.
        
        Args:
            bucket_name: Name of the bucket to test
            
        Returns:
            bool: True if bucket is accessible, False otherwise
        """
        try:
            client = self.get_s3_client()
            client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ['403', '404', 'NoSuchBucket']:
                return False
            raise
        except Exception:
            return False
    
    def get_bucket_region(self, bucket_name: str) -> Optional[str]:
        """
        Get the region of a specific bucket.
        
        Args:
            bucket_name: Name of the bucket
            
        Returns:
            str: Bucket region or None if not found
        """
        try:
            client = self.get_s3_client()
            response = client.get_bucket_location(Bucket=bucket_name)
            location = response.get('LocationConstraint')
            # If location is None, it means us-east-1
            return location if location else 'us-east-1'
        except Exception:
            return None
