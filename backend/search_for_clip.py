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


basic_auth = ("elastic", "==4D6GuIwqE=vp7x*bJ8") #your elastic logins
index_name = "1fe39osodbzeqt3u2msc3k_0.5_minutes"
query = "a big cat"


## functions 

def phrase_query(query, index_name):
    response = es.search(
        index=index_name,
        query={
            "match_phrase": {
                "transcript": query
            }
        }
    )
    return format_clip_results(response)

def intersection_query(query, index_name):
    terms = query.lower().split()
    must_clauses = [{"match": {"transcript": term}} for term in terms]

    response = es.search(
        index=index_name,
        query={
            "bool": {
                "must": must_clauses
            }
        }
    )
    return format_clip_results(response)

def score_query(query, index_name):
    response = es.search(
        index=index_name,
        query={
            "match": {
                "transcript": {
                    "query": query,
                    "operator": "or"
                }
            }
        }
    )
    return format_clip_results(response)





def format_clip_results(response):
    results = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        results.append({
            "filename": source.get("filename"),
            "clip_id": source.get("clip_id"),
            "start_time": source.get("start_time"),
            "end_time": source.get("end_time"),
            "score": hit.get("_score"),
            "snippet": source.get("transcript")  # preview first 300 chars
        })
    return results


def main():
    print("\n🔍 Phrase Query:")
    for result in phrase_query(query, index_name):
        print(result['clip_id'])
        print(f"Duration {result['end_time'] - result['start_time']} seconds")
        print(f"Score {result['score']}")
        print(result['snippet'])

    print("\n📘 Intersection Query:")
    for result in intersection_query(query, index_name):
        print(result['clip_id'])
        print(f"Duration {result['end_time'] - result['start_time']} seconds")
        print(f"Score {result['score']}")
        print(result['snippet'])

    print("\n🌟 Score-Based Query:")
    for result in score_query(query, index_name):
        print(result['clip_id'])
        print(f"Duration {result['end_time'] - result['start_time']} seconds")
        print(f"Score {result['score']}")
        print(result['snippet'])
    


    
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
    
    main()