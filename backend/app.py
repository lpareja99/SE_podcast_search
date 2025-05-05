from flask import Flask, json, jsonify, request
from config import get_es
from flask_cors import CORS
from queries.intersection import intersection_query
from queries.metadata import metadata
from queries.phrase import phrase_query
from queries.filter import search_episodes
from queries.bm25 import bm25_query

app = Flask(__name__)
CORS(app)

es = get_es()
EPISODES_INDEX = "episodes"
TRANSACRIPTS_INDEX = "podcast_transcripts"

@app.route('/')
def home():
    return "Backend is running!" 

@app.route('/search', methods=['POST'])
def search():
    
    try:
        params = request.get_json()
        result = querySelector(params)
        return result
    except Exception as e:
        print(f"Error during search: {e}")
        return jsonify({"error": str(e)}), 500


def querySelector(params):
    
    result = handleFilter(params)
    return result


def handleFilter(params):
  
    if (params["filter"] == "general"):
            transcript_result = handleType(params)
            metadata_results = metadata(transcript_result)
            
            joined_results = [
                {
                    "transcript": transcript,
                    "metadata": next(
                        (meta for meta in metadata_results if meta["show_id"] == transcript["show_id"] and meta["episode_id"] == transcript["episode_id"]),
                        {}
                    )
                }
                for transcript in transcript_result
            ]
            
            return joined_results  
    
    else:
        metadata_results = search_episodes(params['q'], params['filter'])
        
        joined_results = [
            {
                "transcript": {},
                "metadata": meta
            }
            for meta in metadata_results
        ]
        
        return joined_results


def handleType(params):
    match params['type']:
        case "Intersection":
            results = intersection_query(
                params["q"], 
                params["time"], 
                selected_episodes=params["selectedEpisodes"]
            )
            
        case "Phrase":
            results =  phrase_query(
                phrase=params["q"], 
                chunk_size=params['time'], 
                selected_episodes=params["selectedEpisodes"]
            )
        case "Ranking":
            results =  bm25_query(
                query_term=params["q"], 
                chunk_size= params["time"], 
                selected_episodes=params["selectedEpisodes"]
            )
        case _:
            raise ValueError(f"Unsupported query type: {params['type']}")
        
    return results

if __name__ == "__main__":
    app.run(debug=True)
