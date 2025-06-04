import json

with open("known_addresses.json") as f:
    KNOWN_ADDRESSES = {}
    for exchange, addresses in json.load(f).items():
        for addr in addresses:
            KNOWN_ADDRESSES[addr] = exchange

def calculate_suspicion_score(tx_data):
    reasons = []
    score = 0

    num_inputs = len(tx_data.get("vin", []))
    num_outputs = len(tx_data.get("vout", []))

    if num_inputs > 10:
        score += 25
        reasons.append("Dużo wejść (powyżej 10)")

    if num_outputs > 10:
        score += 25
        reasons.append("Dużo wyjść (powyżej 10)")

    for out in tx_data.get("vout", []):
        value = out.get("value", 0)
        address = out.get("scriptpubkey_address", "")

        if value < 1000:
            score += 10
            reasons.append("Bardzo małe wyjście (dust output)")

        if address in KNOWN_ADDRESSES:
            score += 30
            reasons.append(f"Adres powiązany z giełdą: {KNOWN_ADDRESSES[address]}")

    return min(score, 100), reasons
