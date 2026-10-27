import pymupdf

doc = pymupdf.open("order-1004.pdf")

text = ""

for page in doc:
    text += page.get_text()

#print(text)
import requests
prompt = f"""
다음 주문서에서 정보를 추출하세요.
{text}
다음 JSON 형식으로 반환하세요.
{{
    "order_id": "",
    "customer": "",
    "product": "",
    "quantity": 0,
    "amount": 0
}}
"""
response = requests.post(
    "http://localhost:11435/api/generate",
    json={
        "model": "gemma3:12b",
        "prompt": prompt,
        "stream": False
    }
)
print(response.json()["response"])

#print("status:", response.status_code)
#print("body:", response.text)

#response.raise_for_status()

#data = response.json()
#print(data["response"])

