"""
File-Based Connector Template for OpenMetadata

This template provides a foundation for creating connectors that work with
file-based data sources like HDFS, local file systems, FTP, network shares, etc.

Usage:
1. Copy this file to your connector directory
2. Implement the abstract methods for your specific file system
3. Customize the file discovery and parsing logic
4. Test with your data source

Author: OpenMetadata Universal Connector Playbook
License: MIT
"""

import os
import logging
from typing import Dict, List, Tuple, Optional, Iterator
from pathlib import Path
from urllib.parse import urlparse

from metadata.generated.schema.entity.data.table import Table, Column
from metadata.generated.schema.entity.data.database import Database
from metadata.generated.schema.entity.data.databaseSchema import DatabaseSchema
from metadata.ingestion.api.common import Entity
from metadata.utils.logger import ingestion_logger

# Import the base connector
from .base_connector import CommonConnectorSource, ConnectorConfig

logger = ingestion_logger()


class FileBasedConnectorSource(CommonConnectorSource):
    """
    Base class for file-based connectors (HDFS, local files, FTP, network shares, etc.)
    
    This template provides:
    - File discovery and enumeration
    - Format detection and parsing
    - Hierarchical folder structure mapping
    - Partition detection (Hive-style)
    - Schema inference from file contents
    """
    
    def __init__(self, config, metadata_config):
        super().__init__(config, metadata_config)
        
        # File-specific configuration
        self.root_path = self.connector_config.custom_settings.get('root_path', '/')
        self.supported_formats = self.connector_config.custom_settings.get(
            'supported_formats', 
            ['csv', 'json', 'parquet', 'avro', 'orc', 'excel']
        )
        self.recursive_scan = self.connector_config.custom_settings.get('recursive_scan', True)
        self.follow_symlinks = self.connector_config.custom_settings.get('follow_symlinks', False)
        self.max_file_size = self.connector_config.custom_settings.get('max_file_size_mb', 1024) * 1024 * 1024
        
        # Pattern matching
        self.include_patterns = self.connector_config.custom_settings.get('include_patterns', [])
        self.exclude_patterns = self.connector_config.custom_settings.get('exclude_patterns', [])
        
        # Partitioning
        self.enable_partition_detection = self.connector_config.custom_settings.get('enable_partition_detection', True)
        self.partition_style = self.connector_config.custom_settings.get('partition_style', 'hive')  # hive, directory
        
        logger.info(f"Initialized file-based connector for path: {self.root_path}")
    
    def test_connection(self) -> bool:
        """
        Test connectivity to the file system.
        Override this method for your specific file system (HDFS, FTP, etc.)
        """
        try:
            # Example implementation for local file system
            if self._is_local_path():
                return os.path.exists(self.root_path) and os.access(self.root_path, os.R_OK)
            else:
                # Implement for your specific file system
                return self._test_remote_connection()
        except Exception as e:
            self._handle_error(e, "Testing connection")
            return False
    
    def get_database_names(self) -> List[str]:
        """
        For file-based connectors, databases typically represent:
        - Root directories
        - HDFS namespaces
        - Network shares
        - Top-level containers
        """
        try:
            if self._is_local_path():
                return self._get_local_databases()
            else:
                return self._get_remote_databases()
        except Exception as e:
            self._handle_error(e, "Getting database names")
            return []
    
    def get_table_names_and_types(self, database_name: str = None) -> List[Tuple[str, str]]:
        """
        Get files that can be treated as tables.
        
        Returns:
            List of (file_path, file_type) tuples
        """
        try:
            database_path = os.path.join(self.root_path, database_name) if database_name else self.root_path
            
            if self._is_local_path():
                return self._get_local_files(database_path)
            else:
                return self._get_remote_files(database_path)
        except Exception as e:
            self._handle_error(e, f"Getting table names for database {database_name}")
            return []
    
    def get_table_metadata(self, table_name: str, database_name: str = None) -> Dict:
        """
        Extract metadata from a file.
        
        Args:
            table_name: File path or name
            database_name: Container/directory name
            
        Returns:
            Dict: File metadata including schema, size, modification time, etc.
        """
        try:
            file_path = self._construct_file_path(table_name, database_name)
            
            # Get basic file information
            file_info = self._get_file_info(file_path)
            
            # Extract schema using parser
            schema_info = self._extract_metadata_with_parser(file_path)
            
            # Detect partitions if enabled
            partition_info = {}
            if self.enable_partition_detection:
                partition_info = self._detect_partitions(file_path)
            
            return {
                'file_path': file_path,
                'file_info': file_info,
                'schema': schema_info.get('schema', []) if schema_info else [],
                'sample_data': schema_info.get('sample_data', []) if schema_info else [],
                'partitions': partition_info,
                'format': self._detect_file_format(file_path),
                'table_name': self._generate_table_name(file_path),
                'database_name': database_name
            }
            
        except Exception as e:
            self._handle_error(e, f"Getting metadata for {table_name}")
            return {}
    
    # Helper methods that can be customized for specific file systems
    
    def _is_local_path(self) -> bool:
        """Check if the root path is a local file system path"""
        parsed = urlparse(self.root_path)
        return parsed.scheme in ['', 'file']
    
    def _test_remote_connection(self) -> bool:
        """
        Test connection to remote file system.
        Override this for HDFS, FTP, network shares, etc.
        """
        # Example implementation - customize for your file system
        logger.warning("Remote connection test not implemented")
        return True
    
    def _get_local_databases(self) -> List[str]:
        """Get local directories as databases"""
        try:
            databases = []
            for item in os.listdir(self.root_path):
                item_path = os.path.join(self.root_path, item)
                if os.path.isdir(item_path):
                    databases.append(item)
            return databases
        except Exception as e:
            self._handle_error(e, "Getting local databases")
            return []
    
    def _get_remote_databases(self) -> List[str]:
        """
        Get remote directories/containers as databases.
        Override this for your specific file system.
        """
        # Example implementation - customize for your file system
        logger.warning("Remote database enumeration not implemented")
        return ["default"]
    
    def _get_local_files(self, directory_path: str) -> List[Tuple[str, str]]:
        """Get local files with their types"""
        files = []
        try:
            for root, dirs, file_names in os.walk(directory_path):
                for file_name in file_names:
                    file_path = os.path.join(root, file_name)
                    
                    # Check file size limit
                    if os.path.getsize(file_path) > self.max_file_size:
                        logger.warning(f"Skipping large file: {file_path}")
                        continue
                    
                    # Check format support
                    file_format = self._detect_file_format(file_path)
                    if file_format in self.supported_formats:
                        # Make path relative to root
                        relative_path = os.path.relpath(file_path, directory_path)
                        files.append((relative_path, file_format))
                
                # Control recursion
                if not self.recursive_scan:
                    break
            
            return files
        except Exception as e:
            self._handle_error(e, f"Getting local files from {directory_path}")
            return []
    
    def _get_remote_files(self, directory_path: str) -> List[Tuple[str, str]]:
        """
        Get remote files with their types.
        Override this for your specific file system.
        """
        # Example implementation - customize for your file system
        logger.warning("Remote file enumeration not implemented")
        return []
    
    def _construct_file_path(self, table_name: str, database_name: str = None) -> str:
        """Construct full file path from components"""
        if database_name:
            return os.path.join(self.root_path, database_name, table_name)
        else:
            return os.path.join(self.root_path, table_name)
    
    def _get_file_info(self, file_path: str) -> Dict:
        """
        Get basic file information (size, modification time, etc.)
        Override this for remote file systems.
        """
        try:
            if self._is_local_path():
                stat = os.stat(file_path)
                return {
                    'size_bytes': stat.st_size,
                    'modified_time': stat.st_mtime,
                    'created_time': stat.st_ctime,
                    'permissions': oct(stat.st_mode)[-3:],
                    'is_symlink': os.path.islink(file_path)
                }
            else:
                # Implement for remote file systems
                return self._get_remote_file_info(file_path)
        except Exception as e:
            self._handle_error(e, f"Getting file info for {file_path}")
            return {}
    
    def _get_remote_file_info(self, file_path: str) -> Dict:
        """
        Get remote file information.
        Override this for your specific file system.
        """
        logger.warning("Remote file info not implemented")
        return {}
    
    def _detect_file_format(self, file_path: str) -> str:
        """Detect file format from extension"""
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        
        # Map common extensions to formats
        format_mapping = {
            'csv': 'csv',
            'tsv': 'tsv',
            'txt': 'csv',  # Assume text files are CSV
            'json': 'json',
            'jsonl': 'jsonl',
            'ndjson': 'jsonl',
            'parquet': 'parquet',
            'pq': 'parquet',
            'avro': 'avro',
            'orc': 'orc',
            'xlsx': 'excel',
            'xls': 'excel',
            'feather': 'feather',
            'h5': 'hdf5',
            'hdf5': 'hdf5',
            'pickle': 'pickle',
            'pkl': 'pickle'
        }
        
        return format_mapping.get(file_ext, 'unknown')
    
    def _generate_table_name(self, file_path: str) -> str:
        """Generate a clean table name from file path"""
        # Remove file extension and clean up the name
        table_name = Path(file_path).stem
        
        # Replace invalid characters
        table_name = table_name.replace('-', '_').replace(' ', '_')
        
        # Remove consecutive underscores
        while '__' in table_name:
            table_name = table_name.replace('__', '_')
        
        return table_name.strip('_')
    
    def _detect_partitions(self, file_path: str) -> Dict:
        """
        Detect partition information from file path.
        Supports Hive-style partitioning (key=value) and directory-based.
        """
        if not self.enable_partition_detection:
            return {}
        
        try:
            path_parts = Path(file_path).parts
            partitions = {}
            
            if self.partition_style == 'hive':
                # Look for key=value patterns in path
                for part in path_parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        partitions[key] = value
            
            elif self.partition_style == 'directory':
                # Use directory structure as partitions
                # Example: /year/2023/month/01/file.csv -> {year: 2023, month: 01}
                for i in range(0, len(path_parts) - 1, 2):  # Skip filename
                    if i + 1 < len(path_parts):
                        key = path_parts[i]
                        value = path_parts[i + 1]
                        partitions[key] = value
            
            return partitions
            
        except Exception as e:
            self._handle_error(e, f"Detecting partitions for {file_path}")
            return {}
    
    def _create_entity(self, metadata: Dict, table_name: str, database_name: str = None) -> Optional[Entity]:
        """
        Create OpenMetadata Table entity from file metadata.
        """
        try:
            # Extract schema information
            columns = []
            if 'schema' in metadata:
                for i, col_info in enumerate(metadata['schema']):
                    column = Column(
                        name=col_info.get('name', f'column_{i}'),
                        dataType=col_info.get('dataType', 'VARCHAR'),
                        description=col_info.get('description'),
                        ordinalPosition=i + 1
                    )
                    columns.append(column)
            
            # Create table entity
            table = Table(
                name=metadata.get('table_name', table_name),
                displayName=metadata.get('table_name', table_name),
                description=f"File: {metadata.get('file_path', table_name)}",
                columns=columns,
                tableType="External",
                # Add file-specific information as custom properties
                extension={
                    'file_path': metadata.get('file_path'),
                    'file_format': metadata.get('format'),
                    'file_size': metadata.get('file_info', {}).get('size_bytes'),
                    'partitions': metadata.get('partitions', {}),
                    'connector_type': self.__class__.__name__
                }
            )
            
            return table
            
        except Exception as e:
            self._handle_error(e, f"Creating entity for {table_name}")
            return None


# Example usage and customization guide
if __name__ == "__main__":
    """
    Example of how to customize this template for your specific file system.
    
    For HDFS:
    1. Override remote methods to use vendor-specific libraries
    2. Implement HDFS-specific authentication
    
    For FTP:
    1. Override remote methods to use ftplib
    2. Handle FTP-specific connection parameters
    
    For Network Shares:
    1. Override remote methods to use SMB/CIFS libraries
    2. Handle network authentication and mounting
    """
    
    # Example configuration for local file system
    config_example = {
        'root_path': '/data/files',
        'supported_formats': ['csv', 'json', 'parquet'],
        'recursive_scan': True,
        'enable_partition_detection': True,
        'partition_style': 'hive',
        'max_file_size_mb': 1024,
        'include_patterns': ['*.csv', '*.json'],
        'exclude_patterns': ['*.tmp', '*.log']
    }
    
    print("File-based connector template ready for customization!")
    print("See the docstring for implementation examples.")
