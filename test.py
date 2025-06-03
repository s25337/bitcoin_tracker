import requests

txid = "52a3ea879f949c4a2e39479e57e7d5023efada1bf0bb5a846f471bd962fbcf02"
url = f"http://127.0.0.1:5000/trace/{txid}"
url2 = f"http://127.0.0.1:5000/trace-inputs/{txid}"
response = requests.get(url)
print("Status:", response.status_code)
print("Odpowiedź:", response.json())


response = requests.get(url2)
print("Status:", response.status_code)
print("Odpowiedź:", response.json())