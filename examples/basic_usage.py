"""
Example usage of the S3 Connector.

This example demonstrates how to use the S3 connector programmatically.
"""

import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from om_s3_connector.core.s3_connector import S3Source
from om_s3_connector.core.config import S3ConnectorConfig


def main():
    """Example of using the S3 connector programmatically."""
    
    # Configuration
    config = {
        "awsAccessKeyId": os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
        "awsSecretAccessKey": os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        "awsRegion": "us-east-1",
        "endPointURL": "http://localhost:9000",
        "bucketName": "test-bucket",
        "file_formats": "csv,json,parquet",
        "enable_partition_parsing": "true",
        "max_sample_rows": "100",
        "tag_mapping": "users:PII.Sensitive;transactions:Finance.Critical",
        "default_tags": "Source.S3,Tier.Bronze"
    }
    
    print("🔧 S3 Connector Example")
    print("======================")
    
    try:
        # Initialize connector
        print("📊 Initializing S3 connector...")
        connector = S3Source.create(config)
        
        # Get databases (buckets)
        print("🗂️  Discovering databases...")
        databases = list(connector.get_database_names())
        print(f"✅ Found {len(databases)} databases: {databases}")
        
        # Get schemas (folders)
        for db in databases:
            print(f"\n📁 Discovering schemas in database '{db}'...")
            schemas = list(connector.get_database_schema_names())
            print(f"✅ Found {len(schemas)} schemas: {schemas}")
            
            # Get tables (files)
            for schema in schemas[:3]:  # Limit to first 3 schemas
                print(f"\n📊 Discovering tables in schema '{schema}'...")
                tables = list(connector.get_tables_name_and_type())
                print(f"✅ Found {len(tables)} tables")
                
                # Show first few tables
                for table_name, table_type in tables[:5]:
                    print(f"   - {table_name} ({table_type})")
                
                if len(tables) > 5:
                    print(f"   ... and {len(tables) - 5} more")
                
                break  # Only process first schema in example
            break  # Only process first database in example
        
        print("\n✨ Example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
