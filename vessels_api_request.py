import json
import requests

URL = "https://api.staging.maritime.spire.sh/graphql"

HEADERS = {
    "Content-Type": "application/json",
    "accept": "application/json, multipart/mixed",
    "accept-language": "en-US,en;q=0.9",
    "authorization": "Bearer LRfGCIsI2OUgOGdIT6RgAzKYbFHsEzjT",
    "cookie": "_ga=GA1.2.1949726677.1730202226; ajs_anonymous_id=15be5ed9-94e5-4caa-8813-7d6f0e370db6; _ga_YNTPL5KGYB=GS1.2.1731594021.8.1.1731594122.0.0.0",
    "origin": "https://api.staging.maritime.spire.sh",
    "priority": "u=1, i",
    "referer": "https://api.staging.maritime.spire.sh/graphql",
    "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}


def vessels_api_request(query):

    # Convert to JSON
    raw_query = query.strip()
    payload = {
        "query": raw_query
    }
    payload = json.dumps(payload)

    # Perform the API request
    response = requests.request("POST", URL, data=payload, headers=HEADERS)
    return response.text
