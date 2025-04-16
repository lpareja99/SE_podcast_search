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

Wouldn’t it be great to find podcasts that discuss exactly what you are interested in at the moment? Or even better, to find the exact part of the podcast that discusses your topic of interest?  The task is to:

1. Use Elasticsearch (https://github.com/elastic/elasticsearch) to index the transcriptions of the podcasts (You will obtain this data from Johan).

2.  Create an interface where a user can enter a search query, e.g. “Higgs Boson”, “terrorism” or “what Jesus means to me”, to find and rank n-minute clips from podcasts that treat this subject (e.g 2-minute-clips, or n can be selectable).

3.  The relevant portions of the transcriptions of the clips can be shown as search results.

This task is inspired by the TREC 2020 podcasts track, task 1. More information on: https://www.aclweb.org/portal/content/trec-2020-podcasts-track-guidelines

## Technical information and set-up

### Technical Info 
- Elastic Search 
- Front End:
    - Posible frameworks:
        - Angular: https://v16.angular.io/docs
        - React: https://react.dev/
        - Flutter: https://flutter.dev/
        - Vue: https://vuejs.org/
    - Possible styling tools:
        - Bootstrap: https://vuejs.org/
        - Tailwind: https://tailwindcss.com/docs/installation/using-postcss
        - Material UI: https://mui.com/material-ui/?srsltid=AfmBOoqnoV-yBmk9uhwxMkZ-mck2v0gOfdXI4yKC4C-8wbU_9qS2iXqh

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
- To obtain password and username: `sudo /usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic`
- Add your username and password to `backend/.env` and install `pip install python-dotenv`
 
### Kibana instalation (to be able to see the data of elastic search)
- `sudo apt update`
- `sudo apt install kibana`
- `sudo systemctl enable kibana`
- `sudo systemctl start kibana`
- `sudo systemctl status kibana`
- Open browser on: sudo systemctl start kibana
- Obtain elastic token: `sudo /usr/share/elasticsearch/bin/elasticsearch-create-enrollment-token --scope kibana`
- Obtain verification code: `sudo journalctl -u kibana | grep "verification code"`

Useful parts of kirbana:
- Tryout calls and endpoints: http://localhost:5601/app/dev_tools#/console/shell

#### DB

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

#### Flask 
- `pip install -r requirements.txt`
- `python app.py`

#### React 

- Install react
- Install `pip install flask-cors`
- To run the app: `npm start`


### Set-up project (Windows)
TBD

### Set-up project (Mac)
TBD

## Database Population

### Metadata Index:

- Go to `/backend` folder.
- If not already, copy your CA to teh backend folder and add your user and your passwrod to the `config.py` file.
- Run `python3 load_metadata.py`
- If succesfull check call by `curl --cacert http_ca.crt -X GET "https://localhost:9200/episodes/_search?pretty" -u elastic` input teh password and it should return json objects.
- With Kibana access http://localhost:5601/app/dev_tools#/console/shell add `GET episodes/_count` and check that it return 105360.

### Transcripts Index:

### Rss_headers:

### summarization_test:


## Tasks

