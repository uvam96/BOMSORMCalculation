# SO Raw Material Requirement (Streamlit)

Upload the SAP ByD **Sales Order report** and one or more **BOM reports** (FG and SFG).
The app explodes each SO line through the FG BOM, then through every SFG BOM found
in the uploads (any depth), and totals the raw material requirement.

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Community Cloud)
1. Push this folder to a GitHub repo.
2. share.streamlit.io → New app → pick the repo, main file `app.py`.

## Expected report columns
- **Sales Order report**: Sales Order, Product (+ ID column next to it), Sales Order (Item),
  Requested Quantity, Fulfilled Quantity (optional), List Price (optional).
- **BOM report**: Product ID (+ description next to it), Line Item Group ID, Line Item ID,
  Raw Material (+ description next to it), Input Quantity, Output Quantity.

## Logic
RM Requirement = SO Qty × Π (Input Qty ÷ Output Qty) along the FG → SFG → RM path.
A component is treated as an SFG if a BOM for it exists in the uploaded files; otherwise it is an RM.
BOM input quantities already include BOM wastage; the sidebar "extra allowance" adds a buffer on top.
FGs with no uploaded BOM are listed as a warning and in a "Missing BOMs" sheet.
