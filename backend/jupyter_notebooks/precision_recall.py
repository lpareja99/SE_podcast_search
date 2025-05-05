import csv
import math
from collections import defaultdict

def compute_dcg(scores, k):
    """Compute DCG given a ranked list of (doc_id, relevance_score) tuples."""
    dcg = 0.0
    for i, (_, rel) in enumerate(scores[:k]):
        dcg += (rel) / math.log2(i + 2)
    return dcg



def compute_metrics(file_path, threshold=0.5, k=10):
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)
        rows = list(reader)

    meta_cols = 4  # number of non-score metadata columns
    metric_cols = header[meta_cols:]

    precision_scores = {}
    recall_scores = {}
    ndcg_scores = {}

    total_relevant = 100  # you can adapt this based on ground truth

    for i, col in enumerate(metric_cols):
        retrieved = 0
        relevant_retrieved = 0
        relevance_list = []

        for row in rows:
            doc_id = row[3]  # episode_id
            score = float(row[meta_cols + i])
            relevance = 1 if score >= threshold else 0

            retrieved += 1
            if relevance == 1:
                relevant_retrieved += 1

            # For nDCG, we treat score as the relevance score directly
            relevance_list.append((doc_id, score))

        precision = relevant_retrieved / retrieved if retrieved else 0
        recall = relevant_retrieved / total_relevant if total_relevant else 0
        dcg = compute_dcg(relevance_list, k)
        ideal_list = sorted(relevance_list, key=lambda x: x[1], reverse=True)
        ideal_dcg = compute_dcg(ideal_list, k)
        ndcg = dcg / ideal_dcg if ideal_dcg > 0 else 0
        precision_scores[col] = precision
        recall_scores[col] = recall
        ndcg_scores[col] = round(ndcg, 4)

    print("\n=== Precision ===")
    for col, val in precision_scores.items():
        print(f"{col}: {val:.4f}")
    print(precision_scores.values())

    print("\n=== Recall ===")
    for col, val in recall_scores.items():
        print(f"{col}: {val:.4f}")
    print(recall_scores.values())

    print(f"\n=== nDCG@{k} ===")
    for col, val in ndcg_scores.items():
        print(f"{col}: {val:.4f}")
    print(ndcg_scores.values())

# Example usage
compute_metrics("phrase_nice_morning.txt", threshold=0.5, k=10)
