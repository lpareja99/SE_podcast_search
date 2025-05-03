from elasticsearch import Elasticsearch
import os
import json
from glob import glob
from json.decoder import JSONDecodeError
from tqdm import tqdm

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#to disable warnings : "HTTPS without verifying the server's SSL certificate" 


#variables 

parent_folder = "/home/baptiste/kth/SE_podcast_search/spotify-podcasts-2020/podcasts-transcripts-summarization-testset/"  
# replace this with your actual folder path, can be a nested folder
index_name = "podcast_transcripts" #don't change this
log  = False #if you want more log
only_use_n_json = 2000 #if you want to limit the number of json files to use, set it to 0 to use all the json files
basic_auth = ("elastic", "==4D6GuIwqE=vp7x*bJ8") #your elastic logins

## functions 

def get_n_json_files_from_nested_folders(parent_folder, n=5):
    all_json_files = glob(os.path.join(parent_folder, "**", "*.json"), recursive=True)

    selected_files = all_json_files[:n]
    
    print(f"✅ {len(selected_files)}  JSON fill / {len(all_json_files)}")
    return selected_files

def get_valid_json_data(file_paths):
    valid_json_path = []
    for fpath in tqdm(file_paths, desc="Checking files"):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                valid_json_path.append(fpath)                
        except JSONDecodeError as e:
            if(log):
                print(f"❌ JSONDecodeError in file: {fpath} — {e}")
        except Exception as e:
            if(log):
                print(f"⚠️ Unexpected error in file: {fpath} — {e}")

    print(f"✅ Loaded {len(valid_json_path)} valid JSON files / {len(file_paths)}")
    print("❌ Failed to load", len(file_paths) - len(valid_json_path), "files")
    return valid_json_path

def create_index(index_name):
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name)
        print(f"✅ Index '{index_name}' created.")
    else:
        print(f"ℹ️ Index '{index_name}' already exists.")


def index_file(valid_json_files):
    for fpath in tqdm(valid_json_files, desc="Indexing files"):
        fname = os.path.basename(fpath)
        with open(fpath, "r") as f:
            data = json.load(f)

        words = [
            {
                "word": w["word"],
                "start": w["startTime"],
                "end": w["endTime"]
            }
            for result in data["results"]
            for alt in result["alternatives"]
            for w in alt.get("words", [])
        ]

        transcript = ""
        for result in data["results"]:
            for alt in result["alternatives"]:
                if "transcript" in alt:
                    transcript += alt["transcript"] + " "


        transcript = transcript.strip()
        

        doc = {
            "filename": fname,
            "filepath" : fpath,
            # folder name is the episode name
            "transcript": transcript,
            "words": words
        }

        es.index(index=index_name, document=doc)
    if(log):
        print(f"✅ Indexed {fname} into Elasticsearch in {index_name}.")
        print("-" * 40)

def main():
    json_files = get_n_json_files_from_nested_folders(parent_folder, n=2000)
    valid_json_files = get_valid_json_data(json_files)
    create_index(index_name)
    index_file(valid_json_files)

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
