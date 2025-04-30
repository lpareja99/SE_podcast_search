from tqdm import tqdm
from elasticsearch import Elasticsearch 
from config import get_es


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
        'startTime': selected_chunks[0]['startTime'],
        'endTime': selected_chunks[-1]['endTime'],
        'sentence': ' '.join([chunk['sentence'] for chunk in selected_chunks])
    }


def format_hits(hits, query_term, n=3, verbose=False):

    # Formats search results into a list of dicts with keys ['episode_id', 'show_id', 'startTime', 'endTime', 'sentence']. 'sentence' contains the concatenated exact n 30-second chunks with the target (matched) chunk centered

    results = []
    for hit in tqdm(hits, disable=not verbose):
        valid_chunk_indices = get_intersection_chunk_indices(hit, query_term, verbose=verbose)
        if len(valid_chunk_indices) == 0:
            continue
        valid_chunk_indices = [valid_chunk_indices[0]]
        for idx in valid_chunk_indices:
            result = get_n_30s_chunks(hit['_source']['chunks'], idx, n=n)
            result['episode_id'] = hit['_source']['episode_id']
            result['show_id'] = hit['_source']['show_id']
            results.append(result)

    return results


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

    if verbose:
        print(f"Total hits: {response['hits']['total']['value']}")
        print(f"Number of hits returned: {len(hits)}")
    return hits


def main():
    query_term = 'dog cat'
    verbose = False
    
    print(f"Query: '{query_term}'")
    
    hits = intersection_search(query_term, client, INDEX_NAME, size=10, verbose=verbose)
    
    results = format_hits(hits, query_term, n=3, verbose=verbose)
    
    print(f"found {len(results)} matching chunks")
    if results:
        print("\n example result:")
        for sample in results[:5]:
            # sample = results[0]
            print(f"epi id: {sample['episode_id']}")
            print(f"show idx: {sample['show_id']}")
            print(f"setnence: {sample['sentence']}")
            print(f"start time: {sample['startTime']}")
            print(f"end time: {sample['endTime']}\n")

    print('Do MLT search')
    selected_chunks_index = [2, 3]
    relevant_chunks = [results[i] for i in selected_chunks_index]
    hits = intersection_mlt_search(query_term, relevant_chunks, client, INDEX_NAME, size=10, verbose=verbose)
    mlt_results = format_hits(hits, query_term, n=3, verbose=verbose)
    print(f"found {len(mlt_results)} matching mlt chunks")
    if mlt_results:
        print("\n MLT example result:")
        for sample in mlt_results[:5]:
            print(f"epi id: {sample['episode_id']}")
            print(f"show idx: {sample['show_id']}")
            print(f"setnence: {sample['sentence']}")
            print(f"start time: {sample['startTime']}")
            print(f"end time: {sample['endTime']}\n")

    # the order changes
    # more documents might be added

if __name__ == "__main__":
    INDEX_NAME = "podcast_transcripts"
    
    client = get_es()

    main()
        
