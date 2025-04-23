from flask import jsonify
from config import get_es

EPISODE_INDEX = "episodes"
NUM_RESPONSES = 10
es = get_es()

def metadata(transcripts): 
    
    if not es.indices.exists(index=EPISODE_INDEX):
        return jsonify({"error": "Index 'podcast_metadata' does not exist"}), 404

    metadata_query = {
        "size": NUM_RESPONSES,
        "query": {
            "bool": {
                "should": [
                    {
                        "bool": {
                            "must": [
                                { "term": { "episode_id": item["episode_id"] } },
                                { "term": { "show_id": item["show_id"] } }
                            ]
                        }
                    }
                    for item in transcripts
                ]
            }
        }
    }
    
    metadata_response = es.search(index=EPISODE_INDEX, body=metadata_query)
    
    hits = [
        {
            "title": hit["_source"]["episode_title"],
            "description": hit["_source"]["episode_description"],
            "show": hit["_source"]["show_name"]
        }
        for hit in metadata_response["hits"]["hits"]
    ]

    return jsonify(hits if hits else []) 

