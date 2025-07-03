# Use the official OpenMetadata ingestion image for your version as the base
FROM openmetadata/openmetadata-ingestion:1.8.0

# The base image runs as the 'airflow' user.
# It's good practice to switch to this user to ensure correct permissions.
USER airflow

# Copy your custom connectors directory into the image.
# This makes your custom code available in the Python path.
COPY --chown=airflow:airflow connectors/ /opt/airflow/dags/connectors/

# Copy your requirements file
COPY --chown=airflow:airflow requirements.txt .

# Install the additional Python packages required by your connector
RUN pip install -r requirements.txt
