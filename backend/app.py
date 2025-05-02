from flask import Flask, request
from config import get_es
from flask_cors import CORS
from queries.intersection import intersection_query
from queries.metadata import metadata
from queries.phrase import phrase_query
from queries.filter import search_episodes

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
        "time": int(request.args.get("time", None)),
        "selectedEpisodes": request.args.get("selectedEpisodes", "").split(",") if request.args.get("selectedEpisodes") else []
    }
    
    result = querySelector(params)
       
    return result



def querySelector(params):
    
    result = handleFilter(params)

    return result


def handleFilter(params):
  
    """ if params.get("selectedEpisodes"):
        print("Performing 'More Like This' query for selected episodes:", params["selectedEpisodes"])
        #more_like_this_results = more_like_this_query(params["selectedEpisodes"])
        more_like_this_results = {}
        
        joined_results = [
            {
                "transcript": {},
                "metadata": meta
            }
            for meta in more_like_this_results
        ]
        return joined_results """
  
  
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
        print("filters: ", params)
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
            return intersection_query(
                params["q"], 
                params["time"], 
                selected_episodes=params["selectedEpisodes"]
            )
        case "Phrase":
            return phrase_query(
                phrase=params["q"], 
                chunk_size=params['time'], 
                selected_episodes=params["selectedEpisodes"]
            )
        case "Ranking":
            return []
        case _:
            raise ValueError(f"Unsupported query type: {params['type']}")

if __name__ == "__main__":
    app.run(debug=True)
