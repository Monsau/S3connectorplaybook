# File: connectors/s3/s3_connector.py
# This is the final, fully-featured, and documented version of the project.

"""
This module defines a custom OpenMetadata source connector (S3Source)
capable of scanning an S3-compatible bucket (like MinIO), discovering
files, and ingesting them as tables into OpenMetadata.
"""

import os
import re
import pandas as pd
from typing import Iterable, Optional, List, Dict
from collections import defaultdict

from .parsers import get_parser
from connectors.s3.connector import S3Connector

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
    Custom OpenMetadata Source for S3/MinIO buckets.

    Key Features:
    1.  File Discovery: Scans a bucket for files with configurable extensions.
    2.  Schema Parsing: Infers column schemas for supported formats.
    3.  Partition Handling: Intelligently groups Hive-style partitioned files into a single logical table.
    4.  Sample Data Ingestion: Ingests a configurable number of rows for previewing in the UI.
    5.  Automatic Tagging: Applies tags to tables based on configurable rules.
    """

    def __init__(self, config: WorkflowSource, metadata: OpenMetadata):
        """
        Initializes the connector with the configuration from the workflow YAML.
        """
        super().__init__()
        self.config = config
        self.metadata = metadata
        
        service_connection_config = config.serviceConnection.root.config
        connection_options = service_connection_config.connectionOptions.root
        
        self.awsAccessKeyId = connection_options.get("awsAccessKeyId")
        self.awsSecretAccessKey = connection_options.get("awsSecretAccessKey")
        self.awsRegion = connection_options.get("awsRegion", "us-east-1")
        self.endPointURL = connection_options.get("endPointURL")
        self.bucketName = connection_options.get("bucketName")
        self.service_name = self.config.serviceName

        # Read custom configurations from connectionOptions
        formats_str = connection_options.get("file_formats", "csv,json,parquet,tsv")
        self.supported_formats = [f.strip() for f in formats_str.split(',')]
        
        partition_parsing_str = connection_options.get("enable_partition_parsing", "false")
        self.enable_partition_parsing = partition_parsing_str.lower() == 'true'
        
        sample_size_str = connection_options.get("sample_size", "50")
        try:
            self.sample_size = int(sample_size_str)
        except ValueError:
            logger.warning(f"Invalid sample_size '{sample_size_str}'. Defaulting to 50.")
            self.sample_size = 50

        self.tag_mapping = []
        tag_mapping_str = connection_options.get("tag_mapping")
        if tag_mapping_str:
            try:
                rules = tag_mapping_str.split(';')
                for rule in rules:
                    if not rule: continue
                    parts = rule.split(':', 1)
                    if len(parts) == 2:
                        self.tag_mapping.append({"path_keyword": parts[0].strip(), "tag_fqn": parts[1].strip()})
            except Exception as e:
                logger.warning(f"Could not parse tag_mapping configuration. Error: {e}")

        
        logger.info(f"Supported file formats: {self.supported_formats}")
        logger.info(f"Partition parsing enabled: {self.enable_partition_parsing}")
        logger.info(f"Sample data size: {self.sample_size}")
        logger.info(f"Tagging rules configured: {self.tag_mapping}")
        
        self.s3_connector = S3Connector(
            aws_access_key_id=self.awsAccessKeyId,
            aws_secret_access_key=self.awsSecretAccessKey,
            region_name=self.awsRegion,
            endpoint_url=self.endPointURL
        )
        logger.info("S3Connector wrapper initialized.")
        
    @classmethod
    def create(cls, config_dict: dict, metadata: OpenMetadata, pipeline_name: Optional[str] = None) -> "S3Source":
        """Factory method called by OpenMetadata to create an instance."""
        config = WorkflowSource.model_validate(config_dict)
        return cls(config, metadata)

    def prepare(self):
        """Preliminary checks before ingestion starts."""
        if not self.bucketName:
            raise ValueError("bucketName is a required field.")

    def _get_columns_from_dataframe(self, df: pd.DataFrame) -> List[Column]:
        """Infers OpenMetadata columns from a pandas DataFrame."""
        columns = []
        for col_name, col_type in df.dtypes.items():
            om_type = PANDAS_TO_OM_TYPE.get(str(col_type).lower(), DataType.STRING)
            columns.append(Column(name=str(col_name), dataType=om_type))
        return columns

    def _group_files(self, objects: List[Dict]) -> Dict[str, Dict]:
        """Groups S3 objects into logical tables."""
        grouped_files = defaultdict(lambda: {"files": [], "partitions": set()})
        partition_regex = re.compile(r"([^/]+)=([^/]+)")
        for obj in objects:
            obj_key = obj.get('Key')
            if not obj_key or obj_key.endswith('/'): continue
            file_format = os.path.splitext(obj_key)[1].lstrip('.').lower()
            if file_format not in self.supported_formats: continue
            
            logical_table_name = os.path.splitext(os.path.basename(obj_key))[0]
            if self.enable_partition_parsing:
                found_partitions = partition_regex.findall(obj_key)
                if found_partitions:
                    first_partition_str = f"{found_partitions[0][0]}={found_partitions[0][1]}"
                    base_path = obj_key.split(first_partition_str, 1)[0]
                    logical_table_name = os.path.basename(base_path.strip('/')) or os.path.dirname(base_path.strip('/')).split('/')[-1]
                    for key, value in found_partitions:
                        grouped_files[logical_table_name]["partitions"].add(key)
            
            grouped_files[logical_table_name]["files"].append(obj_key)
        return grouped_files

    def _get_tags_for_path(self, path: str) -> List[TagLabel]:
        """Returns a list of TagLabel objects to apply to a table."""
        tags = []
        if not self.tag_mapping: return tags
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
        return tags

    def next_record(self) -> Iterable[Either[dict]]:
        """
        Main generator that orchestrates the ingestion.
        """
        try:
            service_entity = self._get_or_create_service()
            if not service_entity: raise Exception("The service could not be created.")
            
            all_objects = self.s3_connector.list_objects(self.bucketName)
            logical_tables = self._group_files(all_objects)
            database_entity = self._get_or_create_database(service_entity)
            schema_entities_cache = {}

            for table_name, table_info in logical_tables.items():
                representative_path = table_info["files"][0]
                partition_keys = sorted(list(table_info["partitions"]))
                path_parts = os.path.dirname(representative_path).split('/')
                schema_name = path_parts[0] if path_parts and path_parts[0] else "default"

                if schema_name not in schema_entities_cache:
                    schema_entities_cache[schema_name] = self._get_or_create_schema(database_entity, schema_name)
                schema_entity = schema_entities_cache[schema_name]
                
                try:
                    file_format = os.path.splitext(representative_path)[1].lstrip('.').lower()
                    parser = get_parser(file_format)
                    if not parser: continue

                    file_content = self.s3_connector.get_object_body(self.bucketName, representative_path)
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
                    all_tags =  path_tags

                    create_table_request = CreateTableRequest(
                        name=table_name,
                        databaseSchema=schema_entity.fullyQualifiedName,
                        columns=columns,
                        tags=all_tags,
                        description=f"Logical table for {len(table_info['files'])} file(s). Partitions: {partition_keys or 'N/A'}",
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
            yield Either(left=StackTraceError(name=self.bucketName, error=f"Major error during iteration: {e}"))
            
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
        db_fqn = f"{service.fullyQualifiedName.root}.{self.bucketName}"
        database = self.metadata.get_by_name(entity=Database, fqn=db_fqn)
        if database: return database
        db_request = CreateDatabaseRequest(name=self.bucketName, service=service.fullyQualifiedName)
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
        if not self.s3_connector.connect(): raise Exception("S3 connection failed via S3Connector.")
        logger.info("S3 Connection Test successful via S3Connector.")

    def close(self):
        """Closes any open resources."""
        self.s3_connector.close()
