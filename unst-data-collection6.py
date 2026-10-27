import io
import re

import pandas as pd
import pymupdf
import pytesseract
from PIL import Image, ImageOps, ImageEnhance, ImageFilter


# Set the Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# Open the PDF file
doc = pymupdf.open("주간_매출보고서.pdf")


for page_number, page in enumerate(doc):

    # Convert the PDF page to a high-resolution image
    pix = page.get_pixmap(dpi=400)

    image = Image.open(
        io.BytesIO(pix.tobytes("png"))
    )

    # Convert to grayscale
    image = ImageOps.grayscale(image)

    # Increase contrast
    image = ImageEnhance.Contrast(image).enhance(2.0)

    # Sharpen the image
    image = image.filter(ImageFilter.SHARPEN)

    # Convert to a binary black-and-white image
    image = image.point(
        lambda x: 0 if x < 170 else 255
    )

    # Extract text using OCR
    text = pytesseract.image_to_string(
        image,
        lang="kor+eng",
        config="--oem 3 --psm 4"
    )

    print(f"\n===== PAGE {page_number + 1} =====")
    print(text)


# Store extracted sales records
rows = []


# Match a sales record:
# Company / Date / Time / Sales amount / Quantity / Location
#
# "원" and "개" are retained because they appear in the source PDF.
pattern = re.compile(
    r"(.+?)\s+"
    r"(\d{4}-\d{2}-\d{2})\s+"
    r"(\d{2}:\d{2})\s+"
    r"([\d,]+)원\s+"
    r"(\d+)개\s+"
    r"(.+)"
)


for line in text.splitlines():

    line = line.strip()

    if not line:
        continue

    match = pattern.match(line)

    if match:

        company = match.group(1)
        date = match.group(2)
        time = match.group(3)
        sales = match.group(4)
        quantity = match.group(5)
        location = match.group(6)

        rows.append({
            "Customer Company": company,
            "Date": date,
            "Time": time,
            "Sales Amount": int(sales.replace(",", "")),
            "Sales Quantity": int(quantity),
            "Customer Location": location
        })


# Create and display the DataFrame
df = pd.DataFrame(rows)

print(df)