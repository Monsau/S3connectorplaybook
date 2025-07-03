# File: connectors/s3/parsers/factory.py

from typing import Optional, Dict, Type
from .base_parser import FileParser
from .csv_parser import CsvParser
from .json_parser import JsonParser
from .parquet_parser import ParquetParser
from .tsv_parser import TsvParser

# A mapping from file extensions to their corresponding parser class
PARSER_MAPPING: Dict[str, Type[FileParser]] = {
    "csv": CsvParser,
    "json": JsonParser,
    "parquet": ParquetParser,
    "tsv": TsvParser,
}

def get_parser(file_format: str) -> Optional[FileParser]:
    """
    Factory function that returns an instance of the appropriate parser
    for a given file format. Returns None if the format is not supported.
    """
    parser_class = PARSER_MAPPING.get(file_format.lower())
    if parser_class:
        # Create and return an instance of the parser class
        return parser_class()
    return None
