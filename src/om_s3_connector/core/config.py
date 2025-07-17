# File: connectors/s3/config.py
"""
Configuration models for the S3 Connector to be used with OpenMetadata.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class SecurityProtocol(str, Enum):
    """Supported security protocols for S3 authentication."""
    AWS_IAM = "aws_iam"
    ACCESS_KEY = "access_key"
    STS_TOKEN = "sts_token"
    IAM_ROLE = "iam_role"


class S3SecurityConfig(BaseModel):
    """Security configuration for S3 connections."""
    
    protocol: SecurityProtocol = Field(
        default=SecurityProtocol.ACCESS_KEY,
        description="Authentication protocol to use"
    )
    
    # Access Key Authentication
    awsAccessKeyId: Optional[str] = Field(
        default=None,
        description="AWS Access Key ID for authentication"
    )
    
    awsSecretAccessKey: Optional[str] = Field(
        default=None,
        description="AWS Secret Access Key for authentication"
    )
    
    # STS Token Authentication
    awsSessionToken: Optional[str] = Field(
        default=None,
        description="AWS Session Token for temporary credentials"
    )
    
    # IAM Role Authentication
    roleArn: Optional[str] = Field(
        default=None,
        description="ARN of the IAM role to assume"
    )
    
    roleSessionName: Optional[str] = Field(
        default="openmetadata-s3-connector",
        description="Session name for role assumption"
    )
    
    externalId: Optional[str] = Field(
        default=None,
        description="External ID for role assumption (if required)"
    )
    
    # Profile-based Authentication
    profileName: Optional[str] = Field(
        default=None,
        description="AWS profile name to use from credentials file"
    )
    
    @field_validator('awsAccessKeyId', 'awsSecretAccessKey')
    @classmethod
    def validate_access_key_pair(cls, v, info):
        """Ensure both access key and secret are provided when using access key auth."""
        values = info.data if info.data else {}
        field_name = info.field_name
        
        if 'protocol' in values and values['protocol'] == SecurityProtocol.ACCESS_KEY:
            if field_name == 'awsAccessKeyId' and not v:
                raise ValueError("awsAccessKeyId is required when using access_key protocol")
            if field_name == 'awsSecretAccessKey' and not v:
                raise ValueError("awsSecretAccessKey is required when using access_key protocol")
        return v


class S3ConnectionConfig(BaseModel):
    """Connection configuration for S3 Connector."""
    
    # Basic Connection Settings
    awsRegion: str = Field(
        default="us-east-1",
        description="AWS region for S3 operations"
    )
    
    endPointURL: Optional[str] = Field(
        default=None,
        description="Custom S3 endpoint URL (for MinIO or S3-compatible services)"
    )
    
    bucketName: str = Field(
        description="Name of the S3 bucket to scan for metadata"
    )
    
    # Security Configuration
    securityConfig: S3SecurityConfig = Field(
        default_factory=S3SecurityConfig,
        description="Security configuration for S3 authentication"
    )
    
    # Connector-specific Settings
    fileFormats: List[str] = Field(
        default=["csv", "json", "parquet", "tsv", "orc", "avro"],
        description="List of file formats to process"
    )
    
    enablePartitionParsing: bool = Field(
        default=True,
        description="Enable automatic detection and parsing of Hive-style partitions"
    )
    
    sampleSize: int = Field(
        default=50,
        description="Number of rows to sample for data preview",
        ge=1,
        le=1000
    )
    
    # Filtering Settings
    includePathPattern: Optional[str] = Field(
        default=None,
        description="Regex pattern to include specific paths (optional)"
    )
    
    excludePathPattern: Optional[str] = Field(
        default=None,
        description="Regex pattern to exclude specific paths (optional)"
    )
    
    # Tagging Configuration
    tagMapping: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of path-to-tag mapping rules"
    )
    
    defaultTags: List[str] = Field(
        default_factory=list,
        description="Default tags to apply to all discovered tables"
    )
    
    # Performance Settings
    maxWorkers: int = Field(
        default=4,
        description="Maximum number of worker threads for parallel processing",
        ge=1,
        le=32
    )
    
    connectionTimeout: int = Field(
        default=30,
        description="Connection timeout in seconds",
        ge=1,
        le=300
    )
    
    readTimeout: int = Field(
        default=60,
        description="Read timeout in seconds",
        ge=1,
        le=600
    )
    
    # Advanced Settings
    enableMetrics: bool = Field(
        default=True,
        description="Enable collection of performance metrics"
    )
    
    enableDataProfiling: bool = Field(
        default=False,
        description="Enable data profiling for column statistics"
    )
    
    profilingBatchSize: int = Field(
        default=1000,
        description="Batch size for data profiling operations",
        ge=100,
        le=10000
    )
    
    # Hierarchical Folder Settings
    enableHierarchicalFolders: bool = Field(
        default=True,
        description="Enable hierarchical folder processing where folder levels become table names"
    )
    
    folderDepthForTables: int = Field(
        default=1,
        description="Depth level to use for table name extraction (1 = first level)",
        ge=1,
        le=5
    )
    
    includeSubfolderInfo: bool = Field(
        default=True,
        description="Include subfolder information in table descriptions and metadata"
    )


class S3ConnectorConfig(BaseModel):
    """Main configuration class for the S3 Connector."""
    
    type: str = Field(default="S3", description="Connector type identifier")
    connection: S3ConnectionConfig = Field(description="S3 connection configuration")
    
    class Config:
        """Pydantic configuration."""
        extra = "forbid"  # Prevent extra fields
        validate_assignment = True  # Validate on assignment
        use_enum_values = True  # Use enum values instead of enum objects
