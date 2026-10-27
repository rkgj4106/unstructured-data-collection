import pymupdf

doc = pymupdf.open("주간_매출보고서.pdf")

text = ""

for page in doc:
    text += page.get_text()

print(text)


