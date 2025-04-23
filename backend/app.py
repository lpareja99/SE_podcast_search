from flask import Flask, request, jsonify
from config import get_es
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

es = get_es()
INDEX_NAME = "episodes"

@app.route('/')
def home():
    return "Backend is running!"  # Simple response to confirm backend is active

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
    
    result = es.search(index=INDEX_NAME, query=query)
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
    query = {}  # Initialize query to avoid UnboundLocalError
    match type:
        case "Intersection":
            query = {
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
            query = {
                "function_score": {
                    "query": {"match": {"episode_description": params["q"]}},
                    "boost_mode": "multiply",
                    "functions": [
                        {
                            "field_value_factor": {
                                "field": "ranking_score",
                                "factor": 1.2,
                                "modifier": "sqrt"
                            }
                        }
                    ]
                }
            }
        case _:
            raise ValueError(f"Unsupported query type: {type}")

    return query

if __name__ == "__main__":
    app.run(debug=True)
