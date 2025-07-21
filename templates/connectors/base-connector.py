"""
Universal Base Connector Template for OpenMetadata

This module provides the base class and common functionality that all
connector templates inherit from. It includes standard OpenMetadata
integration, security, logging, and error handling.

Author: OpenMetadata Universal Connector Playbook
License: MIT
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional, Iterator
from dataclasses import dataclass
from pathlib import Path

from metadata.generated.schema.entity.services.connections.metadata.openMetadataConnection import (
    OpenMetadataConnection,
)
from metadata.generated.schema.metadataIngestion.workflow import (
    Source as WorkflowSource,
)
from metadata.ingestion.api.common import Entity
from metadata.ingestion.api.models import Either
from metadata.ingestion.api.source import Source, SourceStatus
from metadata.utils.logger import ingestion_logger

# Import universal security and parser components
try:
    from connectors.security import UniversalSecurityManager
    from connectors.parsers.factory import ParserFactory
except ImportError:
    # Fallback for development
    UniversalSecurityManager = None
    ParserFactory = None

logger = ingestion_logger()


@dataclass
class ConnectorConfig:
    """Standard configuration structure for all connectors"""
    # Connection settings
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    
    # Security settings
    use_ssl: bool = True
    verify_ssl: bool = True
    cert_path: Optional[str] = None
    
    # Performance settings
    max_worker_threads: int = 4
    batch_size: int = 100
    timeout_seconds: int = 300
    max_retries: int = 3
    
    # Feature flags
    enable_rbac: bool = False
    enable_audit: bool = True
    enable_pii_detection: bool = False
    
    # Custom settings (override in specific connectors)
    custom_settings: Dict[str, Any] = None


class CommonConnectorSource(Source, ABC):
    """
    Universal base class for all OpenMetadata connectors.
    
    This class provides common functionality including:
    - Standard OpenMetadata integration
    - Security and RBAC validation
    - Error handling and logging
    - Performance monitoring
    - Audit trail generation
    """
    
    def __init__(self, config: WorkflowSource, metadata_config: OpenMetadataConnection):
        """
        Initialize the connector with configuration and metadata settings.
        
        Args:
            config: Workflow source configuration
            metadata_config: OpenMetadata connection configuration
        """
        super().__init__()
        self.config = config
        self.metadata_config = metadata_config
        self.source_config = self.config.sourceConfig.config
        self.service_connection = self.config.serviceConnection.__root__.config
        
        # Initialize connector configuration
        self.connector_config = self._parse_connector_config()
        
        # Initialize security manager
        self.security_manager = None
        if UniversalSecurityManager and self.connector_config.enable_rbac:
            self.security_manager = UniversalSecurityManager(
                self.service_connection.connectionOptions
            )
        
        # Initialize parser factory
        self.parser_factory = ParserFactory() if ParserFactory else None
        
        # Performance tracking
        self.start_time = None
        self.processed_entities = 0
        self.errors = []
        
        # Audit information
        self.audit_info = {
            'connector_type': self.__class__.__name__,
            'start_time': None,
            'end_time': None,
            'status': 'initialized'
        }
        
        logger.info(f"Initialized {self.__class__.__name__} connector")
    
    def _parse_connector_config(self) -> ConnectorConfig:
        """Parse and validate connector configuration"""
        connection_options = getattr(self.service_connection, 'connectionOptions', {})
        
        return ConnectorConfig(
            host=connection_options.get('host'),
            port=connection_options.get('port'),
            username=connection_options.get('username'),
            password=connection_options.get('password'),
            database=connection_options.get('database'),
            use_ssl=connection_options.get('use_ssl', True),
            verify_ssl=connection_options.get('verify_ssl', True),
            cert_path=connection_options.get('cert_path'),
            max_worker_threads=connection_options.get('max_worker_threads', 4),
            batch_size=connection_options.get('batch_size', 100),
            timeout_seconds=connection_options.get('timeout_seconds', 300),
            max_retries=connection_options.get('max_retries', 3),
            enable_rbac=connection_options.get('enable_rbac', False),
            enable_audit=connection_options.get('enable_audit', True),
            enable_pii_detection=connection_options.get('enable_pii_detection', False),
            custom_settings=connection_options.get('custom_settings', {})
        )
    
    def prepare(self):
        """
        Prepare the connector for operation.
        Override this method to implement connector-specific initialization.
        """
        self.start_time = time.time()
        self.audit_info['start_time'] = self.start_time
        self.audit_info['status'] = 'preparing'
        
        logger.info(f"Preparing {self.__class__.__name__} connector")
        
        # Validate security if enabled
        if self.security_manager:
            try:
                self.security_manager.validate_connection()
                logger.info("Security validation passed")
            except Exception as e:
                logger.error(f"Security validation failed: {e}")
                raise
        
        # Test connection
        if not self.test_connection():
            raise ConnectionError("Failed to establish connection to data source")
        
        self.audit_info['status'] = 'prepared'
        logger.info("Connector preparation completed successfully")
    
    def close(self):
        """Clean up resources when connector is finished"""
        self.audit_info['end_time'] = time.time()
        self.audit_info['status'] = 'completed'
        
        if self.start_time:
            duration = time.time() - self.start_time
            logger.info(f"Connector completed in {duration:.2f} seconds")
            logger.info(f"Processed {self.processed_entities} entities")
            if self.errors:
                logger.warning(f"Encountered {len(self.errors)} errors")
        
        # Log audit information
        if self.connector_config.enable_audit:
            self._log_audit_info()
    
    def get_status(self) -> SourceStatus:
        """Return the current status of the connector"""
        return SourceStatus(
            success=len(self.errors) == 0,
            failures=[str(error) for error in self.errors],
            warnings=[],
            records=self.processed_entities
        )
    
    def _log_audit_info(self):
        """Log audit information for compliance"""
        logger.info(f"AUDIT: {self.audit_info}")
    
    def _handle_error(self, error: Exception, context: str = ""):
        """Standard error handling with logging and tracking"""
        error_msg = f"{context}: {str(error)}" if context else str(error)
        logger.error(error_msg)
        self.errors.append(error)
        
        # Update audit info
        if 'errors' not in self.audit_info:
            self.audit_info['errors'] = []
        self.audit_info['errors'].append(error_msg)
    
    def _validate_rbac(self, resource: str, action: str) -> bool:
        """Validate RBAC permissions for a resource and action"""
        if not self.security_manager:
            return True  # RBAC disabled
        
        try:
            return self.security_manager.check_permission(resource, action)
        except Exception as e:
            self._handle_error(e, f"RBAC validation for {resource}:{action}")
            return False
    
    def _extract_metadata_with_parser(self, source_path: str) -> Optional[Dict]:
        """Extract metadata using the appropriate parser"""
        if not self.parser_factory:
            logger.warning("Parser factory not available")
            return None
        
        try:
            parser = self.parser_factory.get_parser(source_path)
            if parser:
                return parser.extract_metadata()
        except Exception as e:
            self._handle_error(e, f"Parsing {source_path}")
        
        return None
    
    # Abstract methods that must be implemented by specific connectors
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connectivity to the data source.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_database_names(self) -> List[str]:
        """
        Get list of database/schema/container names.
        
        Returns:
            List[str]: List of database names
        """
        pass
    
    @abstractmethod
    def get_table_names_and_types(self, database_name: str = None) -> List[Tuple[str, str]]:
        """
        Get list of table/file names and their types.
        
        Args:
            database_name: Optional database name to filter tables
            
        Returns:
            List[Tuple[str, str]]: List of (table_name, table_type) tuples
        """
        pass
    
    @abstractmethod
    def get_table_metadata(self, table_name: str, database_name: str = None) -> Dict:
        """
        Extract metadata for a specific table/file.
        
        Args:
            table_name: Name of the table/file
            database_name: Optional database name
            
        Returns:
            Dict: Metadata information including schema, columns, etc.
        """
        pass
    
    def _iter(self) -> Iterator[Either[Entity]]:
        """
        Main iteration method that yields entities.
        This provides a standard implementation that can be overridden.
        """
        try:
            # Get all databases/schemas
            databases = self.get_database_names()
            logger.info(f"Found {len(databases)} databases/schemas")
            
            for database in databases:
                # Validate RBAC for database access
                if not self._validate_rbac(database, 'read'):
                    logger.warning(f"RBAC: Access denied to database {database}")
                    continue
                
                # Get tables/files in this database
                tables = self.get_table_names_and_types(database)
                logger.info(f"Found {len(tables)} tables/files in {database}")
                
                for table_name, table_type in tables:
                    try:
                        # Validate RBAC for table access
                        if not self._validate_rbac(f"{database}.{table_name}", 'read'):
                            logger.warning(f"RBAC: Access denied to table {database}.{table_name}")
                            continue
                        
                        # Extract metadata
                        metadata = self.get_table_metadata(table_name, database)
                        
                        if metadata:
                            # Convert to OpenMetadata entity
                            entity = self._create_entity(metadata, table_name, database)
                            if entity:
                                yield Either(right=entity)
                                self.processed_entities += 1
                        
                    except Exception as e:
                        self._handle_error(e, f"Processing table {database}.{table_name}")
                        yield Either(left=e)
                        
        except Exception as e:
            self._handle_error(e, "Main iteration")
            yield Either(left=e)
    
    def _create_entity(self, metadata: Dict, table_name: str, database_name: str = None) -> Optional[Entity]:
        """
        Create an OpenMetadata entity from extracted metadata.
        Override this method to create specific entity types.
        
        Args:
            metadata: Extracted metadata
            table_name: Name of the table/file
            database_name: Optional database name
            
        Returns:
            Entity: OpenMetadata entity or None
        """
        # This is a placeholder - implement in specific connectors
        logger.warning("_create_entity not implemented in base class")
        return None
