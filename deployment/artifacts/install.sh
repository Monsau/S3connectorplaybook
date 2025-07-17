#!/bin/bash
# Installation script for OpenMetadata S3 Connector

echo "Installing OpenMetadata S3 Connector..."

# Install the connector
pip install openmetadata-s3-connector*.whl

# Verify installation
python -c "from connectors.s3.s3_connector import S3Source; print('Installation successful')"

echo "Connector installed successfully!"
