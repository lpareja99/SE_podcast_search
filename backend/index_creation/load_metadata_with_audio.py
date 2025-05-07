import csv
import sys
import os
from elasticsearch.helpers import bulk
from elasticsearch import Elasticsearch
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.config import get_es

es =  get_es()
index_name = "episodes"
file_path = "final_podcast_table_all_with_unmatched.csv"  # Path to the generated CSV file

def create_index():
    # Delete the index if it already exists
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)

    # Define the mapping for the new index
    mapping = {
        "mappings": {
            "properties": {
                "episode_id": {"type": "keyword"},
                "episode_title": {"type": "text"},
                "show_id": {"type": "keyword"},
                "show_name": {"type": "text"},
                "image_show": {"type": "text"},
                "image_episode": {"type": "text"},
                "audio_url": {"type": "text"},
                "duration": {"type": "float"},
                "episode_description": {"type": "text"},
                "language": {"type": "keyword"},
                "publisher": {"type": "text"},
                "rss_link": {"type": "text"}
            }
        }
    }

    # Create the index with the specified mapping
    es.indices.create(index=index_name, body=mapping)

def load_data(csv_path):
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        actions = []
        for row in reader:
            # Prepare the document for Elasticsearch
            doc = {
                "episode_id": row["episode_id"],
                "episode_name": row["episode_name"],
                "show_id": row["show_id"],
                "show_name": row["show_name"],
                "image_show": row["image_show"],
                "image_episode": row["image_episode"],
                "audio_url": row["audio_url"],
                "duration": row["duration"],
                "episode_description": row["episode_description"],
                "language": row["language"],
                "publisher": row["publisher"],
                "rss_link": row["rss_link"]
            }
            actions.append({
                "_index": index_name,
                "_id": doc["episode_id"],
                "_source": doc
            })

            # Bulk insert every 1000 documents
            if len(actions) >= 1000:
                bulk(es, actions)
                actions.clear()

        # Insert remaining documents
        if actions:
            bulk(es, actions)

if __name__ == "__main__":
    create_index()
    print("Loading data into Elasticsearch...")
    load_data(file_path)
    print("Data loaded successfully.")