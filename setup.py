from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read version from package
version_file = this_directory / "src" / "om_s3_connector" / "__init__.py"
version = {}
with open(version_file) as f:
    exec(f.read(), version)

setup(
    name="openmetadata-s3-connector",
    version=version.get("__version__", "2.0.0"),
    author="Mustapha Fonsau",
    author_email="mfonsau@talentys.eu",
    description="A comprehensive S3/MinIO connector for OpenMetadata",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/openmetadata-s3-connector",
    
    # Package configuration
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    
    # Dependencies
    install_requires=[
        "openmetadata-ingestion>=1.3.0",
        "boto3>=1.26.0",
        "pandas>=1.5.0",
        "pyarrow>=10.0.0",
        "tqdm>=4.64.0",
        "fastparquet>=0.8.0",
    ],
    
    # Optional dependencies
    extras_require={
        "all": [
            "avro>=1.11.0",
            "pyorc>=0.8.0",
            "xlrd>=2.0.0",
            "openpyxl>=3.0.0",
            "h5py>=3.7.0",
            "tables>=3.7.0",
            "deltalake>=0.10.0",
        ],
        "excel": ["xlrd>=2.0.0", "openpyxl>=3.0.0"],
        "hdf5": ["h5py>=3.7.0", "tables>=3.7.0"],
        "avro": ["avro>=1.11.0"],
        "orc": ["pyorc>=0.8.0"],
        "delta": ["deltalake>=0.10.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=5.0.0",
            "mypy>=0.990",
            "pre-commit>=2.20.0",
        ],
    },
    
    # Entry points for OpenMetadata
    entry_points={
        "openmetadata_sources": [
            "s3 = om_s3_connector.core.s3_connector:S3Source",
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Archiving",
    ],
    
    # Requirements
    python_requires=">=3.8",
    
    # Include package data
    include_package_data=True,
    package_data={
        "om_s3_connector": ["py.typed"],
    },
    
    # Keywords
    keywords="openmetadata s3 minio connector metadata data-catalog data-lineage",
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/your-username/openmetadata-s3-connector/issues",
        "Source": "https://github.com/your-username/openmetadata-s3-connector",
        "Documentation": "https://github.com/your-username/openmetadata-s3-connector#readme",
    },
)