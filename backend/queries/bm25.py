from config import get_es
import re

INDEX_NAME = "podcast_transcripts"

def strip_highlight_tags(text):
    return re.sub(r"</?em>", "", text or "")

def highlight_words(text, phrase):
    words = phrase.strip().split()

    for word in words:
        pattern = re.compile(rf'\b({re.escape(word)})\b', flags=re.IGNORECASE)
        text = pattern.sub(r'<mark><strong><em>\1</em></strong></mark>', text)
    return text


def get_chunks_by_episode(episode_id, index_name, es=None, debug=True):
    query = {
        "query": {
            "term": {
                "episode_id.keyword": episode_id
            }
        },
        "_source": ["show_id", "episode_id", "chunks"]
    }

    response = es.search(index=index_name, body=query, size=1)

    hits = response.get("hits", {}).get("hits", [])
    if not hits:
        if debug:
            print(f"No document found for episode_id: {episode_id}")
        return []

    source = hits[0]["_source"]
    chunks = source.get("chunks", [])

    results = []
    for chunk in chunks:
        results.append({
            "sentence": chunk.get("sentence"),
            "startTime": chunk.get("startTime"),
            "endTime": chunk.get("endTime")
        })

    return results



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


def mlt_search(query_term, selected_chunks, client, index_name, size=10):
    """
    Runs a 'more_like_this' query using chunks marked as relevant, combined with a boosted match query to reinforce the original search intent.
    """
    like_text = [chunk["transcript"]["chunk"] for chunk in selected_chunks if "transcript" in chunk and "chunk" in chunk["transcript"]]
    if not like_text:
        return []

    query_body = {
        "size": size,
        "query": {
            "bool": {
                "should": [
                    {
                        "more_like_this": {
                            "fields": ["chunks.sentence"],
                            "like": like_text
                        }
                    },
                    {
                        "match": {
                            "chunks.sentence": {
                                "query": query_term,
                                "operator": "and",
                                "boost": 2.0
                            }
                        }
                    }
                ]
            }
        }
    }
    response = client.search(index=index_name, body=query_body)
    hits = response.get("hits", {}).get("hits", [])
    for hit in hits:
        hit["_source"]["query"] = query_term
    return hits


def bm25_query(query_term, index_name=INDEX_NAME, top_k = 10, es = None, chunk_size = 30, debug = True, selected_episodes = None):
    client = es or get_es()
    results = []
    
    if selected_episodes:
        hits = mlt_search(query_term, selected_episodes, client, index_name, top_k)
        
    else:
    
        response = bm25_search(query_term, index_name, top_k = 10, es = client)
        hits = response.get("hits", {}).get("hits", [])


    for hit in hits:
        source = hit["_source"]
        highlight_raw = hit.get("highlight", {}).get("chunks.sentence", [None])[0]
        highlight_clean = strip_highlight_tags(highlight_raw)

        best_chunk = next(
            (chunk for chunk in source.get("chunks", []) 
             if highlight_clean and highlight_clean.lower() in chunk["sentence"].lower()),
            source.get("chunks", [{}])[0]
        )
        
        all_chunks_result = get_chunks_by_episode(source["episode_id"], index_name, es=client, debug=True)
        n_chunks_result = add_chunks_together(all_chunks_result, best_chunk.get("sentence"), chunk_size = chunk_size)

        results.append({
            "show_id": source["show_id"],
            "episode_id": source["episode_id"],
            "score": hit["_score"],
            "start_time" : n_chunks_result.get("start_time"),
            "end_time" : n_chunks_result.get("end_time"),
            "chunk": highlight_words(n_chunks_result.get("chunk"),query_term)            
        })

    return results


def add_chunks_together(chunks, matched_chunk, chunk_size=30):
   
    chunks_to_merge = chunk_size // 30
    matched_idx = next((i for i, chunk in enumerate(chunks) 
                        if chunk.get("sentence") == matched_chunk), None)
    
    if matched_idx is None:
        return {}
    
    left_idx = matched_idx - 1
    right_idx = matched_idx + 1
    count = 1 
    selected_indices = [matched_idx]

    while count < chunks_to_merge:
        
        if left_idx >= 0:
            selected_indices.insert(0, left_idx)
            left_idx -= 1
            count += 1
        
        if count < chunks_to_merge and right_idx < len(chunks):
            selected_indices.append(right_idx)
            right_idx += 1
            count += 1

        if left_idx < 0 and right_idx >= len(chunks):
            break
    
    selected_chunks = [chunks[i] for i in selected_indices]
    
    combined_sentence = ' '.join([chunk.get('sentence', '') for chunk in selected_chunks])
    start_time = selected_chunks[0].get('startTime', None)
    end_time = selected_chunks[-1].get('endTime', None)

    return {
        'start_time': start_time,
        'end_time': end_time,
        'chunk': combined_sentence
    }



if __name__ == "__main__":  
    es = get_es()
    query_term = "dog"
    index_name = "podcast_transcripts2"
    results = bm25_query(query_term, index_name, top_k = 3, es = es, chunk_size = 90, debug = True)
    print(results)