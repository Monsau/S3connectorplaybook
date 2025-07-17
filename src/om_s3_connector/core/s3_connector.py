# File: src/s3_connector/core/s3_connector.py
# Enhanced S3 Connector with OpenMetadata security configuration support.

"""
This module defines a custom OpenMetadata source connector (S3Source)
capable of scanning an S3-compatible bucket (like MinIO), discovering
files, and ingesting them as tables into OpenMetadata.

Enhanced with security configuration support for various AWS authentication methods.
"""

import os
import re
import pandas as pd
from typing import Iterable, Optional, List, Dict
from collections import defaultdict

from ..parsers.factory import ParserFactory
from .config import S3ConnectionConfig, S3SecurityConfig, SecurityProtocol
from .security import S3SecurityManager
from .connector import S3Connector

# --- OpenMetadata Imports ---
from metadata.generated.schema.entity.services.databaseService import DatabaseService, DatabaseConnection
from metadata.generated.schema.entity.data.table import Column, DataType, TableData
from metadata.generated.schema.entity.data.database import Database
from metadata.generated.schema.entity.data.databaseSchema import DatabaseSchema
from metadata.generated.schema.type.tagLabel import TagLabel, LabelType, State, TagSource
from metadata.generated.schema.api.data.createDatabase import CreateDatabaseRequest
from metadata.generated.schema.api.data.createDatabaseSchema import CreateDatabaseSchemaRequest
from metadata.generated.schema.api.data.createTable import CreateTableRequest
from metadata.generated.schema.api.services.createDatabaseService import CreateDatabaseServiceRequest
from metadata.generated.schema.metadataIngestion.workflow import Source as WorkflowSource
from metadata.ingestion.api.models import Either, StackTraceError
from metadata.ingestion.api.steps import Source
from metadata.ingestion.ometa.ometa_api import OpenMetadata
from metadata.utils.logger import ingestion_logger

logger = ingestion_logger()

# Mapping from pandas dtypes to OpenMetadata DataTypes
PANDAS_TO_OM_TYPE = {
    "object": DataType.STRING, "int64": DataType.INT, "float64": DataType.FLOAT,
    "bool": DataType.BOOLEAN, "datetime64[ns]": DataType.DATETIME,
    "timedelta[ns]": DataType.TIME, "category": DataType.STRING,
}


class S3Source(Source):
    """
    Enhanced OpenMetadata Source for S3/MinIO buckets with security configuration support.

    Key Features:
    1.  File Discovery: Scans a bucket for files with configurable extensions.
    2.  Schema Parsing: Infers column schemas for supported formats.
    3.  Partition Handling: Intelligently groups Hive-style partitioned files into a single logical table.
    4.  Sample Data Ingestion: Ingests a configurable number of rows for previewing in the UI.
    5.  Automatic Tagging: Applies tags to tables based on configurable rules.
    6.  Security Support: Multiple AWS authentication methods (Access Keys, IAM Roles, STS Tokens, etc.)
    """

    def __init__(self, config: WorkflowSource, metadata: OpenMetadata):
        """
        Initializes the connector with the configuration from the workflow YAML.
        """
        super().__init__()
        self.config = config
        self.metadata = metadata
        
        # Extract configuration from OpenMetadata format
        service_connection_config = config.serviceConnection.root.config
        connection_options = service_connection_config.connectionOptions.root if hasattr(service_connection_config, 'connectionOptions') else {}
        
        # Parse the new configuration format
        self._parse_connection_config(connection_options)
        
        # Initialize security manager
        self.security_manager = S3SecurityManager(
            security_config=self.security_config,
            region=self.aws_region
        )
        
        # Initialize enhanced S3 connector
        self.s3_connector = None
        self._initialize_s3_connector()
        
        logger.info(f"S3Source initialized with security protocol: {self.security_config.protocol}")
        logger.info(f"Supported file formats: {self.supported_formats}")
        logger.info(f"Partition parsing enabled: {self.enable_partition_parsing}")
        logger.info(f"Sample data size: {self.sample_size}")

    def _parse_connection_config(self, connection_options: Dict):
        """Parse connection configuration from OpenMetadata format."""
        # Basic connection settings
        self.aws_region = connection_options.get("awsRegion", "us-east-1")
        self.endpoint_url = connection_options.get("endPointURL")
        self.bucket_name = connection_options.get("bucketName")
        self.service_name = self.config.serviceName
        
        # Security configuration
        security_protocol = connection_options.get("securityProtocol", "access_key")
        self.security_config = S3SecurityConfig(
            protocol=SecurityProtocol(security_protocol),
            awsAccessKeyId=connection_options.get("awsAccessKeyId"),
            awsSecretAccessKey=connection_options.get("awsSecretAccessKey"),
            awsSessionToken=connection_options.get("awsSessionToken"),
            roleArn=connection_options.get("roleArn"),
            roleSessionName=connection_options.get("roleSessionName", "openmetadata-s3-connector"),
            externalId=connection_options.get("externalId"),
            profileName=connection_options.get("profileName")
        )
        
        # Connector settings
        formats_str = connection_options.get("file_formats", "csv,json,parquet,tsv")
        self.supported_formats = [f.strip().lower() for f in formats_str.split(',')]
        
        partition_parsing_str = connection_options.get("enable_partition_parsing", "true")
        self.enable_partition_parsing = partition_parsing_str.lower() == 'true'
        
        sample_size_str = connection_options.get("sample_size", "50")
        try:
            self.sample_size = int(sample_size_str)
        except ValueError:
            logger.warning(f"Invalid sample_size '{sample_size_str}'. Defaulting to 50.")
            self.sample_size = 50

        # Parse tag mapping
        self.tag_mapping = []
        tag_mapping_str = connection_options.get("tag_mapping")
        if tag_mapping_str:
            try:
                rules = tag_mapping_str.split(';')
                for rule in rules:
                    if not rule: continue
                    parts = rule.split(':', 1)
                    if len(parts) == 2:
                        self.tag_mapping.append({
                            "path_keyword": parts[0].strip(), 
                            "tag_fqn": parts[1].strip()
                        })
            except Exception as e:
                logger.warning(f"Could not parse tag_mapping configuration. Error: {e}")

        # Default tags
        default_tags_str = connection_options.get("default_tags", "")
        self.default_tags = [tag.strip() for tag in default_tags_str.split(',') if tag.strip()]
        
        # Performance settings
        self.max_workers = int(connection_options.get("maxWorkers", 4))
        self.connection_timeout = int(connection_options.get("connectionTimeout", 30))
        self.read_timeout = int(connection_options.get("readTimeout", 60))
        
        # Path filtering
        self.include_path_pattern = connection_options.get("includePathPattern")
        self.exclude_path_pattern = connection_options.get("excludePathPattern")
        
        # Advanced options
        self.enable_metrics = connection_options.get("enableMetrics", "true").lower() == "true"
        self.enable_data_profiling = connection_options.get("enableDataProfiling", "false").lower() == "true"
        self.profiling_batch_size = int(connection_options.get("profilingBatchSize", 1000))
        
        # Hierarchical folder settings
        self.enable_hierarchical_folders = connection_options.get("enableHierarchicalFolders", "true").lower() == "true"
        self.folder_depth_for_tables = int(connection_options.get("folderDepthForTables", 1))
        self.include_subfolder_info = connection_options.get("includeSubfolderInfo", "true").lower() == "true"

    def _initialize_s3_connector(self):
        """Initialize the S3 connector with security configuration."""
        try:
            # Test connection first
            if not self.security_manager.test_connection(self.endpoint_url):
                raise ValueError("S3 connection test failed")
            
            # Get S3 client from security manager
            s3_client = self.security_manager.get_s3_client(self.endpoint_url)
            
            # Create enhanced S3 connector wrapper
            self.s3_connector = EnhancedS3Connector(
                s3_client=s3_client,
                security_manager=self.security_manager
            )
            
            # Log credentials info (safe for logging)
            creds_info = self.security_manager.get_credentials_info()
            logger.info(f"S3 connection established using {creds_info.get('protocol')} authentication")
            
        except Exception as e:
            logger.error(f"Failed to initialize S3 connector: {str(e)}")
            raise
        
    @classmethod
    def create(cls, config_dict: dict, metadata: OpenMetadata, pipeline_name: Optional[str] = None) -> "S3Source":
        """Factory method called by OpenMetadata to create an instance."""
        config = WorkflowSource.model_validate(config_dict)
        return cls(config, metadata)

    def prepare(self):
        """Preliminary checks before ingestion starts."""
        if not self.bucket_name:
            raise ValueError("bucketName is a required field.")
        
        # Test connection and log credentials info
        creds_info = self.security_manager.get_credentials_info()
        logger.info(f"Using AWS identity: {creds_info.get('arn', 'Unknown')}")
        
        if not self.s3_connector:
            raise ValueError("S3 connector not properly initialized.")

    def _apply_path_filters(self, object_key: str) -> bool:
        """Apply include/exclude path filters."""
        if self.include_path_pattern:
            if not re.search(self.include_path_pattern, object_key):
                return False
        
        if self.exclude_path_pattern:
            if re.search(self.exclude_path_pattern, object_key):
                return False
        
        return True

    def _get_columns_from_dataframe(self, df: pd.DataFrame) -> List[Column]:
        """Infers OpenMetadata columns from a pandas DataFrame."""
        columns = []
        for col_name, col_type in df.dtypes.items():
            om_type = PANDAS_TO_OM_TYPE.get(str(col_type).lower(), DataType.STRING)
            columns.append(Column(name=str(col_name), dataType=om_type))
        return columns

    def _group_files(self, objects: List[Dict]) -> Dict[str, Dict]:
        """
        Groups S3 objects into logical tables with enhanced hierarchical folder support.
        
        Strategy:
        1. First-level folders become table names (e.g., "users", "orders", "products")
        2. Subfolders are treated as complementary data (partitions, variants, etc.)
        3. Files directly in root are grouped by filename (legacy behavior)
        4. Supports both Hive-style partitioning and hierarchical organization
        """
        grouped_files = defaultdict(lambda: {
            "files": [], 
            "partitions": set(), 
            "subfolders": set(),
            "folder_structure": "flat"  # "flat", "hierarchical", or "mixed"
        })
        partition_regex = re.compile(r"([^/]+)=([^/]+)")
        
        for obj in objects:
            obj_key = obj.get('Key')
            if not obj_key or obj_key.endswith('/'):
                continue
                
            # Apply path filtering
            if not self._apply_path_filters(obj_key):
                continue
                
            file_format = os.path.splitext(obj_key)[1].lstrip('.').lower()
            if file_format not in self.supported_formats:
                continue
            
            # Parse the path structure
            path_parts = obj_key.split('/')
            file_name = path_parts[-1]
            base_name = os.path.splitext(file_name)[0]
            
            # Determine logical table name based on folder structure
            logical_table_name = None
            folder_structure = "flat"
            
            if len(path_parts) > 1 and self.enable_hierarchical_folders:
                # File is in a subfolder - use configured depth for table name
                folder_depth = min(self.folder_depth_for_tables, len(path_parts) - 1)
                table_folder_parts = path_parts[:folder_depth]
                logical_table_name = '/'.join(table_folder_parts)
                folder_structure = "hierarchical"
                
                # Track subfolder structure for metadata if enabled
                if self.include_subfolder_info and len(path_parts) > folder_depth + 1:
                    subfolder_path = '/'.join(path_parts[folder_depth:-1])
                    grouped_files[logical_table_name]["subfolders"].add(subfolder_path)
            else:
                # File is in root - use filename as table name (legacy behavior)
                logical_table_name = base_name
                folder_structure = "flat"
            
            # Handle partition parsing
            if self.enable_partition_parsing:
                found_partitions = partition_regex.findall(obj_key)
                if found_partitions:
                    # Extract partition keys
                    for key, value in found_partitions:
                        grouped_files[logical_table_name]["partitions"].add(key)
                    
                    # For hierarchical structure, refine table name if needed
                    if folder_structure == "hierarchical":
                        # Check if partitions are in the first folder level
                        first_partition_str = f"{found_partitions[0][0]}={found_partitions[0][1]}"
                        if first_partition_str in path_parts[0]:
                            # Partitions start at root level - use base path as table name
                            base_path = obj_key.split(first_partition_str, 1)[0]
                            logical_table_name = os.path.basename(base_path.strip('/')) or "partitioned_data"
                            folder_structure = "partitioned"
            
            # Store file information
            grouped_files[logical_table_name]["files"].append(obj_key)
            grouped_files[logical_table_name]["folder_structure"] = folder_structure
            
            logger.debug(f"Grouped file '{obj_key}' under table '{logical_table_name}' "
                        f"(structure: {folder_structure})")
        
        # Log grouping summary
        for table_name, info in grouped_files.items():
            file_count = len(info["files"])
            partition_count = len(info["partitions"])
            subfolder_count = len(info["subfolders"])
            structure = info["folder_structure"]
            
            logger.info(f"Table '{table_name}': {file_count} files, "
                       f"{partition_count} partitions, {subfolder_count} subfolders "
                       f"(structure: {structure})")
            
            if subfolder_count > 0:
                logger.debug(f"  Subfolders: {sorted(info['subfolders'])}")
        
        return grouped_files

    def _get_tags_for_path(self, path: str) -> List[TagLabel]:
        """Returns a list of TagLabel objects to apply to a table."""
        tags = []
        
        # Apply path-based tags
        for rule in self.tag_mapping:
            keyword = rule.get("path_keyword")
            tag_fqn = rule.get("tag_fqn")
            if keyword and tag_fqn and keyword in path:
                tags.append(TagLabel(
                    tagFQN=tag_fqn,
                    source=TagSource.Classification,
                    labelType=LabelType.Manual,
                    state=State.Confirmed
                ))
                logger.debug(f"Tag '{tag_fqn}' applied to path '{path}' due to keyword '{keyword}'")
        
        # Apply default tags
        for tag_fqn in self.default_tags:
            tags.append(TagLabel(
                tagFQN=tag_fqn,
                source=TagSource.Classification,
                labelType=LabelType.Manual,
                state=State.Confirmed
            ))
        
        return tags

    def next_record(self) -> Iterable[Either[dict]]:
        """
        Main generator that orchestrates the ingestion.
        """
        try:
            service_entity = self._get_or_create_service()
            if not service_entity: raise Exception("The service could not be created.")
            
            all_objects = self.s3_connector.list_objects(self.bucket_name)
            logical_tables = self._group_files(all_objects)
            database_entity = self._get_or_create_database(service_entity)
            schema_entities_cache = {}

            for table_name, table_info in logical_tables.items():
                representative_path = table_info["files"][0]
                partition_keys = sorted(list(table_info["partitions"]))
                folder_structure = table_info.get("folder_structure", "flat")
                subfolders = sorted(list(table_info.get("subfolders", set())))
                
                # Determine schema name based on folder structure
                if folder_structure == "hierarchical":
                    # For hierarchical structure, use the table name as schema (first-level folder)
                    schema_name = table_name
                else:
                    # For flat structure, use directory or default
                    path_parts = os.path.dirname(representative_path).split('/')
                    schema_name = path_parts[0] if path_parts and path_parts[0] else "default"

                if schema_name not in schema_entities_cache:
                    schema_entities_cache[schema_name] = self._get_or_create_schema(database_entity, schema_name)
                schema_entity = schema_entities_cache[schema_name]
                
                try:
                    file_format = os.path.splitext(representative_path)[1].lstrip('.').lower()
                    parser = ParserFactory.get_parser(file_format)
                    if not parser: continue

                    file_content = self.s3_connector.get_object_body(self.bucket_name, representative_path)
                    if not file_content: continue

                    df = parser.parse(file_content)
                    if df is None or df.empty: continue
                    
                    columns = self._get_columns_from_dataframe(df)
                    for p_key in partition_keys:
                        columns.append(Column(name=p_key, dataType=DataType.STRING))
                    
                    sample_df = df.head(self.sample_size)
                    sample_data_rows = [[str(value) for value in row_tuple] for row_tuple in sample_df.itertuples(index=False, name=None)]
                    sample_data = TableData(columns=[col.name.root for col in columns if col.name.root not in partition_keys], rows=sample_data_rows)

                    path_tags = self._get_tags_for_path(representative_path)
                    
                    # Add structure-specific tags
                    structure_tags = self._get_structure_tags(folder_structure, subfolders)
                    all_tags = path_tags + structure_tags

                    # Create enhanced description based on folder structure
                    description = self._create_table_description(
                        table_info, folder_structure, file_format, partition_keys, subfolders
                    )

                    create_table_request = CreateTableRequest(
                        name=table_name,
                        databaseSchema=schema_entity.fullyQualifiedName,
                        columns=columns,
                        tags=all_tags,
                        description=description,
                        fileFormat=file_format,
                        tableType="Regular",
                    )

                    created_table = self.metadata.create_or_update(create_table_request)
                    logger.info(f"Table created/updated: {created_table.fullyQualifiedName.root}")

                    if sample_data and created_table:
                        self.metadata.ingest_table_sample_data(table=created_table, sample_data=sample_data)
                        logger.info(f"Sample data added for: {created_table.fullyQualifiedName.root}")
                    
                    self.status.scanned(created_table.fullyQualifiedName.root)

                except Exception as e:
                    yield Either(left=StackTraceError(name=table_name, error=f"Could not process table group {table_name}: {e}"))
                    continue

        except Exception as e:
            yield Either(left=StackTraceError(name=self.bucket_name, error=f"Major error during iteration: {e}"))
            
    def _iter(self) -> Iterable[Either]:
        """Required method that runs the `next_record` generator."""
        yield from self.next_record()

    def _get_or_create_service(self) -> DatabaseService:
        """Gets or creates the DatabaseService entity."""
        service = self.metadata.get_by_name(entity=DatabaseService, fqn=self.service_name)
        if service: return service
        service_request = CreateDatabaseServiceRequest(name=self.service_name, serviceType="CustomDatabase", connection=self.config.serviceConnection.root)
        return self.metadata.create_or_update(service_request)

    def _get_or_create_database(self, service: DatabaseService) -> Database:
        """Gets or creates the Database entity."""
        db_fqn = f"{service.fullyQualifiedName.root}.{self.bucket_name}"
        database = self.metadata.get_by_name(entity=Database, fqn=db_fqn)
        if database: return database
        db_request = CreateDatabaseRequest(name=self.bucket_name, service=service.fullyQualifiedName)
        return self.metadata.create_or_update(db_request)

    def _get_or_create_schema(self, database: Database, schema_name: str) -> DatabaseSchema:
        """Gets or creates the DatabaseSchema entity."""
        schema_fqn = f"{database.fullyQualifiedName.root}.{schema_name}"
        schema = self.metadata.get_by_name(entity=DatabaseSchema, fqn=schema_fqn)
        if schema: return schema
        schema_request = CreateDatabaseSchemaRequest(name=schema_name, database=database.fullyQualifiedName)
        return self.metadata.create_or_update(schema_request)
    
    def test_connection(self) -> None:
        """Tests the connection to the S3 source."""
        if not self.security_manager.test_connection(self.endpoint_url):
            raise Exception("S3 connection failed")
        logger.info("S3 Connection Test successful")

    def close(self):
        """Closes any open resources."""
        if self.s3_connector:
            self.s3_connector.close()


class EnhancedS3Connector:
    """Enhanced S3 connector that uses the security manager."""
    
    def __init__(self, s3_client, security_manager: S3SecurityManager):
        """Initialize with boto3 S3 client and security manager."""
        self.s3_client = s3_client
        self.security_manager = security_manager
    
    def list_objects(self, bucket_name: str) -> List[Dict]:
        """List all objects in a bucket with pagination support."""
        all_objects = []
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name)
            for page in pages:
                if "Contents" in page:
                    all_objects.extend(page['Contents'])
        except Exception as e:
            logger.error(f"Failed to list objects in bucket {bucket_name}: {e}")
        return all_objects
    
    def get_object_body(self, bucket_name: str, object_key: str) -> Optional[bytes]:
        """Get object content as bytes."""
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=object_key)
            return response['Body'].read()
        except Exception as e:
            logger.error(f"Failed to get object body for {object_key} in bucket {bucket_name}: {e}")
            return None
    
    def close(self):
        """Close any open resources."""
        pass
    
    def _get_structure_tags(self, folder_structure: str, subfolders: List[str]) -> List[TagLabel]:
        """Generate tags based on folder structure type."""
        tags = []
        
        # Add structure type tags
        structure_tag_map = {
            "hierarchical": "Structure.Hierarchical",
            "flat": "Structure.Flat", 
            "partitioned": "Structure.Partitioned",
            "mixed": "Structure.Mixed"
        }
        
        if folder_structure in structure_tag_map:
            tags.append(TagLabel(
                tagFQN=structure_tag_map[folder_structure],
                source=TagSource.Classification,
                labelType=LabelType.Automated,
                state=State.Confirmed
            ))
        
        # Add complexity tags based on subfolder count
        subfolder_count = len(subfolders)
        if subfolder_count > 0:
            if subfolder_count <= 3:
                complexity_tag = "Complexity.Simple"
            elif subfolder_count <= 10:
                complexity_tag = "Complexity.Moderate"
            else:
                complexity_tag = "Complexity.Complex"
                
            tags.append(TagLabel(
                tagFQN=complexity_tag,
                source=TagSource.Classification,
                labelType=LabelType.Automated,
                state=State.Confirmed
            ))
        
        return tags

    def _create_table_description(self, table_info: Dict, folder_structure: str, 
                                 file_format: str, partition_keys: List[str], 
                                 subfolders: List[str]) -> str:
        """Create an enhanced table description based on folder structure."""
        file_count = len(table_info["files"])
        
        # Base description
        description_parts = [
            f"**{folder_structure.title()} Structure Table**",
            f"- **Files**: {file_count} {file_format.upper()} file(s)",
            f"- **Format**: {file_format.upper()}"
        ]
        
        # Add partition information
        if partition_keys:
            description_parts.append(f"- **Partitions**: {', '.join(partition_keys)}")
        else:
            description_parts.append("- **Partitions**: None")
        
        # Add folder structure details
        if folder_structure == "hierarchical":
            if subfolders:
                description_parts.append(f"- **Subfolders**: {len(subfolders)} level(s)")
                if len(subfolders) <= 5:  # Show subfolder names if not too many
                    description_parts.append(f"  - {', '.join(subfolders[:5])}")
                    if len(subfolders) > 5:
                        description_parts.append(f"  - ... and {len(subfolders) - 5} more")
            else:
                description_parts.append("- **Subfolders**: Files in root level of table folder")
        elif folder_structure == "flat":
            description_parts.append("- **Structure**: Files directly in bucket root")
        elif folder_structure == "partitioned":
            description_parts.append("- **Structure**: Hive-style partitioned data")
        
        # Add file location examples
        sample_files = table_info["files"][:3]  # Show up to 3 example files
        if sample_files:
            description_parts.append("- **Sample Paths**:")
            for file_path in sample_files:
                description_parts.append(f"  - `{file_path}`")
            if len(table_info["files"]) > 3:
                description_parts.append(f"  - ... and {len(table_info['files']) - 3} more files")
        
        return "\n".join(description_parts)
