
-----

# Custom S3/MinIO Connector for OpenMetadata

This project contains a custom, feature-rich connector for OpenMetadata designed to ingest metadata from S3-compatible object storage services, including AWS S3 and MinIO.

-----

## Key Features

  - **Automatic File Discovery**: Scans a specified S3/MinIO bucket to find and process data files based on configurable extensions.
  - **Intelligent Partition Handling**: Automatically detects Hive-style partitioned data (e.g., `/region=FR/date=2025-06-30/`) and groups multiple physical files into a single logical table in OpenMetadata.
  - **Flexible Schema Inference**: Parses file content and infers the table schema for multiple formats, including `CSV`, `JSON`, `Parquet`, and `TSV`.
  - **Autonomous Metadata Ingestion**: Directly handles the entire lifecycle of metadata creation in OpenMetadata, including services, databases (buckets), schemas (folders), and tables.
  - **Sample Data Ingestion**: Ingests a preview of the data (the first 50 rows) for each table, making it immediately explorable in the OpenMetadata UI.
  - **Configurable Auto-Tagging**: Automates data governance by applying predefined tags to tables based on path keywords or setting default tags for all ingested assets.

-----

## Project Structure

```
/
├── connectors/
│   └── s3/
│       ├── __init__.py
│       ├── s3_connector.py          # Main source connector logic
│       ├── connector.py             # S3 client helper class
│       └── parsers/                 # Directory for file format parsers
│           ├── __init__.py
│           ├── base_parser.py
│           ├── factory.py
│           ├── csv_parser.py
│           ├── json_parser.py
│           ├── parquet_parser.py
│           └── tsv_parser.py
│
└── playbooks/
    └── ingestion.yaml               # Workflow configuration file
```

-----

## Usage

### 1\. Prerequisites

  - Python 3.8+
  - `openmetadata-ingestion` package installed (`pip install "openmetadata-ingestion[pandas]" boto3 faker tqdm`).
  - Ensure that all directories within the `connectors` path contain an `__init__.py` file (which can be empty). This is required for Python to recognize them as packages.

### 2\. Configuration

Edit the `playbooks/ingestion.yaml` file to match your S3/MinIO credentials and desired connector behavior.

```yaml
source:
  type: customDatabase
  serviceName: minio-storage # The display name for your service in OpenMetadata
  serviceConnection:
    config:
      type: CustomDatabase
      # Python import path to the main connector class
      sourcePythonClass: connectors.s3.s3_connector.S3Source
      connectionOptions:
        # S3/MinIO Connection Details
        awsAccessKeyId: "YOUR_ACCESS_KEY"
        awsSecretAccessKey: "YOUR_SECRET_KEY"
        awsRegion: "us-east-1"
        endPointURL: "http://minio:9000"
        bucketName: "your-bucket-name"

        # --- Custom Connector Configuration ---
        # Comma-separated string of file extensions to ingest
        file_formats: "csv,json,parquet,tsv"
        # Set to "true" to enable partition discovery, "false" otherwise
        enable_partition_parsing: "true"
        # Rule-based tagging. Format: "keyword1:TagFQN1;keyword2:TagFQN2"
        # IMPORTANT: Tags must exist in your OpenMetadata instance beforehand.
        tag_mapping: "users:PII.Sensitive;events:Application.Events"
        # Default tags to apply to all tables. Format: "TagFQN1,TagFQN2"
        default_tags: "Tier.Bronze"

sink:
  type: metadata-rest
  config: {}

workflowConfig:
  loggerLevel: INFO # Can be set to DEBUG for more verbose output
  openMetadataServerConfig:
    hostPort: http://localhost:8585/api
    authProvider: openmetadata
    securityConfig:
      jwtToken: "YOUR_JWT_TOKEN"
```

### 3\. Running the Ingestion

> **Important:** Run the following commands from the root directory of your project.

#### On Linux / macOS

```bash
export PYTHONPATH="."
metadata ingest -c playbooks/ingestion.yaml
```

#### On Windows (PowerShell)

```powershell
$env:PYTHONPATH = "."
metadata ingest -c playbooks/ingestion.yaml
```

#### On Windows (Command Prompt)

```cmd
set PYTHONPATH=.
metadata ingest -c playbooks/ingestion.yaml
```

-----

## Docker Build (Optional)

To build a self-contained Docker image that includes the `openmetadata-ingestion` client and your custom connector code, you can use a `Dockerfile`. This simplifies deployment in containerized environments.

```bash
docker build -t openmetadata-ingestion-custom:latest .
```

-----

## Troubleshooting

  - **`ModuleNotFoundError: No module named 'connectors'`**
    This is the most common issue and is almost always caused by one of the following:
      - You did not run the `metadata ingest` command from the root directory of the project.
      - The `PYTHONPATH` environment variable was not set correctly before running the command.
      - A folder in the import path (e.g., `connectors` or `connectors/s3`) is missing its `__init__.py` file.

## About `S3Source`

The `S3Source` class (see `connectors/s3/s3_connector.py`) implements the main logic for:

* Connecting to S3/MinIO using credentials from the YAML config

* Discovering and grouping files

* Inferring schema and sample data

* Tagging tables based on path rules

* Creating/updating OpenMetadata entities

See the code for detailed comments and extension points.

## Contact

For any questions or inquiries, please contact me:

* **Email**: `mfonsau@talentys.eu`

* **LinkedIn**: `https://www.linkedin.com/in/mustapha-fonsau/`