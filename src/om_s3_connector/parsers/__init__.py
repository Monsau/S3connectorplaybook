"""
File format parsers for the S3 Connector.

This module contains parsers for various file formats supported by the connector.
"""

from .factory import ParserFactory
from .base_parser import FileParser

# Import all parser classes
from .csv_parser import CsvParser
from .json_parser import JsonParser
from .jsonl_parser import JsonlParser
from .parquet_parser import ParquetParser
from .avro_parser import AvroParser
from .orc_parser import OrcParser
from .excel_parser import ExcelParser
from .feather_parser import FeatherParser
from .hdf5_parser import Hdf5Parser
from .pickle_parser import PickleParser
from .delta_parser import DeltaParser
from .tsv_parser import TsvParser

__all__ = [
    "ParserFactory",
    "FileParser",
    "CsvParser",
    "JsonParser", 
    "JsonlParser",
    "ParquetParser",
    "AvroParser",
    "OrcParser",
    "ExcelParser",
    "FeatherParser",
    "Hdf5Parser",
    "PickleParser",
    "DeltaParser",
    "TsvParser"
]
# This file makes the 'parsers' directory a Python package
# and simplifies imports.

from .factory import get_parser
