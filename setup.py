from setuptools import setup, find_packages

setup(
    name="openmetadata-my-custom-csv-connector", # Nom de votre package
    version="0.1.0", # Version de votre connecteur
    packages=find_packages(where="connectors"), # Cherche les packages dans le dossier 'connectors'
    package_dir={"": "connectors"}, # Indique où trouver les packages
    install_requires=[
        "openmetadata-ingestion", # Dépendance essentielle
        # Ajoutez ici toute autre dépendance si votre connecteur en avait besoin (ex: "pandas", "requests")
    ],
    entry_points={
        "openmetadata_sources": [
            # Format: <nom_court_du_connecteur> = <nom_du_package_racine_de_votre_connecteur>.<nom_du_module>:<NomDeVotreClasseSource>
            "csvdb = connectors.my_csv_connector.connector:MyCustomCsvSource",
        ],
    },
)