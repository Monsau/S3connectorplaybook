# File: connectors/s3/parsers/avro_parser.py

import pandas as pd
from typing import Optional
from .base_parser import FileParser
import logging

# Use standard Python logging if OpenMetadata logger is not available
try:
    from metadata.utils.logger import ingestion_logger
    logger = ingestion_logger()
except ImportError:
    logger = logging.getLogger(__name__)


class AvroParser(FileParser):
    """
    Parser for Apache Avro files.
    Avro is a data serialization framework with rich data structures and schema evolution.
    """

    def parse(self, file_content: bytes) -> Optional[pd.DataFrame]:
        """
        Parse Avro file content and return a pandas DataFrame.
        
        Args:
            file_content (bytes): Raw Avro file content
            
        Returns:
            Optional[pd.DataFrame]: Parsed DataFrame or None if parsing fails
        """
        try:
            import avro.schema
            import avro.io
            import io
            import json
            
            logger.debug("Parsing Avro file content")
            
            # Create a file-like object from bytes
            file_buffer = io.BytesIO(file_content)
            
            # Read Avro file
            records = []
            
            # Use avro library to read the file
            decoder = avro.io.BinaryDecoder(file_buffer)
            reader = avro.io.DatumReader()
            
            # Try to read records
            try:
                while True:
                    record = reader.read(decoder)
                    records.append(record)
            except:
                # End of file or error reading more records
                pass
            
            if not records:
                logger.warning("No records found in Avro file")
                return None
            
            # Convert records to DataFrame
            df = pd.DataFrame(records)
            
            if df.empty:
                logger.warning("Avro file resulted in empty DataFrame")
                return None
                
            logger.info(f"Successfully parsed Avro file: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except ImportError:
            # Try alternative approach with fastavro
            try:
                import fastavro
                import io
                
                logger.debug("Using fastavro for Avro parsing")
                
                file_buffer = io.BytesIO(file_content)
                records = []
                
                # Read with fastavro
                avro_reader = fastavro.reader(file_buffer)
                for record in avro_reader:
                    records.append(record)
                
                if not records:
                    logger.warning("No records found in Avro file")
                    return None
                
                df = pd.DataFrame(records)
                
                if df.empty:
                    logger.warning("Avro file resulted in empty DataFrame")
                    return None
                    
                logger.info(f"Successfully parsed Avro file with fastavro: {len(df)} rows, {len(df.columns)} columns")
                return df
                
            except ImportError as e:
                logger.error(f"Neither avro-python3 nor fastavro is available: {e}")
                logger.error("Please install Avro support: pip install avro-python3 or pip install fastavro")
                return None
            except Exception as e:
                logger.error(f"Failed to parse Avro file with fastavro: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to parse Avro file: {str(e)}")
            return None

    def get_file_extension(self) -> str:
        """Return the file extension for Avro files."""
        return "avro"

    def get_format_name(self) -> str:
        """Return the human-readable format name."""
        return "Apache Avro"

    def supports_schema_inference(self) -> bool:
        """Avro files contain schema information."""
        return True

    def get_supported_encodings(self) -> list:
        """Avro files support various codecs."""
        return ["null", "deflate", "snappy", "bzip2", "xz", "zstandard"]
