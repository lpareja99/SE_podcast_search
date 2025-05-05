from config import get_es
import re
import itertools

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


def get_suggested_query(query_term, client, index_name):
    """
    Runs a suggest query and returns the corrected phrase, if different.
    """
    suggest_query = {
        "suggest": {
            "suggestion": {
                "text": query_term,
                "term": {
                    "field": "chunks.sentence",
                    "suggest_mode": "always",
                    "min_word_length": 2,
                    "max_edits": 2,
                    "prefix_length": 1
                }
            }
        }
    }

    try:
        suggest_response = client.search(index=index_name, body=suggest_query)
        suggestions = suggest_response["suggest"]["suggestion"]
        sugested_words = []
        sugested_scores = []
        words = []
        scores = []
        for entry in suggestions: 
            if len(entry["options"]) > 0:
                for word in entry["options"]:
                    words.append(word["text"])
                    scores.append(word["score"])
            else:
                words.append(entry["text"])
                scores.append(1)
            sugested_words.append(words)
            sugested_scores.append(scores)
            words = []
            scores = []

        combinations = [' '.join(combo) for combo in itertools.product(*sugested_words)]
        scores = [sum(combo) for combo in itertools.product(*sugested_scores)]


        dict_combinations = {}
        for i in range(len(combinations)):
            dict_combinations[combinations[i]] = scores[i]
        
        dict_combinations = dict(sorted(dict_combinations.items(), key=lambda item: item[1], reverse=True))
        print(dict_combinations)
        

        return list(dict_combinations.keys())

    except (KeyError, IndexError) as e:
        print(f"Error in suggestion query for: {query_term}")
        print(e)

        return []


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


def format_hits(hits, query_term, chunk_size=3, client=None, index_name=INDEX_NAME):
    results = []
    
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
            "chunk": highlight_words(n_chunks_result.get("chunk"),query_term), 
            "query": hit["_source"].get("query", query_term)            
        })
        
    return results



def bm25_query(query_term, index_name=INDEX_NAME, top_k = 10, es = None, chunk_size = 30, debug = True, selected_episodes = None):
    client = es or get_es()
    
    if selected_episodes:
        hits = mlt_search(query_term, selected_episodes, client, index_name, top_k)
        
        if len(hits) < top_k:
            if debug:
                print(f"Not enough results for query: {query_term}. Attempting suggestions...")
            correcteds = get_suggested_query(query_term, client, index_name)
            print(correcteds)
            for corrected in correcteds:
                if corrected and corrected.lower() != query_term.lower():
                    if debug:
                        print(f"Using suggested query: {corrected}")
                    hits = mlt_search(corrected, selected_episodes, client, index_name, top_k)
                    query_term = corrected
                if len(hits) >= top_k:
                    break
        
    else:
    
        response = bm25_search(query_term, index_name, top_k = 10, es = client)
        hits = response.get("hits", {}).get("hits", [])
        
        if len(hits) < top_k:
            if debug:
                print(f"Not enough results for query: {query_term}. Attempting suggestions...")
            correcteds = get_suggested_query(query_term, client, index_name)
            for corrected in correcteds:
                if corrected and corrected.lower() != query_term.lower():
                    if debug:
                        print(f"Using suggested query: {corrected}")
                    response = bm25_search(corrected, index_name, top_k=top_k, es=client)
                    hits = response.get("hits", {}).get("hits", [])
                    query_term = corrected
                if len(hits) >= top_k:
                    break

    return format_hits(hits, query_term, chunk_size=chunk_size, client=client)



if __name__ == "__main__":  
    es = get_es()
    query_term = "a biig cat"
    index_name = "podcast_transcripts"
    results = bm25_query(query_term, index_name, top_k = 3, es = es, chunk_size = 90, debug = True)
    if results:
        print("\n example result:")
        for sample in results[:10]:
            print(f"epi id: {sample['episode_id']}")
            print(f"show idx: {sample['show_id']}")
            print(f"For query: {sample['query']}")
            print(f"Chunk: {sample['chunk']}")
            print("------------------\n\n")