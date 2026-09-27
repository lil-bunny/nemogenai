import json
import os

# Path where Chrome stores all profile data
LOCAL_STATE_PATH = os.path.expandvars(
    r"%LOCALAPPDATA%\Google\Chrome\User Data\Local State"
)

if not os.path.exists(LOCAL_STATE_PATH):
    print("Chrome Local State file not found!")
    exit()

with open(LOCAL_STATE_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

profiles = data.get("profile", {}).get("info_cache", {})

print("\n==== Chrome Profiles Found ====\n")

for profile_id, details in profiles.items():
    print(f"Profile ID        : {profile_id}")
    print(f"Profile Name      : {details.get('name', 'Unknown')}")
    print(f"Email (if logged) : {details.get('user_name','No Email linked')}")
    print("-" * 40)
