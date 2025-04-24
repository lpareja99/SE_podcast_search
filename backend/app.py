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
    filter = params['filter']

    # Handle filter logic
    result = handleFilter(params)

    return result


def handleFilter(params):
    match params['filter']:
        case "General":
            transcript_result = handleType(params)
            print(transcript_result)
            metadata_results = metadata(transcript_result)
             # TODO: return both results to be able to show both things
            return metadata_results 
        case "Title":
            # Add logic for Title filter
            return []
        case "Episode":
            # Add logic for Episode filter
            return []
        case "Author":
            # Add logic for Author filter
            return []
        case _:
            raise ValueError(f"Unsupported filter type: {filter}")


def handleType(params):
    match params['type']:
        case "Intersection":
            # Add logic for Intersection type
            return []
        case "Phrase":
            print("time: ",params['time'])
            return phrase_query(phrase=params["q"], chunk_size=params['time'])
        case "Ranking":
            # Add logic for Ranking type
            return []
        case _:
            raise ValueError(f"Unsupported query type: {params['type']}")

if __name__ == "__main__":
    app.run(debug=True)
