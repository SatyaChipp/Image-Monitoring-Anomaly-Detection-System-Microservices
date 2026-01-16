import os
import time
import requests
import redis
from pathlib import Path
from PIL import Image
import imagehash

# Environment configuration
UPLOAD_SERVICE_URL = os.getenv("UPLOAD_SERVICE_URL", "http://upload_service:5000")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.9))

# Initialize Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Define folders
folders = [f"folder{i}" for i in range(1, 7)]
DOWNLOAD_ROOT = "downloaded_images"
CCTV_INPUTS_ROOT = "cctv_inputs"

# Ensure folders exist
Path(DOWNLOAD_ROOT).mkdir(exist_ok=True)
Path(CCTV_INPUTS_ROOT).mkdir(exist_ok=True)
for folder in folders:
    Path(os.path.join(DOWNLOAD_ROOT, folder)).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(CCTV_INPUTS_ROOT, folder)).mkdir(parents=True, exist_ok=True)

def get_latest_file(folder_path):
    """Return path to latest file in a folder (or None if empty)."""
    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
             if os.path.isfile(os.path.join(folder_path, f))]
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def compare_images(img1_path, img2_path):
    """Compute perceptual hash similarity between two images."""
    try:
        hash1 = imagehash.phash(Image.open(img1_path))
        hash2 = imagehash.phash(Image.open(img2_path))
        max_diff = len(hash1.hash) ** 2
        diff = hash1 - hash2
        return 1 - (diff / max_diff)
    except Exception as e:
        print(f"⚠️ Error comparing images: {e}")
        return None

def fetch_and_compare():
    print("\n🔍 Checking for updates...")
    for folder in folders:
        try:
            # Step 1. Get latest upload image from Flask
            resp = requests.get(f"{UPLOAD_SERVICE_URL}/latest/{folder}")
            if resp.status_code != 200:
                print(f"⚠️ {folder}: No image uploaded yet.")
                continue

            data = resp.json()
            image_path = data['latest_image']
            relative_path = image_path.replace("uploads/", "")
            image_url = f"{UPLOAD_SERVICE_URL}/uploads/{relative_path}"

            # Step 2. Download image
            image_data = requests.get(image_url)
            if image_data.status_code != 200:
                print(f"⚠️ {folder}: Failed to download uploaded image.")
                continue

            filename = os.path.basename(image_path)
            save_path = os.path.join(DOWNLOAD_ROOT, folder, filename)
            with open(save_path, "wb") as f:
                f.write(image_data.content)

            # Step 3. Find latest CCTV image
            cctv_folder = os.path.join(CCTV_INPUTS_ROOT, folder)
            latest_cctv = get_latest_file(cctv_folder)
            if not latest_cctv:
                print(f"📁 {folder}: No CCTV image found, skipping.")
                continue

            # Step 4. Compare both
            similarity = compare_images(save_path, latest_cctv)
            if similarity is None:
                continue

            print(f"📸 {folder}: Similarity = {similarity:.2f}")
            redis_client.set(f"similarity_{folder}", similarity)

            if similarity < SIMILARITY_THRESHOLD:
                alert_msg = f"🚨 ALERT: {folder} differs from CCTV input! ({similarity:.2f})"
                print(alert_msg)
                redis_client.set(f"alert_{folder}", alert_msg)
            else:
                print(f"✅ {folder}: Images match within threshold.")
                redis_client.delete(f"alert_{folder}")

        except Exception as e:
            print(f"❌ Error processing {folder}: {e}")

if __name__ == "__main__":
    while True:
        fetch_and_compare()
        time.sleep(30)

# Retrieves the latest uploaded image from each Flask upload folder (via REST).
#
# Retrieves the latest CCTV input image (from a separate folder that simulates your camera feed).
#
# Compares both images for each folder using perceptual hashing (phash).
#
# Raises an alert (console + Redis flag) if they differ beyond a similarity threshold.