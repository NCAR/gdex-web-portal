#from django.test import TestCase
import requests

url = "https://calie.k8s.ucar.edu/api/jira-event/"
payload = {"issue_key": "TEST-123", "summary": "Test issue"}

response = requests.post(url, json=payload)
print(response.status_code)
print(response.json())

