from flask import Flask, request, jsonify
from config import get_es
from flask_cors import CORS
from queries.metadata import metadata
from queries.phrase import phrase_query

app = Flask(__name__)
CORS(app)

es = get_es()
EPISODES_INDEX = "episodes"
TRANSACRIPTS_INDEX = "podcast_transcripts"

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
    
    transcript_results = querySelector(params)
    
    print("results of trasncripts: " , transcript_results)
    
    metadata_results = metadata(transcript_results)
    
    return metadata_results



def querySelector(params):
    
    phrase_query(phrase=params["q"])
    type = params['type']
    result = [] 
    match type:
        case "Intersection":
            #result = intersection_query(phrase=params["q"])
            return 
        case "Phrase":
            result = phrase_query(phrase=params["q"])
        case "Ranking":
            """ result = {
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
            } """
            result = ''
        case _:
            raise ValueError(f"Unsupported query type: {type}")

    return result

if __name__ == "__main__":
    app.run(debug=True)
