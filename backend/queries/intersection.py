import re
from tqdm import tqdm
from elasticsearch import Elasticsearch 
from config import get_es

INDEX_NAME = "podcast_transcripts"

def highlight_words(text, phrase):
    words = phrase.strip().split()
    for word in words:
        # Match whole word, case-insensitive, word boundaries
        pattern = re.compile(rf'({re.escape(word)})', flags=re.IGNORECASE)
        text = pattern.sub(r'<mark><strong><em>\1</em></strong></mark>', text)
    return text


def intersection_search(query_term, client, index_name, size=10, verbose=False, selectedEpisodes=None):

    def run_query(query):
        query_body = {
            "size": size,
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "chunks.sentence": {
                                    "query": query,
                                    "operator": "and",  # all terms must be present
                                }
                            }
                        }
                    ]
                }
            }
        }
        return client.search(index=index_name, body=query_body)
    
    response = run_query(query_term)
    hits = response['hits']['hits']
    seen = set()
    for hit in hits:
        doc_id = (hit['_source'].get('show_id'), hit['_source'].get('episode_id'))
        seen.add(doc_id)
        hit['_source']['query'] = query_term
    
    # TODO: Put this in a separate function
    if len(hits) < size:
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
                suggest_response = client.search(index=index_name, body=suggest_query)
                print(suggest_response)
                try:
      
                    suggestions = suggest_response["suggest"]["suggestion"]
                    corrected_words = []

                    for entry in suggestions:
                        if entry["options"]:
                            # take the top suggestion (one with the best score)
                            corrected_words.append(entry["options"][0]["text"]) 
                        else:
                            # keep original if no suggestion
                            corrected_words.append(entry["text"])

                    suggested_phrase = " ".join(corrected_words)
                    print(f"Suggested query {suggested_phrase}")
                    if suggested_phrase:
                        new_response = run_query(suggested_phrase)

                        for hit in new_response["hits"]["hits"]:
                            source = hit["_source"]
                            doc_id = (source["show_id"], source["episode_id"])
                            if doc_id not in seen:
                                hit['_source']['query'] = suggested_phrase
                                hits.append(hit)
                                seen.add(doc_id)
                            if len(hits) >= size:
                                break
                except (KeyError, IndexError):
                    pass
                
    return hits


def intersection_mlt_search(query_term, relevant_chunks, client, index_name, size=10, verbose=False): 
    # expect relevant_chunks data struct and type as the one of format_hits in intersection_search.py

    like_text = [chunk["sentence"] for chunk in relevant_chunks]

    query_body = {
        "size": size,
        "query": {
            "bool": {
                "should": [
                    {
                        "more_like_this": {
                            "fields": ["chunks.sentence"],
                            "like": like_text,
                        }
                    },
                    {
                        "match": {
                            "chunks.sentence": {
                                "query": query_term,
                                "operator": "and",
                                "boost": 2.0  # boost docs that match the original query, avoid topic drift due t the added like_text
                            }
                        }
                    }
                ]
            }
        }
    }
        
    response = client.search(index=index_name, body=query_body)
    hits = response['hits']['hits']
    return hits


def get_intersection_chunk_indices(hit, query_term, verbose=False) -> list[int]:

    source = hit['_source']
    chunk_indices = []
    if 'chunks' in source:
        for i, chunk in enumerate(source['chunks']):
            flag = True
            for term in query_term.lower().split():
                if term not in chunk['sentence'].lower():
                    flag = False
                    break
            if flag:
                chunk_indices.append(i)
                
    return chunk_indices


def get_n_30s_chunks(chunks, idx, n=3) -> dict:
    left_idx = idx - 1
    right_idx = idx + 1
    count = 1
    selected_indices = [idx]

    while count < n:
        if left_idx >= 0:
            selected_indices.insert(0, left_idx)
            left_idx -= 1
            count += 1

        if count < n and right_idx < len(chunks):
            selected_indices.append(right_idx)
            right_idx += 1
            count += 1

        if (left_idx < 0 and right_idx >= len(chunks)):
            break
    selected_chunks = [chunks[i] for i in selected_indices]
    return {
        'start_time': float(selected_chunks[0]['startTime'][:-1]), 
        'end_time': float(selected_chunks[-1]['endTime'][:-1]),
        'chunk': ' '.join([chunk['sentence'] for chunk in selected_chunks])
    }



def format_hits(hits, query_term, n=3, verbose=False):

    # Formats search results into a list of dicts with keys ['episode_id', 'show_id', 'startTime', 'endTime', 'sentence', 'query']. 'sentence' contains the concatenated exact n 30-second chunks with the target (matched) chunk centered
    results = []
    for hit in tqdm(hits, disable=not verbose):
        hit_query_term = hit["_source"].get("query", query_term)
        valid_chunk_indices = get_intersection_chunk_indices(hit, hit_query_term, verbose=verbose)
        if len(valid_chunk_indices) == 0:
            continue
        valid_chunk_indices = [valid_chunk_indices[0]]
        for idx in valid_chunk_indices:
            result = get_n_30s_chunks(hit['_source']['chunks'], idx, n=n)
            result['episode_id'] = hit['_source']['episode_id']
            result['show_id'] = hit['_source']['show_id']
            result['query'] = hit_query_term
            result['chunk'] = highlight_words(result['chunk'], hit_query_term)
            results.append(result)

    return results


def intersection_query(query, chunck_size, verbose=True, selected_episodes=None):
    client = get_es()
    n = int(chunck_size / 30)
    
    if(selected_episodes):
        hits = intersection_mlt_search(query, selected_episodes, client, INDEX_NAME, size=10)
    else: 
        hits = intersection_search(query, client, INDEX_NAME, size=10, verbose=verbose)
        
    results = format_hits(hits, query, n, verbose=verbose)
    return results


def main():
    query_term = 'ddog cat'
    verbose = False
    
    hits = intersection_search(query_term, client, INDEX_NAME, size=10, verbose=verbose)
    
    results = format_hits(hits, query_term, n=3, verbose=verbose)
    
    print(f"found {len(results)} matching chunks")
    
    # Print a sample of the results
    if results:
        print("\n example result:")
        for sample in results[:5]:
            print(f"epi id: {sample['episode_id']}")
            print(f"show idx: {sample['show_id']}")
            print(f"For query: {sample['query']}")
            print(f"Chunk: {sample['chunk']}")
            print("------------------\n\n")
   

if __name__ == "__main__":
    INDEX_NAME = "podcast_transcripts"
    
    client = get_es()

    main()
        