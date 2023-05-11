# Download all solc versions from github

import json
import requests
import os
import stat
import requests

list_json_url = "https://raw.githubusercontent.com/ethereum/solc-bin/gh-pages/linux-amd64/list.json"

def make_executable(file_path):
    st = os.stat(file_path)
    os.chmod(file_path, st.st_mode | stat.S_IEXEC)


def download_github_file(url, output_file):
    response = requests.get(url)

    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded file: {output_file}")
    else:
        print(f"Error downloading file: {output_file}")


base_url = "https://raw.githubusercontent.com/ethereum/solc-bin/gh-pages/linux-amd64/{}"

folder = os.path.expanduser("~/.solcx/")
os.makedirs(folder, exist_ok=True)

# with open('solc.json', 'r') as f:
#     data = json.load(f)

resp = requests.get(list_json_url)
data = resp.json()

for build in data['builds']:
    version = build['version']
    path = build['path']
    download_url = base_url.format(path)
    solc_bin = os.path.join(folder, f"solc-v{version}")
    if os.path.exists(solc_bin):
        make_executable(solc_bin)
        continue

    response = requests.get(download_url)
    if response.status_code == 200:
        with open(solc_bin, "wb") as f:
            f.write(response.content)
        make_executable(solc_bin)
        print(f"Downloaded and saved {path} as v{version}")
    else:
        print(f"Error downloading {path} from {download_url}")
