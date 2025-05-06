from config import get_es
import itertools 
INDEX_NAME = "episodes"


def mlt_search(query_text, selected_chunks, client, index_name, size=10):
    """
    Perform a more_like_this query based on the selected chunks.
    """
    like_text = [chunk["transcript"]["chunk"] for chunk in selected_chunks if "transcript" in chunk and "chunk" in chunk["transcript"]]
    if not like_text:
        return []

    query = {
        "size": size,
        "_source": ["show_id", "episode_id", "show_name", "episode_title", "publisher", "episode_description", "rss_link", "language"],
        "query": {
            "more_like_this": {
                "fields": ["chunks.sentence"],
                "like": like_text
            }
        }
    }

    response = client.search(index=index_name, body=query)
    return response.get("hits", {}).get("hits", [])


def get_suggested_query(query_text, search_field, index_name, es):
    """
    Runs a suggest query and returns the corrected phrase, if different.
    """
    suggest_query = {
        "suggest": {
            "suggestion": {
                "text": query_text,
                "term": {
                    "field": search_field,
                    "suggest_mode": "always",
                    "min_word_length": 3
                }
            }
        }
    }

    try:
        suggest_response = es.search(index=index_name, body=suggest_query)
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


def format_hits(hits, query_text):
    """
    Formats Elasticsearch hits into a structured list of dictionaries.
    """
    results = []
    seen = set()

    for hit in hits:
        doc_id = (hit["_source"].get("show_id"), hit["_source"].get("episode_id"))
        if doc_id not in seen:
            seen.add(doc_id)
            results.append({
                "show_id": hit["_source"].get("show_id", ""),
                "episode_id": hit["_source"].get("episode_id", ""),
                "show": hit["_source"].get("show_name", ""),
                "title": hit["_source"].get("episode_name", ""),
                "publisher": hit["_source"].get("publisher", ""),
                "description": hit["_source"].get("episode_description", ""),
                "rss_link": hit["_source"].get("rss_link", ""),
                "language": hit["_source"].get("language", ""),
                "query": query_text,
                "audio": hit["_source"].get("audio_url", ""),
                "episode_image": hit["_source"].get("image_episode", ""),
                "show_image": hit["_source"].get("image_show", "")
            })

    return results


def search_episodes(query_text, search_field="show_name", index_name=INDEX_NAME, top_k=5, es=None):
    """
    Search episodes in the Elasticsearch index by a specified field, with suggestion and MLT fallback.

    Parameters:
        query_text (str): Text to search.
        search_field (str): Field to perform the match on. One of "show_name", "publisher", or "episode_title".
        index_name (str): Elasticsearch index name. Defaults to "episodes".
        top_k (int): Number of top results to return. Defaults to 5.
        es (Elasticsearch, optional): Existing Elasticsearch client. If None, a new one is fetched from get_es().

    Returns:
        List[dict]: List of episode documents with relevant fields.
    """
    if es is None:
        es = get_es()

    if search_field not in ["show_name", "publisher", "episode_name"]:
        raise ValueError("Invalid search_field. Must be one of: 'show_name', 'publisher', or 'episode_name'")

    def run_query(text):
        query = {
            "size": top_k,
            "query": {
                "match": {
                    search_field: text
                }
            }
        }
        return es.search(index=index_name, body=query)

    # Step 1: Initial search
    response = run_query(query_text)
    hits = response["hits"]["hits"]
    for hit in hits:
        hit["_source"]["query"] = query_text  # Add the query text to each hit
    print(hits)

    # Step 2: Suggestion fallback if results are insufficient
    corrected_query = query_text  # Default to the original query
    if len(hits) < top_k:
        suggested_querys = get_suggested_query(query_text, search_field, index_name, es)
        for suggested_query in suggested_querys:
            if suggested_query.lower() != query_text.lower():
                corrected_query = suggested_query
                suggest_response = run_query(corrected_query)
                hits.extend(suggest_response["hits"]["hits"])
            if len(hits) >= top_k:
                break

    # Step 3: More Like This (MLT) fallback if results are still insufficient
    if len(hits) < top_k:
        mlt_query = {
            "size": top_k - len(hits),
            "_source": ["show_id", "episode_id", "show_name", "episode_name", "publisher", "episode_description", "rss_link", "language"],
            "query": {
                "more_like_this": {
                    "fields": [search_field],
                    "like": query_text,
                    "min_term_freq": 1,
                    "max_query_terms": 12
                }
            }
        }
        mlt_response = es.search(index=index_name, body=mlt_query)
        hits.extend(mlt_response["hits"]["hits"])

    # Format the hits with the final query (corrected or original)
    return format_hits(hits, corrected_query)


def debug_print(results):
    for i, result in enumerate(results):
        print(f"\n🎧 Result {i+1}")
        print(f"Show Name: {result.get('show', 'N/A')}")
        print(f"Episode Title: {result.get('title', 'N/A')}")
        print(f"Publisher: {result.get('publisher', 'N/A')}")
        print(f"Episode Description: {result.get('description', '')[:150]}...")
        print(f"RSS Link: {result.get('rss_link', 'N/A')}")
        print(f"Show ID: {result.get('show_id', 'N/A')}")
        print(f"Episode ID: {result.get('episode_id', 'N/A')}")
        print(f"Query: {result.get('query', 'N/A')}")
        print("-" * 50)


if __name__ == "__main__":
    es = get_es()
    query_text = "a biig cat"  # Replace with your search text
    print(f"\n\n🔍 Searching for '{query_text}'...\n")
    print("🔍 Searching by Publisher...\n")
    results = search_episodes(query_text, search_field="publisher", es=es, top_k=10)
    debug_print(results)

    print("\n\n🔍 Searching by Show Name...\n")
    results = search_episodes(query_text, search_field="show_name", es=es, top_k=10)
    debug_print(results)

    print("\n\n🔍 Searching by Episode Title...\n")
    results = search_episodes(query_text, search_field="episode_name", es=es, top_k=10)
    debug_print(results)
