from config import get_es
import re
import itertools

INDEX_NAME = "podcast_transcripts"


def highlight_words(text, phrase):
    """
    Highlights the full phrase (not individual words) in the text (case-insensitive).
    """
    pattern = re.compile(re.escape(phrase), re.IGNORECASE)
    return pattern.sub(r"<mark><strong><em>\g<0></em></strong></mark>", text)


def get_suggested_phrase(phrase, es, index_name):
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
        return None
    
    
def phrase_search(phrase, index_name=INDEX_NAME, top_k=10, es=None):
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
            "show_id": source["show_id"],
            "episode_id": source["episode_id"],
            "query": phrase
        })

    if len(results) < top_k:
        suggested_phrases = get_suggested_phrase(phrase, es, index_name)
        for suggested_phrase in suggested_phrases:
            if suggested_phrase and suggested_phrase.lower() != phrase.lower() and len(results) < top_k:
                new_response = do_query(suggested_phrase)

                for hit in new_response["hits"]["hits"]:
                    source = hit["_source"]
                    doc_id = (source["show_id"], source["episode_id"])
                    if doc_id not in seen:
                        results.append({
                            "show_id": source["show_id"],
                            "episode_id": source["episode_id"],
                            "query": suggested_phrase
                        })
                        seen.add(doc_id)
                    if len(results) >= top_k:
                        break
            if len(results) >= top_k:
                break

    return results


def get_first_chunk(show_id, episode_id, phrase, index_name=INDEX_NAME, es=None, chunk_size = 30):
    
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
            if len(doc["chunks"]) == doc["chunks"].index(chunk) + 1 :
                break
            next_chunk = doc["chunks"][doc["chunks"].index(chunk) + 1]
            
            endTime = get_time_from_string(next_chunk["endTime"])
            startTime = get_time_from_string(best_chunk["startTime"])
            tolerance  =  15 #10% of chunk_size
            while endTime - startTime < chunk_size + tolerance:
                #if next_chunk is the last chunk, break
                if doc["chunks"].index(next_chunk) == len(doc["chunks"]) - 1:
                    break
                #add next chunk to best_chunk
                best_chunk["sentence"] += " " + next_chunk["sentence"]
                best_chunk["endTime"] = next_chunk["endTime"]

                next_chunk = doc["chunks"][doc["chunks"].index(next_chunk) + 1]
                endTime = get_time_from_string(next_chunk["endTime"])

            break #we retrieve the first chunk that matches

    if best_chunk:
        highlighted_sentence = highlight_words(best_chunk["sentence"], phrase)
        return {
            "show_id": show_id,
            "episode_id": episode_id,
            "chunk": highlighted_sentence,
            "start_time": best_chunk["startTime"],
            "end_time": best_chunk["endTime"],
            "query": phrase
        }
    else:
        return None
    
def get_time_from_string(str):
    return float(str[:-1])


def mlt_search(phrase, selected_chunks, client, index_name, size):
        like_text = [chunk["transcript"]["chunk"] for chunk in selected_chunks if "transcript" in chunk and "chunk" in chunk["transcript"]]
        if not like_text:
            return []

        query = {
            "size": size,
            "_source": ["show_id", "episode_id", "chunks"],
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
                            "match_phrase": {
                                "chunks.sentence": {
                                    "query": phrase,
                                    "boost": 2.0
                                }
                            }
                        }
                    ]
                }
            }
        }

        response = client.search(index=index_name, body=query)
        hits = response.get("hits", {}).get("hits", [])
        for hit in hits:
            hit["_source"]["query"] = phrase
        return hits


def phrase_query(phrase, index_name= INDEX_NAME, top_k = 10, es = None, chunk_size = 30, debug = False, selected_episodes = None):
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
    
    if es is None:
        es = get_es()
        
    # Perform the more_like_this based on whether `selected_episodes` is provided
    if selected_episodes:
        
        hits = mlt_search(phrase, selected_episodes, es, index_name, top_k)
        
        if len(hits) < top_k:
            corrected = get_suggested_phrase(phrase, es, index_name)
            if corrected and corrected.lower() != phrase.lower():
                hits = mlt_search(corrected, selected_episodes, es, index_name, top_k)
                phrase = corrected
        
        response = hits
            
            
    else:
        # Perform normal phrase search
        response = phrase_search(phrase, index_name=index_name, top_k=top_k, es=es)
    
    results = []
    for doc in response:
        
        if debug:
            print(f"Show ID: {doc['show_id']}, Episode ID: {doc['episode_id']}")
            print("\n🎯 Best Chunk in Episode:")
            
        source = doc["_source"] if "_source" in doc else doc
        best_chunk = get_first_chunk(source['show_id'], source['episode_id'], source['query'], index_name, es=es, chunk_size=chunk_size)
        if best_chunk:
            results.append(best_chunk)
            if debug:
                print(f"Show: {best_chunk['show_id']}")
                print(f"Episode: {best_chunk['episode_id']}")
                print(f"Chunk: {best_chunk['chunk']}")
                print(f"Time: {best_chunk['start_time']} → {best_chunk['end_time']}")
                print(f"Query: {best_chunk['query']} (original was {phrase})")
                print(f"Time: {float(best_chunk['start_time'][:-1]) - float(best_chunk['end_time'][:-1])}")
                print("|----------------------------------|\n\n")
        else:
            print("No chunk found for.")
    return results

    
if __name__ == "__main__":  
    es = get_es()
    q = "th climat chnge"
    results = phrase_query(q, index_name=INDEX_NAME, top_k = 10, es = es, chunk_size = 60, debug = True)
 