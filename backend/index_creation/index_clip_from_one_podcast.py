from elasticsearch import Elasticsearch
import os
import json
from glob import glob
from json.decoder import JSONDecodeError
from tqdm import tqdm
from time import time 

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#to disable warnings : "HTTPS without verifying the server's SSL certificate" 


#variables 

file_path = "/home/baptiste/kth/SE_podcast_search/spotify-podcasts-2020/podcasts-transcripts-summarization-testset/3/M/show_3mag99EygwfUS7UZPdVOuq/1fE39oSODbzEQt3u2mSC3K.json"
basic_auth = ("elastic", "==4D6GuIwqE=vp7x*bJ8") #your elastic logins
clip_minute = 0.5 # = 30s

## functions 

def parse_time(t):
    return float(t.replace("s", "")) #Converts '123.456s' -> float seconds.

def index_podcast_clips(json_path, n_minutes=2):
    with open(json_path, "r") as f:
        data = json.load(f)

    filename = os.path.basename(json_path)
    podcast_name = os.path.splitext(filename)[0]
    index_name = f"{podcast_name}_{n_minutes}_minutes".lower()
    total_clip_secs = n_minutes * 60

    transcripts = []


    for result in data["results"]:

        for alt in result["alternatives"]:


            transcript = {}
            transcript["transcript"] = alt.get("transcript", "")
            if alt.get("words"):

                transcript["start"] = parse_time(alt.get("words")[0].get("startTime", "0s"))
                transcript["end"] = parse_time(alt.get("words")[-1].get("endTime", "0s"))
                transcripts.append(transcript)

            else:
                print("⚠️ No words found in alternative.")


    clips = []
    clip = ""
    clip_start_time = None
    
    for transcript in transcripts:

        if clip == "":
            clip_start_time = transcript["start"]
        clip += transcript["transcript"]

        clip_duration = transcript["end"] - clip_start_time
        if clip_duration >= total_clip_secs:
            print("\n Generated clip : \n")
            print(clip)
            print("\n########################################")
            clips.append({
                "clip_id": len(clips) + 1,
                "transcript": clip,
                "start_time": clip_start_time,
                "end_time": transcript["end"],
                "filename": filename,
                "file_path" : json_path
            })
            clip = ""

    # Handle last leftover clip if needed
    if clip:
        clips.append({
                "clip_id": len(clips) + 1,
                "transcript": clip,
                "start_time": clip_start_time,
                "end_time": transcript["end"],
                "filename": filename,
                "file_path" : json_path
            })

    # Create index and push to ES
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name)

    for clip_doc in tqdm(clips, desc=f"Indexing {index_name}"):
        es.index(index=index_name, document=clip_doc)

    print(f"✅ Indexed {len(clips)} clips into {index_name}.")

def main():
    start = time()
    index_podcast_clips(file_path, n_minutes=clip_minute)  # 15 seconds
    print("Time taken:", time() - start, "seconds")



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