import io

import pandas as pd
import pymupdf
import pytesseract
from PIL import Image, ImageOps, ImageEnhance, ImageFilter


# ---------------------------------------------------------
# 1. Set the Tesseract executable path
# ---------------------------------------------------------

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# ---------------------------------------------------------
# 2. Open the PDF file
# ---------------------------------------------------------

# Keep this name if the actual PDF file has a Korean filename.
PDF_FILE = "주간_매출보고서.pdf"

doc = pymupdf.open(PDF_FILE)

# Store OCR data from all pages
all_ocr_data = []


# ---------------------------------------------------------
# 3. PDF → Image → Preprocessing → OCR
# ---------------------------------------------------------

for page_number, page in enumerate(doc):

    print()
    print("========================================")
    print(f"Processing PAGE {page_number + 1}")
    print("========================================")

    # -----------------------------------------------------
    # Convert the PDF page to a high-resolution image
    # -----------------------------------------------------

    pix = page.get_pixmap(dpi=400)

    image = Image.open(
        io.BytesIO(
            pix.tobytes("png")
        )
    )

    # -----------------------------------------------------
    # Image preprocessing
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Perform OCR
    # -----------------------------------------------------

    ocr_data = pytesseract.image_to_data(
        image,
        lang="kor+eng",
        config="--oem 3 --psm 4",
        output_type=pytesseract.Output.DATAFRAME
    )

    # Add the PDF page number
    ocr_data["pdf_page"] = page_number + 1

    # -----------------------------------------------------
    # Clean the OCR results
    # -----------------------------------------------------

    ocr_data = ocr_data[
        ocr_data["text"].notna()
    ]

    ocr_data["text"] = (
        ocr_data["text"]
        .astype(str)
        .str.strip()
    )

    ocr_data = ocr_data[
        ocr_data["text"] != ""
    ]

    # Remove words with very low confidence
    ocr_data = ocr_data[
        ocr_data["conf"] >= 30
    ]

    all_ocr_data.append(ocr_data)


# ---------------------------------------------------------
# 4. Combine OCR results from all pages
# ---------------------------------------------------------

ocr_df = pd.concat(
    all_ocr_data,
    ignore_index=True
)

print()
print("Sample OCR results")
print()

print(
    ocr_df[
        [
            "pdf_page",
            "text",
            "left",
            "top",
            "width",
            "height",
            "conf"
        ]
    ].head(30)
)


# ---------------------------------------------------------
# 5. Save the raw OCR results
# ---------------------------------------------------------

ocr_df.to_csv(
    "ocr_raw_data.csv",
    index=False,
    encoding="utf-8-sig"
)


# ---------------------------------------------------------
# 6. Combine OCR words on the same line
# ---------------------------------------------------------

line_df = (
    ocr_df
    .sort_values(
        [
            "pdf_page",
            "block_num",
            "par_num",
            "line_num",
            "left"
        ]
    )
    .groupby(
        [
            "pdf_page",
            "block_num",
            "par_num",
            "line_num"
        ],
        as_index=False
    )
    .agg(
        text=(
            "text",
            lambda x: " ".join(x.astype(str))
        ),
        left=(
            "left",
            "min"
        ),
        top=(
            "top",
            "min"
        ),
        right=(
            "left",
            lambda x: x.max()
        )
    )
)

print()
print("OCR results grouped by line")
print()

print(line_df.head(30))


# ---------------------------------------------------------
# 7. Select the table area
# ---------------------------------------------------------
#
# Adjust the coordinates after checking the OCR output.
#
# Example:
# Assume the customer sales table is located between
# top coordinates 1100 and 2600.
# ---------------------------------------------------------

table_words = ocr_df[
    (ocr_df["top"] >= 1100)
    &
    (ocr_df["top"] <= 2600)
].copy()


# ---------------------------------------------------------
# 8. Classify columns using X coordinates
# ---------------------------------------------------------
#
# These are example coordinates for 400 DPI.
#
# Check the following output and adjust the values
# for your actual PDF:
#
# ocr_df[["text", "left", "top"]]
# ---------------------------------------------------------

def classify_column(x):

    if x < 550:
        return "Customer Company"

    elif x < 1250:
        return "Sales Date and Time"

    elif x < 1750:
        return "Sales Amount"

    elif x < 2150:
        return "Sales Quantity"

    else:
        return "Customer Location"


table_words["column"] = (
    table_words["left"]
    .apply(classify_column)
)


# ---------------------------------------------------------
# 9. Group words with similar Y coordinates into rows
# ---------------------------------------------------------
#
# OCR words in the same table row may have slightly
# different top coordinates.
#
# For example:
# 1332
# 1335
# 1338
#
# Group them using a fixed row height.
# ---------------------------------------------------------

ROW_HEIGHT = 70

table_words["row_group"] = (
    (table_words["top"] / ROW_HEIGHT)
    .round()
    .astype(int)
)


# ---------------------------------------------------------
# 10. Combine text by row and column
# ---------------------------------------------------------

table_cells = (
    table_words
    .sort_values(
        [
            "row_group",
            "left"
        ]
    )
    .groupby(
        [
            "row_group",
            "column"
        ]
    )["text"]
    .apply(
        lambda x: " ".join(x.astype(str))
    )
    .reset_index()
)


# ---------------------------------------------------------
# 11. Reconstruct the table using pivot
# ---------------------------------------------------------

sales_df = table_cells.pivot(
    index="row_group",
    columns="column",
    values="text"
).reset_index()

# Remove the row_group column
sales_df = sales_df.drop(
    columns=["row_group"]
)

# Set the desired column order
column_order = [
    "Customer Company",
    "Sales Date and Time",
    "Sales Amount",
    "Sales Quantity",
    "Customer Location"
]

sales_df = sales_df.reindex(
    columns=column_order
)


# ---------------------------------------------------------
# 12. Remove empty rows
# ---------------------------------------------------------

sales_df = sales_df.dropna(
    how="all"
)


# ---------------------------------------------------------
# 13. Post-process OCR results
# ---------------------------------------------------------

for column in sales_df.columns:

    sales_df[column] = (
        sales_df[column]
        .fillna("")
        .astype(str)
        .str.strip()
    )


# ---------------------------------------------------------
# 14. Display the reconstructed table
# ---------------------------------------------------------

print()
print("========================================")
print("Reconstructed Sales DataFrame")
print("========================================")

print(
    sales_df.to_string(index=False)
)


# ---------------------------------------------------------
# 15. Save as CSV
# ---------------------------------------------------------

sales_df.to_csv(
    "weekly_sales.csv",
    index=False,
    encoding="utf-8-sig"
)


# ---------------------------------------------------------
# 16. Save as Excel
# ---------------------------------------------------------

sales_df.to_excel(
    "weekly_sales.xlsx",
    index=False
)

print()
print("CSV file saved: weekly_sales.csv")
print("Excel file saved: weekly_sales.xlsx")