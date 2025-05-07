# Podcast search

## Table of Contents
- [Authors](#authors)
- [General Information of the project](#general-information-of-the-project)
- [Technical information and set-up](#technical-information-and-set-up)
- [Database Population](#database-population)
- [Tasks](#tasks)
- [Project Info](#project-info)


## Authors: 
- 	Léonard Belenge Dalnor: lbd@kth.se
-   Baptiste Boutaud de la Combe: boabdlc@kth.se
-   Laura Pareja Prieto: laurapp@kth.se
-   Jun Wei Serena Wang: jwswang@kth.se


## General Information of the project

### Task Given

Wouldn’t it be great to find podcasts that discuss exactly what you are interested in at the moment? Or even better, to find the exact part of the podcast that discusses your topic of interest?  The task is to:

1. Use Elasticsearch (https://github.com/elastic/elasticsearch) to index the transcriptions of the podcasts (You will obtain this data from Johan).

2.  Create an interface where a user can enter a search query, e.g. “Higgs Boson”, “terrorism” or “what Jesus means to me”, to find and rank n-minute clips from podcasts that treat this subject (e.g 2-minute-clips, or n can be selectable).

3.  The relevant portions of the transcriptions of the clips can be shown as search results.

This task is inspired by the TREC 2020 podcasts track, task 1. More information on: https://www.aclweb.org/portal/content/trec-2020-podcasts-track-guidelines

### What our Search Engine Can Do
- UI design Spotify like for intuitive use by the user
- Single endpoint /search that keeps front end clean and detach from backend.
- Audio and image show display for enhanced experience for the user.
- Audio for each episode can be played from the beguinning and from start time of the relevant transcript found.
- Size of the transcript to search for and display can be vary from 30 sec to 5 min by the user. 
- Highlight of relevant information on the transcript obtained. 
- Elastic search implementation for fast and powerfull index management.
- Types of general searchs avilable: Intersection, Phrase and Ranking (bm-25).
- Additional search avialable by "filter" where user can look for specific results based on show name, episode title and author. 
- Enhance search for queries with typos using "suggest" to provide user with a more complete experience in case of small typos. 
- Basic relevance feedback implemented using "more_like_this" given a wuery and the relevant transcript of one or more selected episode.

## Technical information and set-up

### Technical Info 
- Elastic Search:
    - Main Page: https://www.elastic.co/docs/solutions/search
- Front End:
        - React: https://react.dev/
        - Bootstrap: https://vuejs.org/
com/docs/installation/using-postcss


- Back End:
    - Flask: https://flask.palletsprojects.com/en/stable/
    - Python: https://docs.python.org/3.12/tutorial/index.html
    - Node.js: https://nodejs.org/en && https://www.elastic.co/guide/en/cloud/current/ec-getting-started-node-js.html

### Set-up project (Ubuntu)

#### Elastic Search Intallation
- Add its repository and update the GPG key: `wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg`
- Add the Elasticsearch repository to the system's apt sources list: `echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list`
- Update packages: `sudo apt update`
- Install Elasticsearch from the repository: `sudo apt install elasticsearch`
- start the Elasticsearch service manually: `sudo systemctl daemon-reload`.
- Configure Elasticsearch to start automatically during system boot: `sudo systemctl enable elasticsearch.service`
- Start elatic search: `sudo systemctl start elasticsearch.service`
- Check status: `sudo systemctl status elasticsearch.service`
- Add cert to the backend folder: `sudo mv /etc/elasticsearch/certs/http_ca.crt /backend/`
- Ensure certificafe has the right permissions: `sudo chmod 644 http_ca.crt`
- Add it to the config.py file:
'''
    def get_es():
        return Elasticsearch(
            hosts=["https://localhost:9200"],
            http_auth=(os.getenv("ELASTIC_USERNAME"), os.getenv("ELASTIC_PASSWORD")),  
            verify_certs=True,
            ca_certs="http_ca.crt",
        )
'''
- To obtain password and username: `sudo /usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic` (better if teh password does not have "=")
- If the `/backend/.env` file exists add teh password to the file, otherwise create a new `.env` file at `/backend` folder level that looks like the:
'''
ELASTIC_PASSWORD={password}
ELASTIC_USERNAME=elastic
ELASTIC_TOKEN={token}
ELASTIC_VERIFICTION_CODE={code_optional}
ELASTICSEARCH_URL=https://localhost:9200
'''

- Install `pip install python-dotenv`
 
### Kibana instalation (to be able to see the data of elastic search)
- `sudo apt update`
- `sudo apt install kibana`
- `sudo systemctl enable kibana`
- `sudo systemctl start kibana`
- `sudo systemctl status kibana`
- Open browser on: sudo systemctl start kibana
- Obtain elastic token: `sudo /usr/share/elasticsearch/bin/elasticsearch-create-enrollment-token --scope kibana`
- Obtain verification code: `sudo journalctl -u kibana | grep "verification code"`
- Check access to kibana: http://localhost:5601/app/management/data/index_management/indices


#### DB

- Note: If you got the project by a zip file, you probably already have the transcrips and the structure of the transcripts correctly integrated.

- Download DB: https://kth-my.sharepoint.com/personal/jboye_ug_kth_se/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fjboye%5Fug%5Fkth%5Fse%2FDocuments%2Fbox%5Ffiles%2Fpodcasts%2Dno%2Daudio%2D13GB%2Ezip&parent=%2Fpersonal%2Fjboye%5Fug%5Fkth%5Fse%2FDocuments%2Fbox%5Ffiles.

- Copy file to your project repo
- Unzip file:  `unzip podcasts-no-audio-13GB.zip`
- Unzip tar files:
    - Transcripts (it would take a while): `mkdir -p transcripts && for f in podcasts-transcripts-*.tar.gz; do tar -xvzf "$f" -C ./transcripts/; done`
    - spotify-podcasts-2020-summarization-testset: `mkdir -p summarization-testset && for f in spotify-podcasts-2020-summarization-testset.tar.gz; do tar -xvzf "$f" -C ./summarization-testset/; done`
    - Show-rrs: `mkdir -p show-rss && for f in show-rss.tar.gz; do tar -xvzf "$f" -C ./show-rss/; done`
    - Scripts: `mkdir -p scripts && for f in scripts.tar.gz; do tar -xvzf "$f" -C ./scripts/; done`
    - Metadata: `mkdir -p metadata && for f in metadata.tar.gz; do tar -xvzf "$f" -C ./metadata/; done`

#### Pyhton

- Install python and pip if not installed
- Create virtual environment: `python3 -m venv venv`
- Activate veirtual environment: `source venv/bin/activate`

#### Start Flask Project
- Activate veirtual environment: `source venv/bin/activate`
- `pip install -r requirements.txt`
- To get the backend running: `python app.py`

#### React 

- Activate veirtual environment: `source venv/bin/activate`
- Install react: TODO: check
- Install `pip install flask-cors`
- Install node modules: `npm install`
- To run the app: `npm start`

## Database Population

### Metadata Index:

- Go to `/backend` folder.
- If not already, copy your CA to the backend folder and add your user and your passwrod to the `config.py` file.
- Check if the file `final_podcast_table_all_with_unmatched.csv` exist on the folder index_creation. If not run the last cell on the python book `generate_metadata_with_audio.ipynb`. Take into account that it can take up to an hour to generate the csv file. Once the file is generated, place it on the `/backend/index_creation` folder.
- Run `python3 ./index_creation/load_metadata_with_audio.py`
- If succesfull check call by `curl --cacert http_ca.crt -X GET "https://localhost:9200/episodes/_search?pretty" -u elastic` input teh password and it should return json objects.
- With Kibana access http://localhost:5601/app/dev_tools#/console/shell add `GET episodes/_count` and check that it return 105360.

### Transcripts Index:

- Go to `/backend/index_creation` folder.
- Run script `index_30s_chuncks.py` it can take a while.


## Run Project

- Once all steps have been done you should be able to get the project running from the root of the project by running:
- Activate veirtual environment: `source venv/bin/activate`
- `python ./backend/app.py`
- `cd frontend` + `npm start`

- Note: If you get an error similar to 
```
Error during search: Connection error caused by: ConnectionError(Connection error caused by: NewConnectionError(<elastic_transport._node._urllib3_chain_certs.HTTPSConnection object at 0x7f9e79371460>: Failed to establish a new connection: [Errno 111] Connection refused))
127.0.0.1 - - [07/May/2025 11:55:04] "POST /search HTTP/1.1" 500 -
```
Check elasticsearch status using `sudo systemctl status elasticsearch.service`. If the active field is `failed` try to stpop the backend and restart elastic search service with the command `sudo systemctl restart elasticsearch.service`. Then start the back en service again (`python /backend/app.py`)




