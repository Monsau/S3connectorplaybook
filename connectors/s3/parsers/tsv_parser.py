# File: connectors/s3/parsers/tsv_parser.py

import pandas as pd
import io
from .base_parser import FileParser

class TsvParser(FileParser):
    """
    Concrete parser for TSV (Tab-Separated Values) files.
    """
    def parse(self, content: bytes) -> pd.DataFrame:
        return pd.read_csv(io.BytesIO(content), sep='\t')
