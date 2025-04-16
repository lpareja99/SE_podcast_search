from elasticsearch import Elasticsearch

basic_auth = ("elastic", "==4D6GuIwqE=vp7x*bJ8") #your elastic logins
index_name = "1fe39osodbzeqt3u2msc3k_0.5_minutes"


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