# filepath: /home/lpa/master/search_engines/SE_podcast_search/backend/performance_test.py
import requests
import time
from itertools import product
import pandas as pd

API_URL = "http://127.0.0.1:5000/search"

# No misspellings
#q = ["morning", "terror", "change", "tomorrwow", "politics"]
#q = ["nice morning", "terror movie", "climate change", "blue sky", "tricky matter"]
#q = ["really nice morning", "new scary movie", "climate change is real", "blue sky is nice", "tricky matter to solve"]

# Misspellings
#q = ["mornng", "teror", "chnage", "tomorrwow", "politcs"]
#q = ["nice mornng", "teror movie", "climate chnge", "blue skyy", "tricky mater"]
q = ["really nice mornng", "new scary moovie", "climate chnge is real", "blue skyy is nice", "tricky mater to solve"]


types = ["Phrase", "Intersection", "Ranking"]
times = [30, 60, 120, 180, 300]
filters = ["general"]
selected_episodes = [[]]

parameter_combinations = list(product(q, types, times, filters, selected_episodes))

results = []

# Run each combination
for combination in parameter_combinations:
    query, query_type, time_chunk, filter_type, episodes = combination
    payload = {
        "q": query,
        "type": query_type,
        "time": time_chunk,
        "filter": filter_type,
        "selectedEpisodes": episodes
    }

    start_time = time.time()
    response = requests.post(API_URL, json=payload)
    end_time = time.time()

    latency = (end_time - start_time) * 1000  # Convert to milliseconds
    result_count = len(response.json()) if response.status_code == 200 else 0

    results.append({
        "query": query,
        "type": query_type,
        "time": time_chunk,
        "filter": filter_type,
        "latency_ms": latency,
        "result_count": result_count,
        "status_code": response.status_code
    })

df = pd.DataFrame(results)

average_latency = df.groupby(['type'])['latency_ms'].mean().reset_index()


print(df)

print(average_latency)