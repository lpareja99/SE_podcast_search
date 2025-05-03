from elasticsearch import Elasticsearch
import os
import json
from glob import glob
from json.decoder import JSONDecodeError
from tqdm import tqdm

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#to disable warnings : "HTTPS without verifying the server's SSL certificate" 

#variables 

index_name = "podcast_transcripts" #don't change this
log  = False #if you want more log
query = "big cat"
query_type="phrase" #can be : "phrase", "intersection" or "score"
basic_auth = ("elastic", "==4D6GuIwqE=vp7x*bJ8") #your elastic logins



## functions 



def search_words(query, index="podcast_transcripts", query_type="phrase"):
    try:
        if query_type == "phrase":
            es_query = phrase_query(query)
        elif query_type == "intersection":
            es_query = intersection_query(query)
        elif query_type == "score":
            es_query = score_query(query)
        else:
            raise ValueError("Invalid query_type. Use 'phrase', 'intersection', or 'score'.")

        response = es.search(index=index, query=es_query, size=10)
        return process_results(response)
    
    except Exception as e:
        print(f"Search failed: {e}")
        return []

# --- Subfunctions below ---

def phrase_query(query):
    return {
        "match_phrase": {
            "transcript": query
        }
    }

def intersection_query(query):
    words = query.split()
    return {
        "bool": {
            "must": [{"match": {"transcript": word}} for word in words]
        }
    }

def score_query(query):
    return {
        "match": {
            "transcript": {
                "query": query,
                "operator": "or"
            }
        }
    }


def process_results(response):
    results = []
    for hit in response.get("hits", {}).get("hits", []):
        doc = hit["_source"]
        transcript = doc.get("transcript", "")
        filename = doc.get("filename", "unknown")
        filepath = doc.get("filepath", "unknown")

        score = hit.get("_score", 0.0)

        results.append({
            "filename": filename,
            "filepath" :filepath ,
            "score": score,
            "transcript" : transcript
        })

    return results

def main(query, index, query_type):
    results = search_words(query, index=index_name, query_type=query_type)
    for r in results:
        print(f"\n🎙️ {r['filename']} (Score: {r['score']:.2f})")
        print(f"{r['filepath']}")





if __name__ == "__main__":
    es = Elasticsearch(
        "https://localhost:9200",
        basic_auth=basic_auth,  
        verify_certs=False  
    )

    if es.ping():
        print("✅ Elasticsearch is up and running.")
    else:
        print("❌ Can't connect to Elasticsearch.")
    print(f"\nIntersection query for : '{query}'")
    main(query,index_name,"intersection")
    print("######################################################################")
    print(f"\nScore query for : '{query}'")
    main(query,index_name,"score")
    print("######################################################################")

    print(f"\nPhrase query for : '{query}'")
    main(query,index_name,"phrase")
    print("######################################################################")


        

