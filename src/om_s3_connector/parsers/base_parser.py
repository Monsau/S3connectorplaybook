# File: connectors/s3/parsers/base_parser.py

from abc import ABC, abstractmethod
import pandas as pd

class FileParser(ABC):
    """
    Abstract base class for all file parsers.
    It defines a single contract: a `parse` method that takes file content
    as bytes and returns a pandas DataFrame.
    """
    @abstractmethod
    def parse(self, content: bytes) -> pd.DataFrame:
        """
        Parses the binary content of a file and returns a DataFrame.
        """
        pass
