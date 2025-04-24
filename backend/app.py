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
        "time": int(request.args.get("time", None)),
        "selectedEpisodes": request.args.get("selectedEpisodes", "").split(",") if request.args.get("selectedEpisodes") else []
    }
    
    result = querySelector(params)
       
    return result



def querySelector(params):
    
    result = handleFilter(params)

    return result


def handleFilter(params):
    match params['filter']:
        case "General":
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
        
        case "Title":
            return []
        case "Episode":
            return []
        case "Author":
            return []
        case _:
            raise ValueError(f"Unsupported filter type: {params['filter']}")


def handleType(params):
    match params['type']:
        case "Intersection":
            return []
        case "Phrase":
            return phrase_query(phrase=params["q"], chunk_size=params['time'])
        case "Ranking":
            return []
        case _:
            raise ValueError(f"Unsupported query type: {params['type']}")

if __name__ == "__main__":
    app.run(debug=True)
