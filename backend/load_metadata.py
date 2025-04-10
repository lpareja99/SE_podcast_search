import csv
from elasticsearch.helpers import bulk
from config import get_es

es = get_es()
index_name = "episodes"
file_path = "../podcasts-no-audio-13GB/metadata/spotify-podcasts-2020/metadata.tsv"

def create_index():
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)

    mapping = {
        "mappings": {
            "properties": {
                "episode_id": {"type": "keyword"},
                "episode_title": {"type": "text"},
                "episode_description": {"type": "text"},
                "show_id": {"type": "keyword"},
                "show_name": {"type": "text"},
                "publisher": {"type": "text"},
                "language": {"type": "keyword"},
                "rss_link": {"type": "text"},
                "duration": {"type": "float"}
            }
        }
    }

    es.indices.create(index=index_name, body=mapping)

def load_data(tsv_path):
    with open(tsv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        actions = []
        for row in reader:
            doc = {
                "episode_id": row["episode_uri"],
                "episode_title": row["episode_name"],
                "episode_description": row["episode_description"],
                "show_id": row["show_uri"],
                "show_name": row["show_name"],
                "publisher": row["publisher"],
                "language": row["language"],
                "rss_link": row["rss_link"],
                "duration": float(row["duration"]) if row["duration"] else None
            }
            actions.append({
                "_index": index_name,
                "_id": doc["episode_id"],
                "_source": doc
            })

            if len(actions) >= 1000:
                bulk(es, actions)
                actions.clear()

        if actions:
            bulk(es, actions)

if __name__ == "__main__":
    create_index()
    load_data(file_path)
    print("Data loaded successfully.")
