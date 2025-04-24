from flask import jsonify
from config import get_es

EPISODE_INDEX = "episodes"
NUM_RESPONSES = 10
es = get_es()

def metadata(transcripts): 
    # Map keys to match expected structure
    transcripts = [
        {"show_id": item["show_id"], "episode_id": item["episode_id"]}
        for item in transcripts
    ]
    
    if not es.indices.exists(index=EPISODE_INDEX):  # Correct index name
        return jsonify({"error": f"Index '{EPISODE_INDEX}' does not exist"}), 404

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
    
    # Process hits to extract relevant fields
    hits = [
        {
            "show_id": hit["_source"]["show_id"],
            "episode_id": hit["_source"]["episode_id"],
            "title": hit["_source"].get("episode_title", ""),
            "description": hit["_source"].get("episode_description", ""),
            "show": hit["_source"].get("show_name", ""),
            "duration": hit["_source"].get("duration", ""),  
            "language": hit["_source"].get("language", ""), 
            "publisher": hit["_source"].get("publisher", ""),  
            "rss_link": hit["_source"].get("rss_link", "")  
        }
        for hit in metadata_response["hits"]["hits"]
    ]

    return hits  # Return processed list

