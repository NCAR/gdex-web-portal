#from django.test import TestCase
import requests

url = "https://gdex.ucar.edu/api/jira-payload/"
payload = {"message": "Hello Django!", "test": True}

response = requests.post(url, json=payload)
print(response.json())

