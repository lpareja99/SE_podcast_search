#!/usr/bin/env python3

import pandas as pd
import feedparser
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import tqdm

# === Configuración ===
METADATA_PATH = "../../podcasts-no-audio-13GB/metadata/spotify-podcasts-2020/metadata.tsv"
MAX_WORKERS = 10  # Número de hilos para procesamiento paralelo
OUTPUT_PATH = "final_podcast_table_all_with_unmatched.csv"

def load_metadata(path):
    df = pd.read_csv(path, delimiter="\t", encoding="utf-8")
    df["show_id"] = df["show_uri"].apply(lambda x: x.split(":")[-1])
    df["episode_id"] = df["episode_uri"].apply(lambda x: x.split(":")[-1])
    df["rss_link"] = df["rss_link"].astype(str).str.strip()
    df = df[[
        "episode_name", "episode_id", "show_name", "show_id",
        "rss_link", "language", "publisher", "episode_description", "duration"
    ]]
    return df

def process_rss_link(rss_url, metadata):
    try:
        response = requests.get(rss_url, timeout=5)
        if response.status_code != 200:
            return []

        feed = feedparser.parse(rss_url)
        rss_entries = {
            (entry.get("guid") or entry.get("id") or entry.get("link")): entry
            for entry in feed.entries if (entry.get("guid") or entry.get("id") or entry.get("link"))
        }

        show_image = ""
        if "itunes_image" in feed.feed:
            show_image = feed.feed["itunes_image"].get("href", "")
        elif "image" in feed.feed and "href" in feed.feed["image"]:
            show_image = feed.feed["image"]["href"]

        filtered_metadata = metadata[metadata["rss_link"] == rss_url].copy()
        filtered_metadata["image_show"] = show_image
        filtered_metadata["image_episode"] = ""
        filtered_metadata["audio_url"] = ""

        matched_episodes = []
        for idx, row in filtered_metadata.iterrows():
            metadata_title = row["episode_name"].strip().lower()
            matched_entry = None

            for guid, entry in rss_entries.items():
                rss_title = entry.get("title", "").strip().lower()
                if metadata_title == rss_title:
                    matched_entry = entry
                    break

            if matched_entry and matched_entry.enclosures:
                audio_url = matched_entry.enclosures[0].get("href", "")
                filtered_metadata.at[idx, "audio_url"] = audio_url
                filtered_metadata.at[idx, "image_episode"] = matched_entry.get("itunes_image", {}).get("href", show_image)
                matched_episodes.append(filtered_metadata.loc[idx])

        return matched_episodes

    except requests.exceptions.RequestException:
        return []

def main():
    print("Loading metadata...")
    metadata = load_metadata(METADATA_PATH)
    unique_rss_links = metadata["rss_link"].dropna().unique()

    episodes_with_audio = []

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_rss_link, url, metadata): url for url in unique_rss_links}
        for future in tqdm.tqdm(as_completed(futures), total=len(futures), desc="Processing RSS links"):
            try:
                episodes_with_audio.extend(future.result())
            except Exception:
                continue

    matched_ids = {ep["episode_id"] for ep in episodes_with_audio}
    unmatched = metadata[~metadata["episode_id"].isin(matched_ids)].copy()
    unmatched["image_show"] = ""
    unmatched["image_episode"] = ""
    unmatched["audio_url"] = ""

    df_with_audio = pd.DataFrame(episodes_with_audio)
    df_with_audio = pd.concat([df_with_audio, unmatched], ignore_index=True)

    total_checked = len(df_with_audio)
    print(f"Total entries checked: {total_checked}")
    print(f"Entries with audio: {len(df_with_audio) - len(unmatched)}")
    print(f"Unmatched entries: {len(unmatched)}")
    print(f"Time taken: {time.time() - start_time:.2f} seconds")

    df_with_audio.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved final table to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
