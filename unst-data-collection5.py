import io

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