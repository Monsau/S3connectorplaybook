# Use the official OpenMetadata ingestion image for your version as the base
FROM openmetadata/openmetadata-ingestion:1.8.0

# Set working directory
WORKDIR /app

# The base image runs as the 'airflow' user.
# It's good practice to switch to this user to ensure correct permissions.
USER airflow

# Copy the new source structure
COPY --chown=airflow:airflow src/ /app/src/
COPY --chown=airflow:airflow config/ /app/config/
COPY --chown=airflow:airflow requirements.txt setup.py /app/

# Set Python path to include src directory
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Install the package and dependencies
RUN pip install -e . && \
    pip install -r requirements.txt

# Set default command
CMD ["metadata", "ingest", "-c", "config/ingestion.yaml"]
