import re
from tqdm import tqdm
from elasticsearch import Elasticsearch 
from config import get_es


def highlight_words(text, phrase):
    words = phrase.strip().split()
    for word in words:
        # Match whole word, case-insensitive, word boundaries
        pattern = re.compile(rf'\b({re.escape(word)})\b', flags=re.IGNORECASE)
        text = pattern.sub(r'<mark>\1</mark>', text)
    return text


def intersection_search(query_term, client, index_name, size=10, verbose=False):

    query_body = {
        "size": size,
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "chunks.sentence": {
                                "query": query_term,
                                "operator": "and",  # all terms must be present
                                # "fuzziness": 1  
                            }
                        }
                    }
                ]
            }
        }
    }
    response = client.search(index=index_name, body=query_body)
    hits = response['hits']['hits']

    if verbose:
        print(f"Total hits: {response['hits']['total']['value']}")
        print(f"Number of hits returned: {len(hits)}")
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
    if verbose:
        print(f'indices of valid chunks: {len(chunk_indices)}',  chunk_indices)
    return chunk_indices


def get_n_30s_chunks(chunks, idx, n=3) -> list:
    # return list of n chunks centered around idx

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

    return [chunks[i] for i in selected_indices]


def format_hits(hits, query_term, n=3, verbose=False):

    # Formats search results into a list of dicts with keys ['episode_id', 'show_id', 'target_index', 'chunks']. Each 'chunks' list contains exactly n 30-second chunks with the target (matched) chunk centered

    results = []
    for i, hit in tqdm(enumerate(hits), disable=not verbose):          
        valid_chunk_indices = get_intersection_chunk_indices(hit, query_term, verbose=verbose) 
        if len(valid_chunk_indices) == 0:
            continue
        # to only get the first match as phase search
        valid_chunk_indices = [valid_chunk_indices[0]]
        results += [
            {
                'episode_id': hit['_source']['episode_id'],
                'show_id': hit['_source']['show_id'],
                'target_index': idx,
                'chunks': get_n_30s_chunks(hit['_source']['chunks'], idx, n=n)
            }
            for idx in valid_chunk_indices
        ]
    return results


def main():
    query_term = 'dog cat'
    verbose = False
    
    print(f"Query: '{query_term}'")
    
    hits = intersection_search(query_term, client, INDEX_NAME, size=10, verbose=verbose)
    
    results = format_hits(hits, query_term, n=3, verbose=verbose)
    
    print(f"found {len(results)} matching chunks")
    
    # Print a sample of the results
    if results:
        print("\n example result:")
        for sample in results[:5]:
            # sample = results[0]
            print(f"epi id: {sample['episode_id']}")
            print(f"show idx: {sample['show_id']}")
            print(f"matched chunk idx: {sample['target_index']}")
            print("chunks retrieved:")
            for i, chunk in enumerate(sample['chunks']):
                print(f"  {i+1}. {chunk['sentence'][:100]}...")

if __name__ == "__main__":
    INDEX_NAME = "podcast_transcripts"
    
    client = get_es()

    main()
        