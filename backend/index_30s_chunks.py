from elasticsearch import Elasticsearch
import os
import json
from glob import glob
from json.decoder import JSONDecodeError
import re
from tqdm import tqdm

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#to disable warnings : "HTTPS without verifying the server's SSL certificate" 


#variables 

parent_folder = "/home/baptiste/kth/SE_podcast_search/spotify-podcasts-2020/podcasts-transcripts-summarization-testset/"  
# replace this with your actual folder path, can be a nested folder
index_name = "podcast_transcripts" #don't change this
# log  = False #if you want more log
only_use_n_json = 2000 #if you want to limit the number of json files to use, set it to 0 to use all the json files
basic_auth = ("elastic", "==4D6GuIwqE=vp7x*bJ8") #your elastic logins

## functions 

def get_n_json_files_from_nested_folders(parent_folder, n=5):
    all_json_files = glob(os.path.join(parent_folder, "**", "*.json"), recursive=True)

    selected_files = all_json_files[:n]
    
    print(f"✅ {len(selected_files)}  JSON fill / {len(all_json_files)}")
    return selected_files

def create_index(index_name: str):
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name)
        print(f"✅ Index '{index_name}' created.")
    else:
        print(f"ℹ️ Index '{index_name}' already exists.")


def find_sentence_chunks(data: list):
    # get sentence chunks from word list, with appropriate startTime and endTime
    if data is None or len(data) == 0:
        return []
    
    chunks = []
    current_chunk = []
    chunk_start_time = None
    
    for index, item in enumerate(data):
        word = item['word']
        
        if not current_chunk:
            chunk_start_time = item['startTime']
        
        current_chunk.append(word)
        
        if (re.search(r'[.!?;:,]$', word) or index == len(data) - 1):
            chunk_text = ' '.join(current_chunk)
            chunk_end_time = item['endTime']
            
            chunks.append({
                'startTime': chunk_start_time,
                'endTime': chunk_end_time,
                'sentence': chunk_text
            })
            current_chunk = []
            chunk_start_time = None
    
    return chunks

def get_30s_chunks(chunks: list):
    # Get 30s segments from sentence chunks
    def time_to_seconds(time_str):
        return float(time_str.rstrip('s'))
    
    merged_chunks = []
    current_chunk = {
        'startTime': None,
        'endTime': None,
        'sentence': '',
        'duration': 0
    }
    
    for chunk in chunks:
        start_seconds = time_to_seconds(chunk['startTime'])
        end_seconds = time_to_seconds(chunk['endTime'])
        chunk_duration = end_seconds - start_seconds

        if current_chunk['startTime'] is None:
            current_chunk['startTime'] = chunk['startTime']
            current_chunk['sentence'] = chunk['sentence']
            current_chunk['duration'] = chunk_duration
            current_chunk['endTime'] = chunk['endTime']
        else:
            tduration = current_chunk['duration'] + chunk_duration
            if tduration >= 28: 
                if abs(30 - tduration) < abs(30 - current_chunk['duration']):
                    current_chunk['sentence'] += ' ' + chunk['sentence']
                    current_chunk['endTime'] = chunk['endTime']
                    current_chunk['duration'] = tduration
                
                merged_chunks.append({
                    'startTime': current_chunk['startTime'],
                    'endTime': current_chunk['endTime'],
                    'sentence': current_chunk['sentence'],
                    'duration': current_chunk['duration']
                })
                
                if abs(30 - tduration) >= abs(30 - current_chunk['duration']):
                    current_chunk = {
                        'startTime': chunk['startTime'],
                        'endTime': chunk['endTime'],
                        'sentence': chunk['sentence'],
                        'duration': chunk_duration
                    }
                else:
                    current_chunk = {
                        'startTime': None,
                        'endTime': None,
                        'sentence': '',
                        'duration': 0
                    }
            else:
                current_chunk['sentence'] += ' ' + chunk['sentence']
                current_chunk['endTime'] = chunk['endTime']
                current_chunk['duration'] = tduration
    
    if current_chunk['startTime'] is not None:
        merged_chunks.append(current_chunk)
    
    return merged_chunks


def format_json(input_file):
    podcast_id = os.path.basename(os.path.dirname(input_file))
    
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)

    except JSONDecodeError as e:
        print(f"JSONDecodeError in file: {input_file} — {e}")
        return {}
    except Exception as e:
        print(f"⚠Unexpected error in file: {input_file} — {e}")
        return {}

    num_words = 0
    chunks_list = []
    for result in data.get('results', []):
        for alternative in result.get('alternatives', []):
            transcript = alternative.get('transcript', '')
            num_words += len(transcript.split())
            words = alternative.get('words', [])
            if transcript.strip() == '':
                continue

            # word list (word, startTime, endTime) is used to obtain sentence chunks
            chunks = find_sentence_chunks(words)
            chunks_list += chunks

    # all sentence chunks are processed to ~30s segments 
    formatted_chunks = get_30s_chunks(chunks_list)
    output = {
        'episode_id': podcast_id,
        'num_words': num_words,
        'chunks': formatted_chunks
    }

    return output

def main():
    json_files = get_n_json_files_from_nested_folders(parent_folder, n=only_use_n_json)

    create_index(index_name)
    for file in tqdm(json_files, desc="Indexing files"):
        formatted_doc = format_json(file)
        if formatted_doc == {}:
            continue
        es.index(index=index_name, document=formatted_doc)

    print(f"✅ All documents indexed into Elasticsearch in {index_name}.")


if __name__ == "__main__":
    es = Elasticsearch(
        "https://localhost:9200",
        basic_auth=basic_auth,  
        verify_certs=False  
    )

    if es.ping():
        print("✅ Elasticsearch is up and running.")
    else:
        print("❌ Can't connect to Elasticsearch.")
    main()