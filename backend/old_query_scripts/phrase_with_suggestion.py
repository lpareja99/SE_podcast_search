from config import get_es


def phrase_search(phrase, index_name, top_k=1, es=None):
    if es is None:
        es = get_es()
    
    def do_query(q):
        query = {
            "size": top_k,
            "_source": ["show_id", "episode_id", "chunks"],
            "query": {
                "match_phrase": {
                    "chunks.sentence": q
                }
            }
        }
        return es.search(index=index_name, body=query)
    
    response = do_query(phrase)
    results = []
    seen = set()

    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        doc_id = (source["show_id"], source["episode_id"])
        seen.add(doc_id)
        results.append({
            "show": source["show_id"],
            "episode": source["episode_id"],
            "query" : phrase
        })

    if len(results) < top_k:
        suggest_query = {
            "suggest": {
                "word_suggest": {
                    "text": phrase,
                    "term": {
                        "field": "chunks.sentence",
                        "suggest_mode": "always",
                        "min_word_length": 3
                    }
                }
            }
        }
        suggest_response = es.search(index=index_name, body=suggest_query)

        try:
            suggestions = suggest_response["suggest"]["word_suggest"]
            corrected_words = []

            for entry in suggestions:
                if entry["options"]:
                    # take the top suggestion (one with the best score)
                    corrected_words.append(entry["options"][0]["text"]) 
                else:
                    # keep original if no suggestion
                    corrected_words.append(entry["text"])

            suggested_phrase = " ".join(corrected_words)
            if suggested_phrase:
                new_response = do_query(suggested_phrase)

                for hit in new_response["hits"]["hits"]:
                    source = hit["_source"]
                    doc_id = (source["show_id"], source["episode_id"])
                    if doc_id not in seen:
                        results.append({
                            "show": source["show_id"],
                            "episode": source["episode_id"],
                            "query": suggested_phrase
                        })
                        seen.add(doc_id)
                    if len(results) >= top_k:
                        break
        except (KeyError, IndexError):
            pass

    return results


def get_first_chunk(show_id, episode_id, phrase, index_name, es=None, chunk_size = 30):
    
    if es is None:
        es = get_es()
    
    if chunk_size not in [30, 60, 90, 120, 180, 300]:
        raise ValueError("chunk_size must be one of [30, 60, 90, 120, 180, 300] seconds")
    
    #retrieve entry that match show_id and episode_id
    query = {
        "size": 1,
        "query": {
            "bool": {
                "must": [
                    {"match": {"show_id": show_id}},
                    {"match": {"episode_id": episode_id}}
                ]
            }
        }
    }

    response = es.search(index=index_name, body=query)
    if not response["hits"]["hits"]:
        return None

    doc = response["hits"]["hits"][0]["_source"]
    best_chunk = None
    #search for the first chunk that matches the phrase
    for chunk in doc["chunks"]:
        score = phrase.lower() in chunk["sentence"].lower()
        if score:
            best_chunk = chunk
            next_chunk = chunk
            #add chunk to best_chunk so chunk duration is chunk_size
            endTime = get_time_from_string(best_chunk["endTime"])
            startTime = get_time_from_string(best_chunk["startTime"])
            while endTime - startTime < chunk_size:
                #if next_chunk is the last chunk, break
                if doc["chunks"].index(next_chunk) == len(doc["chunks"]) - 1:
                    break
                #add next chunk to best_chunk
                
                next_chunk = doc["chunks"][doc["chunks"].index(next_chunk) + 1]
                best_chunk["sentence"] += " " + next_chunk["sentence"]
                best_chunk["endTime"] = next_chunk["endTime"]
                endTime = get_time_from_string(best_chunk["endTime"])


            break #we retrieve the first chunk that matches

    if best_chunk:
        return {
            "show": show_id,
            "episode": episode_id,
            "chunk": best_chunk["sentence"],
            "start_time": best_chunk["startTime"],
            "end_time": best_chunk["endTime"],
            "query": phrase
        }
    else:
        return None
    
def get_time_from_string(str):
    return float(str[:-1])

def phrase_query(phrase, index_name, top_k = 1, es = None, chunk_size = 30, debug = False):
    """
    Search for a phrase in the transcript chunks of podcast episodes stored in Elasticsearch.

    This function performs a phrase search across podcast transcripts and retrieves 
    the first matching chunk from each top result. Each chunk is extended (if needed) 
    to fit the specified duration (`chunk_size`).

    Parameters:
        phrase (str): The phrase to search for in transcript chunks.
        index_name (str): The name of the Elasticsearch index to search.
        top_k (int, optional): The number of top results (episodes) to retrieve. Default is 1.
        es (Elasticsearch, optional): An existing Elasticsearch client instance. If None, a new one is fetched from `get_es()`.
        chunk_size (int, optional): Desired duration (in seconds) of the output chunk. Must be one of [30, 60, 90, 120, 180, 300]. Default is 30.
        debug (bool, optional): If True, prints debug information about matched results. Default is False.

    Returns:
        List[dict]: A list of dictionaries, each containing:
            - show (str): The show ID.
            - episode (str): The episode ID.
            - chunk (str): The chunk of transcript text containing the phrase.
            - start_time (str): Start time of the chunk (e.g., '5.43s').
            - end_time (str): End time of the chunk (e.g., '35.29s').
    """

    documents = phrase_search(phrase, index_name,top_k= top_k, es=es)
    results = []
    for doc in documents:
        if debug:
            print(f"Show ID: {doc['show']}, Episode ID: {doc['episode']}")
            print("\n🎯 Best Chunk in Episode:")
        best_chunk = get_first_chunk(doc['show'], doc['episode'], doc['query'], index_name, es=es, chunk_size=chunk_size)
        if best_chunk:
            results.append(best_chunk)
            if debug:
                print(f"Show: {best_chunk['show']}")
                print(f"Episode: {best_chunk['episode']}")
                print(f"Chunk: {best_chunk['chunk']}")
                print(f"Time: {best_chunk['start_time']} → {best_chunk['end_time']}")
                print(f"Query: {best_chunk['query']} (original was {phrase})")
                print("|----------------------------------|\n\n")
        else:
            print("No chunk found for.")
    return results

    
if __name__ == "__main__":  
    es = get_es()
    phrase = "climte chage"
    index_name = "podcast_transcripts"
    results = phrase_query(phrase, index_name, top_k = 10, es = es, chunk_size = 30, debug = True)
        
