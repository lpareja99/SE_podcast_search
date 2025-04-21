from flask import Flask, request, jsonify, render_template
from config import get_es
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

es = get_es()
INDEX_NAME = "episodes"

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/search')
def search():
    params = {
        "q": request.args.get("q", ""),
        "filter": request.args.get("filter", None),
        "type": request.args.get("type", None),
        "ranking": request.args.get("ranking", None),
        "time": request.args.get("time", None),
        "selectedEpisodes": request.args.get("selectedEpisodes", "").split(",") if request.args.get("selectedEpisodes") else []
    }
    query = querySelector(params)

    result = es.search(index=INDEX_NAME, query= query)
    hits = [
        {
            "title": hit["_source"]["episode_title"],
            "description": hit["_source"]["episode_description"],
            "show": hit["_source"]["show_name"]
        }
        for hit in result["hits"]["hits"]
    ]
    return jsonify(hits)

def querySelector(params):
    type = params['type']
    match type:
        case "Intersection":
            query = query = {
    "bool": {
        "must": [
            {
                "match": {
                    "episode_description": {
                        "query": params["q"],
                        "fuzziness": 1
                    }
                }
            }
        ]
    }
}
        case "Phrase":
            query = {"match_phrase": {"episode_description": params["q"]}}
        case "Ranking":
            pass

    return query
    
    # query1 = {"match": {"episode_description": params["q"]}}
    # query2 = {"match_phrase": {"episode_description": params["q"]}}
    # query3 = {"bool": {"must" : [{"match": {"episode_description": params["q"]}}]}}

if __name__ == "__main__":
    app.run(debug=True)
