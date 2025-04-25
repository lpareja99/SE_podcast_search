import feedparser

rss_url = "https://anchor.fm/s/31cb3dc/podcast/rss"
feed = feedparser.parse(rss_url)

# Get the show-level image as fallback
default_image = None
if "itunes_image" in feed.feed:
    default_image = feed.feed["itunes_image"].get("href")
elif "image" in feed.feed and "href" in feed.feed["image"]:
    default_image = feed.feed["image"]["href"]

for entry in feed.entries:
    title = entry.get("title", "No Title")
    audio_url = entry.enclosures[0]["href"] if entry.enclosures else "No audio"

    # Try to get the episode-specific image
    episode_image = None
    if "itunes_image" in entry:
        episode_image = entry["itunes_image"].get("href")

    image_to_use = episode_image or default_image or "No image"

    print(f"Title: {title}")
    print(f"Audio URL: {audio_url}")
    print(f"Image URL: {image_to_use}\n")
