import requests

RPC_URL = "http://127.0.0.1:18332/"
RPC_USER = "mojuser"
RPC_PASS = "mojehaslo"

def rpc(method, params=[]):
    payload = {"jsonrpc": "1.0", "id": "python", "method": method, "params": params}
    response = requests.post(RPC_URL, json=payload, auth=(RPC_USER, RPC_PASS))
    return response.json()

print(rpc("getblockchaininfo"))
