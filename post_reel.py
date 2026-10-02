import os
import sys
import time
import requests

GRAPH = "https://graph.facebook.com/v21.0"

IG_USER_ID = os.environ.get("IG_USER_ID") or "17841417729755083"
TOKEN = os.environ["ACCESS_TOKEN"]
VIDEO_URL = os.environ["VIDEO_URL"]
COVER_URL = os.environ.get("COVER_URL", "")
CAPTION = os.environ.get("CAPTION", "")


def check(r):
    try:
        data = r.json()
    except Exception:
        print("Bad response:", r.text)
        sys.exit(1)
    if "error" in data:
        print("API error:", data["error"])
        sys.exit(1)
    return data


def main():
    # Step 1: create the reel container
    payload = {
        "media_type": "REELS",
        "video_url": VIDEO_URL,
        "caption": CAPTION,
        "share_to_feed": "true",
        "access_token": TOKEN,
    }
    if COVER_URL:
        payload["cover_url"] = COVER_URL

    data = check(requests.post(f"{GRAPH}/{IG_USER_ID}/media", data=payload, timeout=60))
    creation_id = data["id"]
    print("Container created:", creation_id)

    # Step 2: wait until Instagram finishes processing the video
    for _ in range(40):  # up to ~10 minutes
        time.sleep(15)
        s = check(requests.get(
            f"{GRAPH}/{creation_id}",
            params={"fields": "status_code,status", "access_token": TOKEN},
            timeout=60,
        ))
        code = s.get("status_code")
        print("Status:", code)
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            print("Processing failed:", s)
            sys.exit(1)
    else:
        print("Timed out waiting for processing")
        sys.exit(1)

    # Step 3: publish
    pub = check(requests.post(
        f"{GRAPH}/{IG_USER_ID}/media_publish",
        data={"creation_id": creation_id, "access_token": TOKEN},
        timeout=60,
    ))
    print("Published! Media ID:", pub["id"])


if __name__ == "__main__":
    main()
