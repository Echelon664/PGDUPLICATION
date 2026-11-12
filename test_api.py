import json
import urllib.request
import http.cookiejar

BASE_URL = "https://file.sandiegocounty.gov/HHSAPublicSite"
MODULE_VERSION = "zxF+S8oCjmRatPW60zkGuw"
CSRF_TOKEN = "T6C+9iB49TLra4jEsMeSckDMNhQ="

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Initialize session
req = urllib.request.Request(
    f"{BASE_URL}/moduleservices/roles",
    headers={
        "Accept": "application/json",
        "OutSystems-Client-Env": "browser",
        "X-CSRFToken": CSRF_TOKEN
    }
)
opener.open(req)

def get_first_level_folders(folder_id):
    payload = {
        "versionInfo": {
            "moduleVersion": MODULE_VERSION,
            "apiVersion": "Z7kXx_Ng5kxUrOB40OrtOg"
        },
        "viewName": "MainFlow.Section",
        "screenData": {
            "variables": {
                "folderIdIn": str(folder_id)
            }
        },
        "inputParameters": {
            "StartIndex": 0,
            "MaxRecords": 100
        }
    }
    api_url = f"{BASE_URL}/screenservices/HHSAPublicSite/MainFlow/Section_FirstLevel/ScreenDataSetGetById_Folder"
    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json",
            "OutSystems-Client-Env": "browser",
            "X-CSRFToken": CSRF_TOKEN
        }
    )
    with opener.open(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("data", {}).get("List", {}).get("List", [])

print("--- CalFresh (Folder 542) First Level Folders ---")
folders = get_first_level_folders(542)
print(f"Found {len(folders)} folders:")
for f in folders[:10]:
    folder_info = f.get("Folder", {})
    print(f"  ID: {folder_info.get('Id')} | Chapter: {folder_info.get('ChapterId')} | Name: {folder_info.get('Name')}")
