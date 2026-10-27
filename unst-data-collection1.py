import fitz

doc = fitz.open("report.pdf")

for page in doc:
    text = page.get_text()
    print(text)

