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
    query = request.args.get("q", "")
    result = es.search(index=INDEX_NAME, query={"match": {"episode_description": query}})
    hits = [
        {
            "title": hit["_source"]["episode_title"],
            "description": hit["_source"]["episode_description"],
            "show": hit["_source"]["show_name"]
        }
        for hit in result["hits"]["hits"]
    ]
    return jsonify(hits)

if __name__ == "__main__":
    app.run(debug=True)
