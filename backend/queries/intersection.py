import re
from tqdm import tqdm
from config import get_es
import itertools


INDEX_NAME = "podcast_transcripts"

def highlight_words(text, phrase):
    """
    Highlights all words from the given phrase in the text (case-insensitive),
    """
    words = phrase.strip().split()
    for word in words:
        pattern = re.compile(rf'({re.escape(word)})', flags=re.IGNORECASE)
        text = pattern.sub(r'<mark><strong><em>\1</em></strong></mark>', text)
    return text


# Query Functions
def run_query(query_term, client, index_name, size=10):
    """
    Executes a match query with 'AND' operator over 'chunks.sentence' to retrieve documents that contain all query terms.
    """
    query_body = {
        "size": size,
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "chunks.sentence": {
                                "query": query_term,
                                "operator": "and"
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


def handle_suggestions(query_term, client, index_name, hits, seen, size=10):
    """
    If not enough results were found, runs a suggest query on 'chunks.sentence'. Re-executes the search with the corrected phrase and appends new results.
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
        response = client.search(index=index_name, body=suggest_query)
        suggestions = response["suggest"]["suggestion"]
        corrected_words = [
            entry["options"][0]["text"] if entry["options"] else entry["text"]
            for entry in suggestions
        ]
        suggested_phrase = " ".join(corrected_words)

        if suggested_phrase and suggested_phrase.lower() != query_term.lower():
            new_hits = run_query(suggested_phrase, client, index_name, size)
            for hit in new_hits:
                doc_id = (hit["_source"]["show_id"], hit["_source"]["episode_id"])
                if doc_id not in seen:
                    hit["_source"]["query"] = suggested_phrase
                    hits.append(hit)
                    seen.add(doc_id)
                if len(hits) >= size:
                    break

    except Exception:
        pass
    
    
def get_suggested_query(phrase, es, index_name):
    suggest_query = {
        "suggest": {
            "word_suggest": {
                "text": phrase,
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
        suggest_response = es.search(index=index_name, body=suggest_query)
        suggestions = suggest_response["suggest"]["word_suggest"]
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

        #sugested_words = [[word["text"] if len(entry["options"])>0 else entry["text"] for word in entry["options"]] for entry in suggestions if entry["options"]] 
        #sugested_score = [[word["score"] for word in entry["options"]] for entry in suggestions if entry["options"]] 
        combinations = [' '.join(combo) for combo in itertools.product(*sugested_words)]
        scores = [sum(combo) for combo in itertools.product(*sugested_scores)]


        dict_combinations = {}
        for i in range(len(combinations)):
            dict_combinations[combinations[i]] = scores[i]
        
        dict_combinations = dict(sorted(dict_combinations.items(), key=lambda item: item[1], reverse=True))
        print(dict_combinations)
        

        return list(dict_combinations.keys())

    except (KeyError, IndexError):
        return []


    
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
    

def get_intersection_chunk_indices(hit, query_term) -> list[int]:
    """
    Returns indices of chunks that contain all query terms.
    """
    source = hit['_source']
    chunk_indices = []
    if 'chunks' in source:
        for i, chunk in enumerate(source['chunks']):
            if all(term in chunk['sentence'].lower() for term in query_term.lower().split()):
                chunk_indices.append(i)
    return chunk_indices


def get_n_30s_chunks(chunks, idx, n=3):
    """
    Given a chunk index, expands to n ~30s chunks by adding neighbors before/after to form a longer contiguous segment.
    """
    left_idx, right_idx = idx - 1, idx + 1
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
        if left_idx < 0 and right_idx >= len(chunks):
            break
        
    selected_chunks = [chunks[i] for i in selected_indices]
    return {
        'start_time': float(selected_chunks[0]['startTime'][:-1]),
        'end_time': float(selected_chunks[-1]['endTime'][:-1]),
        'chunk': ' '.join(chunk['sentence'] for chunk in selected_chunks)
    }


def format_hits(hits, query_term, n=3):
    """
    Given a list of documents (hits), selects the best chunk from each one that contains all query terms and returns:
    - episode_id, show_id, query
    - chunk (highlighted), start_time, end_time
    """
    results = []
    for hit in tqdm(hits, disable=False):
        q_term = hit["_source"].get("query", query_term)
        chunk_indices = get_intersection_chunk_indices(hit, q_term)
        if not chunk_indices:
            continue
        idx = chunk_indices[0]
        chunk_data = get_n_30s_chunks(hit["_source"]["chunks"], idx, n=n)
        chunk_data.update({
            "episode_id": hit["_source"]["episode_id"],
            "show_id": hit["_source"]["show_id"],
            "query": q_term,
            "chunk": highlight_words(chunk_data["chunk"], q_term)
        })
        results.append(chunk_data)
    return results



# Main Query Function
def intersection_query(query_term, chunk_size, selected_episodes=None):
    """
    Main fuction. Runs either standard or MLT-based intersection search, applies suggestions if needed, and returns formatted results.
    """
    client = get_es()
    size = 10
    n = int(chunk_size / 30)

    if selected_episodes:
        print("executing MLT search")
        hits = mlt_search(query_term, selected_episodes, client, INDEX_NAME, size)
        print("MLT hits", hits)
        print(len(hits))
        if len(hits) < size:
            correcteds = get_suggested_query(query_term, client, INDEX_NAME)
            for corrected in correcteds:
                if corrected and corrected.lower() != query_term.lower():
                    hits += mlt_search(corrected, selected_episodes, client, INDEX_NAME, size)
                    query_term = corrected
                if len(hits) >= size:
                    break
    else:
        hits = run_query(query_term, client, INDEX_NAME, size)
        print(len(hits))
        if len(hits) < size:

            correcteds = get_suggested_query(query_term, client, INDEX_NAME)
            for corrected in correcteds:
                if corrected and corrected.lower() != query_term.lower():
                    hits += run_query(corrected, client, INDEX_NAME, size)
                    print(len(hits))    
                    query_term = corrected
                if len(hits) >= size:
                    break


    return format_hits(hits, query_term, n)


# Main Function - for testing the script
def main():
    query_term = 'ddog caats'
    client = get_es()
    hits = intersection_query(query_term, 30)
    print("hits")
    print(hits[0])
    #results = format_hits(hits, query_term, n=3)
    print(f"found {len(hits)} matching chunks")
    if hits:
        print("\n example result:")
        for sample in hits[:10]:
            print(f"epi id: {sample['episode_id']}")
            print(f"show idx: {sample['show_id']}")
            print(f"For query: {sample['query']}")
            print(f"Chunk: {sample['chunk']}")
            print("------------------\n\n")


if __name__ == "__main__":
    main()