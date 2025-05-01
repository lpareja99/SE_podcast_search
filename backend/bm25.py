from config import get_es
import re
import os

def strip_highlight_tags(text):
    return re.sub(r"</?em>", "", text or "")

def bm25_search(query_term, index_name, top_k=1, es=None):
    

    if es is None:
        es = get_es()

    query_body = {
        "size": top_k,
        "query": {
            "function_score": {
                "query": {
                    "bool": {
                        "must": [{
                            "match": {
                                "chunks.sentence": {
                                    "query": query_term,
                                    "operator": "and"
                                }
                            }
                        }]
                    }
                },
                "functions": [{
                    "field_value_factor": {
                        "field": "ranking_score",
                        "factor": 1.2,
                        "modifier": "sqrt",
                        "missing": 1.0
                    }
                }],
                "boost_mode": "multiply"
            }
        },
        "highlight": {
            "fields": {
                "chunks.sentence": {
                    "number_of_fragments": 1,
                }
            }
        }
    }

    response = es.search(index=index_name, body=query_body)
    return response



def bm25_query(query_term, index_name, top_k = 1, es = None, chunk_size = 30, debug = True):
    response = bm25_search(query_term, index_name, top_k = 10, es = es)
    results = []

    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        highlight_raw = hit.get("highlight", {}).get("chunks.sentence", [None])[0]
        highlight_clean = strip_highlight_tags(highlight_raw)

        best_chunk = next(
            (chunk for chunk in source.get("chunks", []) 
             if highlight_clean and highlight_clean.lower() in chunk["sentence"].lower()),
            source.get("chunks", [{}])[0]
        )

        results.append({
            "show": source["show_id"],
            "episode": source["episode_id"],
            "score": hit["_score"],
            "start_time" : best_chunk.get("startTime"),
            "end_time" : best_chunk.get("endTime"),
            "matched_chunk": {
                "text": best_chunk.get("sentence"),
                "highlight": highlight_raw
            }
        })

    return results



if __name__ == "__main__":  
    es = get_es()
    query_term = "and the"
    index_name = "podcast_transcripts2"
    results = bm25_query(query_term, index_name, top_k = 3, es = es, chunk_size = 30, debug = True)
    print(results)