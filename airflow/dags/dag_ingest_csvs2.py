
import sys
sys.path.insert(0, "/opt/airflow")

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import yaml
from jinja2 import Template
from metadata.ingestion.api.workflow import Workflow

CSV_DIR = "../data"  # 🟡 à adapter
TEMPLATE_PATH = "../templates/ingestion_template.yaml.j2"

def generate_yaml(csv_file: str) -> str:
    """Génère un fichier YAML d'ingestion à partir d'un template"""
    base_name = os.path.splitext(os.path.basename(csv_file))[0]
    yaml_path = f"../ingestions/{base_name}_ingestion.yaml"

    with open(TEMPLATE_PATH, "r") as f:
        template = Template(f.read())

    rendered = template.render(
        csv_file=csv_file,
        table_name=base_name,
        service_name="csv_service",
        business_unit=base_name + "_db"
    )

    with open(yaml_path, "w") as out:
        out.write(rendered)

    return yaml_path

def ingest_csv(csv_file: str):
    """Exécute l’ingestion d’un fichier CSV avec OpenMetadata"""
    os.environ["PYTHONPATH"] = "."
    yaml_path = generate_yaml(csv_file)
    workflow = Workflow.create_workflow_from_config(yaml_path)
    workflow.execute()
    workflow.stop()

default_args = {"owner": "airflow", "start_date": datetime(2024, 1, 1)}

with DAG(
    dag_id="ingest_all_csvs_to_openmetadata",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=["openmetadata", "csv", "generic"],
) as dag:
    for file in os.listdir(CSV_DIR):
        if file.endswith(".csv"):
            full_path = os.path.join(CSV_DIR, file)
            task = PythonOperator(
                task_id=f"ingest_{file.replace('.csv','')}",
                python_callable=ingest_csv,
                op_args=[full_path],
            )