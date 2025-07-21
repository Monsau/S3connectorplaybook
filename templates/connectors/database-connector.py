"""
Database Connector Template for OpenMetadata

This template provides a foundation for creating connectors that work with
database systems like MySQL, PostgreSQL, Oracle, MongoDB, etc.

Usage:
1. Copy this file to your connector directory
2. Implement the database-specific connection methods
3. Customize the schema and table discovery logic
4. Test with your database system

Author: OpenMetadata Universal Connector Playbook
License: MIT
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from urllib.parse import urlparse
from abc import abstractmethod

from metadata.generated.schema.entity.data.table import Table, Column, TableType
from metadata.generated.schema.entity.data.database import Database
from metadata.generated.schema.entity.data.databaseSchema import DatabaseSchema
from metadata.ingestion.api.common import Entity
from metadata.utils.logger import ingestion_logger

# Import the base connector
from .base_connector import CommonConnectorSource

logger = ingestion_logger()


class DatabaseConnectorSource(CommonConnectorSource):
    """
    Base class for database connectors (MySQL, PostgreSQL, Oracle, MongoDB, etc.)
    
    This template provides:
    - Database connection management
    - Schema and table discovery
    - Column metadata extraction
    - Index and constraint information
    - Query execution for sampling
    - Connection pooling support
    """
    
    def __init__(self, config, metadata_config):
        super().__init__(config, metadata_config)
        
        # Database-specific configuration
        self.connection_string = self._build_connection_string()
        self.schema_filter = self.connector_config.custom_settings.get('schema_filter', [])
        self.table_filter = self.connector_config.custom_settings.get('table_filter', [])
        self.include_views = self.connector_config.custom_settings.get('include_views', True)
        self.include_tables = self.connector_config.custom_settings.get('include_tables', True)
        self.sample_size = self.connector_config.custom_settings.get('sample_size', 100)
        
        # Connection pool settings
        self.pool_size = self.connector_config.custom_settings.get('pool_size', 5)
        self.pool_timeout = self.connector_config.custom_settings.get('pool_timeout', 30)
        self.pool_recycle = self.connector_config.custom_settings.get('pool_recycle', 3600)
        
        # Database connection
        self.connection = None
        self.engine = None
        
        logger.info(f"Initialized database connector for: {self.connector_config.host}")
    
    def _build_connection_string(self) -> str:
        """
        Build database connection string.
        Override this method for your specific database type.
        """
        # Generic connection string template
        # Customize for your database (MySQL, PostgreSQL, Oracle, etc.)
        
        protocol = self.connector_config.custom_settings.get('protocol', 'postgresql')
        host = self.connector_config.host
        port = self.connector_config.port or self._get_default_port(protocol)
        database = self.connector_config.database or 'default'
        username = self.connector_config.username
        password = self.connector_config.password
        
        if username and password:
            return f"{protocol}://{username}:{password}@{host}:{port}/{database}"
        else:
            return f"{protocol}://{host}:{port}/{database}"
    
    def _get_default_port(self, protocol: str) -> int:
        """Get default port for database type"""
        default_ports = {
            'postgresql': 5432,
            'mysql': 3306,
            'oracle': 1521,
            'sqlserver': 1433,
            'mongodb': 27017,
            'redis': 6379,
            'cassandra': 9042
        }
        return default_ports.get(protocol, 5432)
    
    def prepare(self):
        """Initialize database connection"""
        super().prepare()
        try:
            self.connection = self._create_connection()
            self.engine = self._create_engine()
            logger.info("Database connection established successfully")
        except Exception as e:
            self._handle_error(e, "Establishing database connection")
            raise
    
    def close(self):
        """Clean up database connections"""
        try:
            if self.connection:
                self.connection.close()
            if self.engine:
                self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            self._handle_error(e, "Closing database connections")
        finally:
            super().close()
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            test_connection = self._create_connection()
            result = self._execute_test_query(test_connection)
            test_connection.close()
            return result is not None
        except Exception as e:
            self._handle_error(e, "Testing database connection")
            return False
    
    def get_database_names(self) -> List[str]:
        """Get list of databases/schemas"""
        try:
            databases = self._get_databases_from_db()
            
            # Apply schema filter if specified
            if self.schema_filter:
                databases = [db for db in databases if db in self.schema_filter]
            
            return databases
        except Exception as e:
            self._handle_error(e, "Getting database names")
            return []
    
    def get_table_names_and_types(self, database_name: str = None) -> List[Tuple[str, str]]:
        """Get tables and views with their types"""
        try:
            tables = []
            
            if self.include_tables:
                db_tables = self._get_tables_from_db(database_name)
                tables.extend([(name, 'TABLE') for name in db_tables])
            
            if self.include_views:
                db_views = self._get_views_from_db(database_name)
                tables.extend([(name, 'VIEW') for name in db_views])
            
            # Apply table filter if specified
            if self.table_filter:
                tables = [(name, type_) for name, type_ in tables if name in self.table_filter]
            
            return tables
        except Exception as e:
            self._handle_error(e, f"Getting table names for database {database_name}")
            return []
    
    def get_table_metadata(self, table_name: str, database_name: str = None) -> Dict:
        """Extract comprehensive table metadata"""
        try:
            metadata = {
                'table_name': table_name,
                'database_name': database_name,
                'schema': self._get_table_schema(table_name, database_name),
                'indexes': self._get_table_indexes(table_name, database_name),
                'constraints': self._get_table_constraints(table_name, database_name),
                'statistics': self._get_table_statistics(table_name, database_name),
                'sample_data': self._get_sample_data(table_name, database_name),
                'table_type': self._get_table_type(table_name, database_name),
                'comment': self._get_table_comment(table_name, database_name)
            }
            
            return metadata
        except Exception as e:
            self._handle_error(e, f"Getting metadata for table {table_name}")
            return {}
    
    # Abstract methods to be implemented for specific database types
    
    @abstractmethod
    def _create_connection(self):
        """
        Create database connection.
        Implement using appropriate database driver (psycopg2, pymysql, etc.)
        """
        pass
    
    @abstractmethod
    def _create_engine(self):
        """
        Create SQLAlchemy engine or equivalent connection pool.
        """
        pass
    
    @abstractmethod
    def _execute_test_query(self, connection) -> Any:
        """
        Execute a simple test query to verify connection.
        Example: SELECT 1 or SELECT version()
        """
        pass
    
    @abstractmethod
    def _get_databases_from_db(self) -> List[str]:
        """
        Query database to get list of databases/schemas.
        Example SQL: SHOW DATABASES or SELECT schema_name FROM information_schema.schemata
        """
        pass
    
    @abstractmethod
    def _get_tables_from_db(self, database_name: str = None) -> List[str]:
        """
        Query database to get list of tables.
        Example SQL: SHOW TABLES or SELECT table_name FROM information_schema.tables
        """
        pass
    
    @abstractmethod
    def _get_views_from_db(self, database_name: str = None) -> List[str]:
        """
        Query database to get list of views.
        """
        pass
    
    # Optional methods with default implementations
    
    def _get_table_schema(self, table_name: str, database_name: str = None) -> List[Dict]:
        """Get table column information"""
        try:
            return self._query_table_schema(table_name, database_name)
        except Exception as e:
            self._handle_error(e, f"Getting schema for {table_name}")
            return []
    
    def _get_table_indexes(self, table_name: str, database_name: str = None) -> List[Dict]:
        """Get table index information"""
        try:
            return self._query_table_indexes(table_name, database_name)
        except Exception as e:
            self._handle_error(e, f"Getting indexes for {table_name}")
            return []
    
    def _get_table_constraints(self, table_name: str, database_name: str = None) -> List[Dict]:
        """Get table constraint information"""
        try:
            return self._query_table_constraints(table_name, database_name)
        except Exception as e:
            self._handle_error(e, f"Getting constraints for {table_name}")
            return []
    
    def _get_table_statistics(self, table_name: str, database_name: str = None) -> Dict:
        """Get table statistics (row count, size, etc.)"""
        try:
            return self._query_table_statistics(table_name, database_name)
        except Exception as e:
            self._handle_error(e, f"Getting statistics for {table_name}")
            return {}
    
    def _get_sample_data(self, table_name: str, database_name: str = None) -> List[Dict]:
        """Get sample data from table"""
        try:
            return self._query_sample_data(table_name, database_name)
        except Exception as e:
            self._handle_error(e, f"Getting sample data for {table_name}")
            return []
    
    def _get_table_type(self, table_name: str, database_name: str = None) -> str:
        """Get table type (TABLE, VIEW, MATERIALIZED_VIEW, etc.)"""
        try:
            return self._query_table_type(table_name, database_name)
        except Exception as e:
            self._handle_error(e, f"Getting table type for {table_name}")
            return "TABLE"
    
    def _get_table_comment(self, table_name: str, database_name: str = None) -> str:
        """Get table comment/description"""
        try:
            return self._query_table_comment(table_name, database_name)
        except Exception as e:
            self._handle_error(e, f"Getting comment for {table_name}")
            return ""
    
    # Database-specific query methods to be implemented
    
    def _query_table_schema(self, table_name: str, database_name: str = None) -> List[Dict]:
        """
        Query database for table schema information.
        Should return list of column dictionaries with keys:
        - name: column name
        - dataType: column data type
        - nullable: whether column can be null
        - default: default value
        - comment: column comment
        """
        # Implement using information_schema or database-specific system tables
        logger.warning("Table schema query not implemented")
        return []
    
    def _query_table_indexes(self, table_name: str, database_name: str = None) -> List[Dict]:
        """Query database for table indexes"""
        logger.warning("Table indexes query not implemented")
        return []
    
    def _query_table_constraints(self, table_name: str, database_name: str = None) -> List[Dict]:
        """Query database for table constraints"""
        logger.warning("Table constraints query not implemented")
        return []
    
    def _query_table_statistics(self, table_name: str, database_name: str = None) -> Dict:
        """Query database for table statistics"""
        logger.warning("Table statistics query not implemented")
        return {}
    
    def _query_sample_data(self, table_name: str, database_name: str = None) -> List[Dict]:
        """Query database for sample data"""
        try:
            # Generic implementation - customize for your database
            full_table_name = f"{database_name}.{table_name}" if database_name else table_name
            query = f"SELECT * FROM {full_table_name} LIMIT {self.sample_size}"
            
            result = self._execute_query(query)
            return [dict(row) for row in result] if result else []
        except Exception as e:
            self._handle_error(e, f"Querying sample data for {table_name}")
            return []
    
    def _query_table_type(self, table_name: str, database_name: str = None) -> str:
        """Query database for table type"""
        logger.warning("Table type query not implemented")
        return "TABLE"
    
    def _query_table_comment(self, table_name: str, database_name: str = None) -> str:
        """Query database for table comment"""
        logger.warning("Table comment query not implemented")
        return ""
    
    def _execute_query(self, query: str) -> Any:
        """Execute SQL query and return results"""
        try:
            if self.connection:
                cursor = self.connection.cursor()
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            self._handle_error(e, f"Executing query: {query}")
            return None
    
    def _create_entity(self, metadata: Dict, table_name: str, database_name: str = None) -> Optional[Entity]:
        """Create OpenMetadata Table entity from database metadata"""
        try:
            # Convert schema information to OpenMetadata columns
            columns = []
            for i, col_info in enumerate(metadata.get('schema', [])):
                column = Column(
                    name=col_info.get('name'),
                    dataType=col_info.get('dataType', 'VARCHAR'),
                    description=col_info.get('comment'),
                    ordinalPosition=i + 1,
                    constraint=col_info.get('constraint'),
                    defaultValue=col_info.get('default')
                )
                columns.append(column)
            
            # Determine table type
            table_type_mapping = {
                'TABLE': TableType.Regular,
                'VIEW': TableType.View,
                'MATERIALIZED_VIEW': TableType.MaterializedView,
                'EXTERNAL': TableType.External
            }
            table_type = table_type_mapping.get(
                metadata.get('table_type', 'TABLE'), 
                TableType.Regular
            )
            
            # Create table entity
            table = Table(
                name=table_name,
                displayName=table_name,
                description=metadata.get('comment', ''),
                columns=columns,
                tableType=table_type,
                # Add database-specific information
                extension={
                    'database_name': database_name,
                    'indexes': metadata.get('indexes', []),
                    'constraints': metadata.get('constraints', []),
                    'statistics': metadata.get('statistics', {}),
                    'connector_type': self.__class__.__name__
                }
            )
            
            return table
            
        except Exception as e:
            self._handle_error(e, f"Creating entity for table {table_name}")
            return None


# Example usage for specific database types
if __name__ == "__main__":
    """
    Example customizations for specific database types:
    
    PostgreSQL:
    - Use psycopg2 for connection
    - Query information_schema for metadata
    - Handle PostgreSQL-specific data types
    
    MySQL:
    - Use pymysql for connection
    - Query information_schema and SHOW commands
    - Handle MySQL-specific data types
    
    Oracle:
    - Use cx_Oracle for connection
    - Query USER_TABLES, ALL_TABLES system views
    - Handle Oracle-specific data types
    
    MongoDB:
    - Use pymongo for connection
    - Introspect collections and documents
    - Handle NoSQL schema inference
    """
    
    print("Database connector template ready for customization!")
    print("Implement the abstract methods for your specific database type.")
