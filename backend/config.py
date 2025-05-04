from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import os

def get_es():
    load_dotenv()
    return Elasticsearch(
        hosts=["https://localhost:9200"],
        http_auth=(os.getenv("ELASTIC_USERNAME"), os.getenv("ELASTIC_PASSWORD")),  
        verify_certs=True,
        ca_certs="http_ca.crt",
    )