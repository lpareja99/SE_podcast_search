# Podcast search

## Table of Contents
- [Authors](#authors)
- [General Information of the project](#general-information-of-the-project)
- [Technical information and set-up](#technical-information-and-set-up)
- [Tasks](#tasks)
- [Others](#others)

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

### Set-up project (Windows)
TBD

### Set-up project (Mac)
TBD

## Tasks


## Others




