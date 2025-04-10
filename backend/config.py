from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import os

def get_es():
    return Elasticsearch(
        hosts=["https://localhost:9200"],
        http_auth=(os.getenv("ELASTIC_USERNAME"), os.getenv("ELASTIC_PASSWORD")),  
        verify_certs=True,
        ca_certs="http_ca.crt",
    )