import pymupdf
import pytesseract
from PIL import Image
import io

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

doc = pymupdf.open("주간_매출보고서.pdf")

text = ""

for page in doc:
    pix = page.get_pixmap(dpi=300)

    image = Image.open(
        io.BytesIO(pix.tobytes("png"))
    )

    page_text = pytesseract.image_to_string(
        image,
        lang="kor+eng"
    )

    text += page_text

print(text)