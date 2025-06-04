import subprocess
import sys
import json
import time
import random
from pathlib import Path
from urllib.parse import urlparse

# Ensure `requests` is installed
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests


def find_keys_recursively(obj, target_key):
# Recursively find all values for a given key in nested JSON
    found = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == target_key:
                found.append(value)
            else:
                found.extend(find_keys_recursively(value, target_key))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(find_keys_recursively(item, target_key))
    return found


def fetch_json(url, filename, headers):
# Fetch JSON from a URL or load from file
    file_path = Path(filename)
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f), False  # False = not newly downloaded
    else:
        # Don't overwhelm server
        delay = random.uniform(4, 10)
        print(f"{filename} not found. Sleeping {delay:.2f}s before fetching...")
        time.sleep(delay)
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved data to {filename}")
            return data, True
        else:
            print(f"Failed {url} ({response.status_code})")
            return None, False


def parse_filename_from_url(url):
# Extract a filename from NHL JSON
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    return f"{parts[1]}_{parts[2]}" if len(parts) >= 3 else "unknown_file.json"

def main():
    # minimum headers to get Edge data
    headers = {
        'Referer': 'https://www.nhl.com/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15',
    }

    for gmnum in range(20001, 21313):
        pbp_url = f'https://api-web.nhle.com/v1/gamecenter/20240{gmnum}/play-by-play'
        game_id = f"20240{gmnum}"
        filename = f"pbp_{game_id}.json"

        data, _ = fetch_json(pbp_url, filename, headers)
        if not data:
            continue

        replay_urls = find_keys_recursively(data, "pptReplayUrl")
        print(f"{game_id}: Found {len(replay_urls)} replay URLs")

        for url in replay_urls:
            replay_filename = parse_filename_from_url(url)
            fetch_json(url, replay_filename, headers)

if __name__ == "__main__":
    main()
