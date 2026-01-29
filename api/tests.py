#from django.test import TestCase
import requests

url = "https://calie.k8s.ucar.edu/api/jira-payload/"
payload = {"key": "DATAHELP-5597", "test": True}

response = requests.post(url, json=payload)

print("Status code:", response.status_code)
print("Response text:", response.text)

# Only parse JSON if response is JSON
try:
    print("JSON response:", response.json())
except Exception as e:
    print("Error parsing JSON:", e)
