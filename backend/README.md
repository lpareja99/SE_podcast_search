# Podcast Search Backend

This project provides a set of Python scripts to index and search podcast transcripts using Elasticsearch. Below is an explanation of how each script works and its purpose.

---

## Prerequisites

- **Elasticsearch**: Ensure Elasticsearch is installed and running locally or on a server.
- **Python Dependencies**: Install the required Python libraries using `pip install -r requirements.txt`. The main dependencies include:
  - `elasticsearch`
  - `tqdm`
  - `urllib3`

---

## Scripts Overview

### 1. `index_all_podcasts.py`

This script indexes all podcast transcripts from a specified folder into Elasticsearch.

- **Key Variables**:
  - `parent_folder`: Path to the folder containing podcast transcript JSON files.
  - `index_name`: Name of the Elasticsearch index where the transcripts will be stored.
  - `only_use_n_json`: Limits the number of JSON files to process (set to `0` to process all files).

- **Workflow**:
  1. **Load JSON Files**: Recursively fetches JSON files from the folder.
  2. **Validate JSON Files**: Ensures the JSON files are valid and can be processed.
  3. **Create Elasticsearch Index**: Creates the index if it doesn't already exist.
  4. **Index Files**: Extracts transcript data and indexes it into Elasticsearch.

- **Run**: Execute the script to index all podcast transcripts:
  ```bash
  python index_all_podcasts.py
  ```


### 2. `search_for_podcasts.py`

This script search revelant podcast transcripts from an index.

- **Key Variables**:
  - `query` : The content of the query
  - `query_type` : The type of the query
  - `index_name`: Name of the Elasticsearch index where the transcripts will be stored.


- **Run**: Execute the script to index all podcast transcripts:
  ```bash
  python search_for_podcasts.py
  ```

### 3. `index_clip_from_one_podcast.py`

This script indexes all n-minute clips from a specified podcast into Elasticsearch.

- **Key Variables**:
  - `file_path`: Path to the podcast (a .json file)
  - `clip_minute`: Clip lenght

- **Workflow**:
  1. **Read the JSON File**
  2. **Create n-minute Clips**
  3. **Create a specific Index**
  4. **Index Clips**

- **Run**: Execute the script to index all podcast transcripts:
  ```bash
  python index_clip_from_one_podcast.py
  ```

### 2. `search_for_clip.py`

This script search revelant clip from a podcast.

- **Key Variables**:
  - `query` : The content of the query
  - `index_name`: Name of the Elasticsearch index where the clips will be stored.


- **Run**: Execute the script to index all podcast transcripts:
  ```bash
  python search_for_clip.py
  ```
