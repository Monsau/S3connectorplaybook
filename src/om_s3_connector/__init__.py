"""
S3 Connector for OpenMetadata

A comprehensive connector for ingesting metadata from S3-compatible storage systems.
"""

__version__ = "0.9"
__author__ = "Mustapha Fonsau"
__email__ = "mfonsau@talentys.eu"

from .core.s3_connector import S3Source
from .core.connector import S3Client
from .core.config import S3ConnectorConfig
from .parsers.factory import get_parser

__all__ = [
    "S3Source",
    "S3Client", 
    "S3ConnectorConfig",
    "get_parser"
]
