"""
Core components of the S3 Connector.

This module contains the main connector logic, configuration, and client classes.
"""

from .s3_connector import S3Source
from .connector import S3Client
from .config import S3ConnectorConfig
from .security import SecurityHandler

__all__ = [
    "S3Source",
    "S3Client",
    "S3ConnectorConfig", 
    "SecurityHandler"
]
