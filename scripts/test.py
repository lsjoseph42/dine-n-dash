from google import genai
from google.genai import types
import monsterui
import fasthtml
from itsdangerous import URLSafeSerializer
import json

def parse_receipt(image_path):
    client = genai.Client()

    with open(image_path, 'rb') as f:
      image_bytes = f.read()

    prompt = """Itemize the provided receipt in JSON where the key is the name of the item
                and the value is the price. If the same item has multiple entries, divide the
                price by the number of orders, and create separate keys for each individual item.
                (Ex. Milkshake x 3 = 9.00 becomes {milkshake_1: 3.00, milkshake_2: 3.00, milkshake_3: 3.00}).
                Also include the keys "tap", "tip", "total", and "other", where other is the sum of additional fees
                such as service fees that are not otherwise already accounted.
                Return only the JSON."""    
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
        types.Part.from_bytes(
            data=image_bytes,
            mime_type='image/jpeg',
        ),
        prompt
        ]
    )
    raw = response.text
    clean = raw.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean)

    return data

def calculate_split(selected_items: list, receipt_dict: dict, number_in_party: int):
    selected_cost = [receipt_dict[item] for item in selected_items if item in receipt_dict.keys()]
    tax = receipt_dict.get('tax')
    tip = receipt_dict.get('tip')
    other = receipt_dict.get('other')

    for fee in [tax, tip, other]:
        if fee:
            total_fees += (fee / number_in_party)

    return sum(selected_cost) + total_fees

def main(image_path):
    receipt_dict = parse_receipt(image_path)
    generate_signed_qr_code(receipt_dict)

def generate_signed_qr_code(receipt_dict: dict):
    auth_s = URLSafeSerializer("secret key", "auth")
    token = auth_s.dumps(receipt_dict)

    print(f"Receipt token: {token}")

def read_signed_url(url: str):
    # TODO: Parse URL and dict from server
    pass

if __name__ == "__main__":
    image_path = "data/IMG_6756.jpg"
    main(image_path)