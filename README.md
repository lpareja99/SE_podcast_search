# Podcast search

## Table of Contents
- [Authors](#authors)
- [General Information of the project](#general-information-of-the-project)
- [Technical information and set-up](#technical-information-and-set-up)
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
- Add your username and password to `backend/.env` and install `pip install python-dotenv`
 
### Kibana instalation (to be able to see the data of elastic search)
- `sudo apt update`
- `sudo apt install kibana`
- `sudo systemctl enable kibana`
- `sudo systemctl start kibana`
- `sudo systemctl status kibana`
- Open browser on: http://localhost:5601
- Obtain elastic token: `sudo /usr/share/elasticsearch/bin/elasticsearch-create-enrollment-token --scope kibana`
- Obtain verification code: `sudo journalctl -u kibana | grep "verification code"`

Useful parts of kirbana:
- Tryout calls and endpoints: http://localhost:5601/app/dev_tools#/console/shell

#### DB

- Download DB:https://kth-my.sharepoint.com/personal/jboye_ug_kth_se/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fjboye%5Fug%5Fkth%5Fse%2FDocuments%2Fbox%5Ffiles%2Fpodcasts%2Dno%2Daudio%2D13GB%2Ezip&parent=%2Fpersonal%2Fjboye%5Fug%5Fkth%5Fse%2FDocuments%2Fbox%5Ffiles.

- Copy file to your project repo
- Unzip file:  `unzip podcasts-no-audio-13GB.zip`
- Unzip tar files:
    - Transcripts(it would take a while): `mkdir -p transcripts && for f in podcasts-transcripts-*.tar.gz; do tar -xvzf "$f" -C ./transcripts/; done`
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

#### Populate indexes on ElasticSearch 
- Populate Metadata:
    - Go to `/backend` folder.
    - If not already, copy your CA to teh backend folder and add your user and your passwrod to the `config.py` file.
    - Run `python3 load_metadata.py`
    - If succesfull check call by `curl --cacert http_ca.crt -X GET "https://localhost:9200/episodes/_search?pretty" -u elastic` input teh password and it should return json objects.
    - With Kibana access http://localhost:5601/app/dev_tools#/console/shell add `GET episodes/_count` and check that it return 105360.

#### React 


### Set-up project (Windows)
TBD

### Set-up project (Mac)
TBD

## Tasks


## Project Info 

README - Spotify Podcasts 2020 Dataset
======

Last modified 2020-DEC-23

Dataset Title: 
Spotify Podcasts 2020 Dataset
Data Version:
2020-MAY-14
Test Set Version:
2020-JUL-21
Contact: 
podcasts-challenge-organizers@spotify.com
When using this dataset please cite this paper: 
"100,000 Podcasts: A Spoken English Document Corpus" by Ann Clifton, Sravana Reddy, Yongze Yu, Aasish Pappu, Rezvaneh Rezapour, Hamed Bonab, Maria Eskevich, Gareth Jones, Jussi Karlgren, Ben Carterette, and Rosie Jones, COLING 2020

Permission to use - You must sign up for TREC here: https://ir.nist.gov/trecsubmit.open/application.html 
and also sign the data usage agreement which can be obtained by by contacting: podcasts-challenge-organizers@spotify.com

How to Download From Box.com
============================
You can download directly from the website, or from the command line using rclone. Box.com also provides other tools.

From website
-	When you are given access to the shared directory on Box.com you will be able to right-click on a file or directory and select download

-  	We recommend first downloading the subdirectory podcasts-no-audio-13GB/ which contains transcripts, rss, scripts, metadata, etc., to your project.
	Then if you also want the ~ 2TB of audio data, download podcasts-audio-only-2TB.  If you download the entire Spotify-Podcast-2020 directory
	the entire dataset would take up ~2Tb disk space. See below for descriptions of the subdirectories and space requirements.

OR

Using rclone

$curl https://rclone.org/install.sh | sudo bash
$rclone config
- No remotes found - make a new one  n/s/q> n
- name> trecbox 
- Choose a number from below, or type in your own value Storage> 6
- client_id>:  #enter leave empty
- client_secret>: #enter leave empty
- box_config_file>: #enter leave empty
- box_sub_type>: 1
- Edit advanced config? (y/n)  y/n> n
- Use auto config? (y/n)  y/n> n
- Then paste the result below:
	- $rclone authorize box #run this on a seperate terminal
	- result> {"access_token":"....","token_type":"...","refresh_token":".....","expiry":"...."}

$rclone ls trecbox:
$rclone copy -P trecbox:{PODCASTS_DIRECTORY} /path/to/your/project

OR

Other Tools You can Use
https://www.box.com/resources/downloads/drive


Unpacking and checking your downloaded data set
===============================================

There are two sub-directories, podcasts-audio-only-2TB and podcasts-no-audio-13GB in main directory in box.com. The contents in those directories are described below.


Audio files
-----------

There are 105360 ogg files arranged in the show-id subdirectories in the podcasts-audio-only-2TB directory. For details, please refer to section data structure below.

Transcripts
-----------
There are three tar files of transcripts in podcasts-no-audio-13GB directory
podcasts-transcripts-0to2.tar.gz (4.6 GB)- 39892 transcripts
podcasts-transcripts-3to5.tar.gz (4.6 GB)- 41273 transcripts
podcasts-transcripts-6to7.tar.gz (2.8 GB)- 24195 transcripts


Untar on Unix/Mac using 
tar -xzvf <filename>.tar -C <your_data_path>

All three tar files untar to the same directory with the subdirectories which will be described in next section: 
spotify-podcasts-2020/podcasts-transcripts/0/A/show_*/*.json

Check the total number of transcripts files:
$find spotify-podcasts-2020/podcasts-transcripts/ -name '*.json' |wc -l
105360

RSS Headers
-----------
The single tar file containing xml files for 18,376 distinct podcast shows untars to the directory with the subdirectories:
spotify-podcasts-2020/show-rss/0/A/show_*.xml

Check the total number of RSS header files:
$find spotify-podcasts-2020/show-rss/ -name '*.xml' |wc -l
 18376

Metadata
--------
There is a metadada.tsv for preview and a duplicate copy as a single tar file metadata.tar.gz which will untar into:
spotify-podcasts-2020/metadata.tsv

Fields and explanations in metadata.tsv :
- show_uri :  Spotify uri for the show. e.g. spotify:show:7gozmLqbcbr6PScMjc0Zl4
- show_name :  Name of the show. e.g. Reply All
- show_description : Description of the show. e.g. "'A podcast about the internet' that is actual…”
- publisher : Publisher of the show. e.g. Gimlet
- language : Language the show is in in BCP 47 format. e.g. [en]
- rss_link: links of show rss feed. e.g. https://feeds.megaphone.fm/replyall
- episode_uri : Spotify uri for the episode. e.g. spotify:episode:4vYOibPeC270jJlnRoAVO6
- episode_name : Name of the episode. e.g. #109 Is Facebook Spying on You?
- episode_description :	Description of the episode. e.g. “This year we’ve gotten one question more than …”
- duration : duration of the episode in minutes. e.g. 31.680000
- show_filename_prefix: Filename_prefix of the show. e.g. show_7gozmLqbcbr6PScMjc0Zl4
- episode_filename_prefix: Filename_prefix of the episode. e.g. 4vYOibPeC270jJlnRoAVO6

Scripts
-------
A single tar file scripts.tar.gz containing helper scripts and files untars into:
spotify-podcasts-2020/scripts/. Please refer to section "Retraction of episodes".

Summarization Test Set
----------------------
There is also a tar file of test episodes for summarization 
spotify-podcasts-2020-summarization-testset.tar.gz  (147MB, 1027 episodes)
It contains metadata, transcripts and RSS headers in the same format as above.


Dataset description (unpacked)
===================

README 		this README

metadata.tsv	the metadata associated with each podcast episode - one line per episode

show-rss/ 			RSS headers made by podcast show creators in XML format. One RSS header file per show, named using show_filename_prefix, Spotify URI for the show, given in metadata.tsv. Each show contains multiple episodes. Not all episodes in the RSS headers are included in the dataset.

podcasts-transcripts/	transcripts consist of JSON format files, one per podcast episode. Each transcript is named using the episode_filename_prefix given in metadata.tsv. 

podcasts-audio/ 	an OGG format audio file per podcast episode. Each OGG file is named using the episode_filename_prefix given in metadata.tsv. 

scripts/ 		contains utility scripts
compliance.py - a deletion script which MUST be run before using the data. 

trec2020podcastsTrackGuidelines.txt	Task Guidelines for TREC2020 podcasts challenge


Directory structure (unpacked)
===================

The data set is organized into subdirectories under the transcripts and audio directories by the first two characters of the show-id to avoid overwhelming filesystem operations. The show-ids and the episode-ids are alphanumeric character sequences of length 22. Since some operating systems do not distinguish between upper and lower case, the subdirectory paths are all in upper case and include both upper and lower case show-ids in the same subdirectory. 

The default data structure is:
    $ spotify-podcasts-2020/podcasts-transcripts/0/A/show_*/*.json
    $ spotify-podcasts-2020/podcasts-audio/0/A/show_*/*.ogg
    $ spotify-podcasts-2020/show-rss/0/A/show_*.xml
    $ spotify-podcasts-2020/metadata.tsv 
    $ spotify-podcasts-2020/scripts/compliance.py
    $ spotify-podcasts-2020/scripts/delete_file.txt 

Retraction of episodes
======================
 
Occasionally some episodes may be retracted from the data set. When this happens, this will be communicated to all participants, and you are required to comply with the deletion. To facilitate this, a deletion script - compliance.py - has been provided in the scripts directory. If you retain the default directory structure as given above without renaming files, you can simply run the compliance script as per below and it will do the deletion for you; otherwise you will be responsible for deleting the requested items yourself.

Run the deletion script using:
`$ cd spotify-podcasts-2020/
 $ python3 scripts/compliance.py`

The file "delete_file.txt" has two columns which are show_filename_prefix and episode_filename_prefix.
It could be empty if nothing needs to be deleted. When delete requests are issued, we will update the delete_file.txt in the repository and ask you to download it. 
Example : 
        show_0F2zZNU9wzNSfAW1IJTjU2,2rPk0aN8NIArjJuJEqz8KL
        show_0F2zZNU9wzNSfAW1IJTjU2,5m0lPlDNjMeFjtukFBFpiC
        show_0f2P0fH4EwuEtXKpXIt7Ui,0BDVyuIPWhu8XoG5y9m7nF






