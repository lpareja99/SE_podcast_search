from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv
load_dotenv()

basic_auth=(os.getenv("ELASTIC_USERNAME"), os.getenv("ELASTIC_PASSWORD")) 

index_name = "episodes"


es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=basic_auth,  
    verify_certs=False  
)
def reset_index(index_name):
    # Delete the index if it exists
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        print(f"🗑️ Deleted index: {index_name}")



reset_index(index_name)