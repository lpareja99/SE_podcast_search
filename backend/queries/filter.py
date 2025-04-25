from config import get_es

INDEX_NAME = "episodes"

def search_episodes(query_text, search_field="show_name", index_name=INDEX_NAME, top_k=5, es=None):
    """
    Search episodes in the Elasticsearch index by a specified field.

    Parameters:
        query_text (str): Text to search.
        search_field (str): Field to perform the match on. One of "show_name", "publisher", or "episode_title".
        index_name (str): Elasticsearch index name. Defaults to "episodes".
        top_k (int): Number of top results to return. Defaults to 5.
        es (Elasticsearch, optional): Existing Elasticsearch client. If None, a new one is fetched from get_es().

    Returns:
        List[dict]: List of episode documents with relevant fields. Fields are : "show_id", "episode_id", "show_name", "episode_title", "publisher", "episode_description", "rss_link".
    """
    if es is None:
        es = get_es()

    if search_field not in ["show_name", "publisher", "episode_title"]:
        raise ValueError("Invalid search_field. Must be one of: 'show_name', 'publisher', or 'episode_title'")

    print(query_text, search_field)
    query = {
        "size": top_k,
        "query": {
            "match": {
                search_field:  f"*{query_text.lower()}*"
            }
        }
        
    }

    response = es.search(index=index_name, body=query)
    
    print(response)
    results = []
    for hit in response["hits"]["hits"]:
        result = {
            "show_id": hit["_source"].get("show_id", ""),
            "episode_id": hit["_source"].get("episode_id", ""),
            "show": hit["_source"].get("show_name", ""),
            "title": hit["_source"].get("episode_title", ""),
            "publisher": hit["_source"].get("publisher", ""),
            "description": hit["_source"].get("episode_description", ""),
            "rss_link": hit["_source"].get("rss_link", ""),
            "language": hit["_source"].get("language", ""),
        }
        results.append(result)

    return results


def debug_print(results):
    for i, result in enumerate(results):
        print(f"\n🎧 Result {i+1}")
        print(f"Show Name: {result.get('show_name', 'N/A')}")
        print(f"Episode Title: {result.get('episode_title', 'N/A')}")
        print(f"Publisher: {result.get('publisher', 'N/A')}")
        print(f"Episode Description: {result.get('episode_description', '')[:150]}...")
        print(f"RSS Link: {result.get('rss_link', 'N/A')}")
        print(f"Show ID: {result.get('show_id', 'N/A')}")
        print(f"Episode ID: {result.get('episode_id', 'N/A')}")
        print("-" * 50)


if __name__ == "__main__":
    es = get_es()
    query_text = "Olivia"  # Replace with your search text
    print(f"\n\n🔍 Searching for '{query_text}'...\n")
    print("🔍 Searching by Publisher...\n")
    results = search_episodes(query_text, search_field="publisher", es=es, top_k=5)
    debug_print(results)

    print("\n\n🔍 Searching by Show Name...\n")
    results = search_episodes(query_text, search_field="show_name", es=es, top_k=5)
    debug_print(results)

    print("\n\n🔍 Searching by Episode Title...\n")
    results = search_episodes(query_text, search_field="episode_title", es=es, top_k=5)
    debug_print(results)
