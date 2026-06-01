"""
upload_to_drive.py
────────────────────────────────────────────────────────────────
Uploads rvlcdip_sample/ folder to Google Drive.
Creates one sub-folder per class inside your Drive folder.

Usage:
    python upload_to_drive.py
"""

import os
import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from tqdm import tqdm

# ─── Config ──────────────────────────────────────────────────
SAMPLE_DIR      = Path("rvlcdip_sample")
DRIVE_FOLDER_ID = "16wXgLuuWlPhEq7Lb_VpK6CVEXJhGQ3yc"
SCOPES          = ["https://www.googleapis.com/auth/drive"]
TOKEN_FILE      = "token.json"
CREDS_FILE      = "credentials.json"

# ─── Authenticate ────────────────────────────────────────────
def authenticate():
    creds = None
    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

# ─── Helper: create Drive folder ─────────────────────────────
def create_drive_folder(service, name, parent_id):
    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]

# ─── Helper: upload one file ─────────────────────────────────
def upload_file(service, local_path, parent_id):
    meta = {"name": local_path.name, "parents": [parent_id]}
    media = MediaFileUpload(str(local_path), mimetype="image/jpeg", resumable=False)
    service.files().create(body=meta, media_body=media, fields="id").execute()

# ─── Main ────────────────────────────────────────────────────
print("=" * 60)
print("  Uploading rvlcdip_sample/ to Google Drive")
print(f"  Drive folder ID: {DRIVE_FOLDER_ID}")
print("=" * 60)

print("\n[1/2] Authenticating with Google Drive...")
print("      A browser window will open — sign in and allow access.\n")
service = authenticate()
print("      Authenticated!")

# Count total files
all_images = list(SAMPLE_DIR.glob("**/*.jpg"))
print(f"\n[2/2] Uploading {len(all_images):,} images...\n")

class_dirs = sorted([d for d in SAMPLE_DIR.iterdir() if d.is_dir()])
total_uploaded = 0

for class_dir in class_dirs:
    class_name = class_dir.name
    images = sorted(class_dir.glob("*.jpg"))

    # Create sub-folder on Drive
    drive_subfolder_id = create_drive_folder(service, class_name, DRIVE_FOLDER_ID)

    # Upload images
    for img_path in tqdm(images, desc=f"  {class_name:<20}", leave=True):
        upload_file(service, img_path, drive_subfolder_id)
        total_uploaded += 1

print(f"\n{'=' * 60}")
print(f"  DONE! Uploaded {total_uploaded:,} images to Google Drive.")
print(f"  Check your Drive folder:")
print(f"  https://drive.google.com/drive/folders/{DRIVE_FOLDER_ID}")
print("=" * 60)