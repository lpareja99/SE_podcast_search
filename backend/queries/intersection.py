import re
from tqdm import tqdm
from config import get_es

INDEX_NAME = "podcast_transcripts"

def highlight_words(text, phrase):
    words = phrase.strip().split()
    for word in words:
        # Match whole word, case-insensitive, word boundaries
        pattern = re.compile(rf'({re.escape(word)})', flags=re.IGNORECASE)
        text = pattern.sub(r'<mark><strong><em>\1</em></strong></mark>', text)
    return text

def get_intersection_chunk_indices(hit, query_term) -> list[int]:
    source = hit['_source']
    chunk_indices = []
    if 'chunks' in source:
        for i, chunk in enumerate(source['chunks']):
            if all(term in chunk['sentence'].lower() for term in query_term.lower().split()):
                chunk_indices.append(i)
    return chunk_indices


def get_n_30s_chunks(chunks, idx, n=3) -> dict:
    left_idx, right_idx = idx - 1, idx + 1
    count, selected_indices = 1, [idx]

    while count < n:
        if left_idx >= 0:
            selected_indices.insert(0, left_idx)
            left_idx -= 1
            count += 1
        if count < n and right_idx < len(chunks):
            selected_indices.append(right_idx)
            right_idx += 1
            count += 1
        if left_idx < 0 and right_idx >= len(chunks):
            break

    selected_chunks = [chunks[i] for i in selected_indices]
    return {
        'start_time': float(selected_chunks[0]['startTime'][:-1]),
        'end_time': float(selected_chunks[-1]['endTime'][:-1]),
        'chunk': ' '.join([chunk['sentence'] for chunk in selected_chunks])
    }
        

def format_hits(hits, query_term, n=3):
    results = []
    for hit in tqdm(hits, disable=not False):
        hit_query_term = hit["_source"].get("query", query_term)
        valid_chunk_indices = get_intersection_chunk_indices(hit, hit_query_term)
        if not valid_chunk_indices:
            continue
        for idx in [valid_chunk_indices[0]]:
            result = get_n_30s_chunks(hit['_source']['chunks'], idx, n=n)
            result.update({
                'episode_id': hit['_source']['episode_id'],
                'show_id': hit['_source']['show_id'],
                'query': hit_query_term,
                'chunk': highlight_words(result['chunk'], hit_query_term)
            })
            results.append(result)
    return results


# Query Functions
def run_query(query, client, index_name, size):
    query_body = {
        "size": size,
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "chunks.sentence": {
                                "query": query,
                                "operator": "and",
                            }
                        }
                    }
                ]
            }
        }
    }
    return client.search(index=index_name, body=query_body)


def handle_suggestions(query_term, client, index_name, hits, seen, size):
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
    try:
        suggestions = suggest_response["suggest"]["suggestion"]
        corrected_words = [
            entry["options"][0]["text"] if entry["options"] else entry["text"]
            for entry in suggestions
        ]
        suggested_phrase = " ".join(corrected_words)
        if suggested_phrase:
            new_response = run_query(suggested_phrase, client, index_name, size)
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
    
    

def intersection_search(query_term, client, index_name, size=10):
    response = run_query(query_term, client, index_name, size)
    hits = response['hits']['hits']
    seen = {(hit['_source'].get('show_id'), hit['_source'].get('episode_id')) for hit in hits}
    for hit in hits:
        hit['_source']['query'] = query_term

    if len(hits) < size:
        handle_suggestions(query_term, client, index_name, hits, seen, size)

    return hits


def intersection_mlt_search(query_term, relevant_chunks, client, index_name, size=10):
    like_text = [chunk["transcript"]["chunk"] for chunk in relevant_chunks]
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
                                "boost": 2.0
                            }
                        }
                    }
                ]
            }
        }
    }
    response = client.search(index=index_name, body=query_body)
    return response['hits']['hits']


# Main Query Function
def intersection_query(query, chunk_size, selected_episodes=None):
    client = get_es()
    n = int(chunk_size / 30)
    if selected_episodes:
        hits = intersection_mlt_search(query, selected_episodes, client, INDEX_NAME, size=10)
    else:
        hits = intersection_search(query, client, INDEX_NAME, size=10)
    return format_hits(hits, query, n)


# Main Function
def main():
    query_term = 'ddog cat'
    client = get_es()
    hits = intersection_search(query_term, client, INDEX_NAME, size=10)
    results = format_hits(hits, query_term, n=3)
    print(f"found {len(results)} matching chunks")
    if results:
        print("\n example result:")
        for sample in results[:5]:
            print(f"epi id: {sample['episode_id']}")
            print(f"show idx: {sample['show_id']}")
            print(f"For query: {sample['query']}")
            print(f"Chunk: {sample['chunk']}")
            print("------------------\n\n")


if __name__ == "__main__":
    main()