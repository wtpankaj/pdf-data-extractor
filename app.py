import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# Page Config
st.set_page_config(page_title="PDF Data Extractor", layout="wide")
st.title("📄 Bulk PDF Data Extractor")
st.write("Upload up to 200 PDFs to extract: Ship To, Order ID, Phone, Seller Name, SKU.")

# Extraction Function
def extract_data(file_bytes):
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
            
    # Regex Patterns - These look for specific keywords in the PDF
    data = {
        "Ship To": None,
        "Order ID": None,
        "Phone": None,
        "Seller Name": None,
        "SKU": None
    }
    
    # 1. Order ID (Looks for "Order ID:" followed by text)
    order = re.search(r'(?i)Order\s*ID[:#]?\s*([A-Za-z0-9-]+)', text)
    if order: data["Order ID"] = order.group(1)

    # 2. Phone (Looks for "Phone :" followed by digits)
    phone = re.search(r'(?i)(?:Phone|Mobile|Tel)[:.]?\s*([\d\+\-\s]+)', text)
    if phone: data["Phone"] = phone.group(1).strip()

    # 3. SKU (Looks for "SKU" followed by text)
    sku = re.search(r'(?i)SKU[:#]?\s*([A-Za-z0-9\-\.]+)', text)
    if sku: data["SKU"] = sku.group(1)

    # 4. Seller Name (Looks for "Seller Name" or "Sold By")
    seller = re.search(r'(?i)(?:Seller Name|Sold By)[:]?\s*(.+)', text)
    if seller: data["Seller Name"] = seller.group(1).strip()

    # 5. Ship To (Grabs text after "Ship To:" until a double newline)
    ship = re.search(r'(?i)Ship\s*To[:]?\s*(.*?)(?=\n\n|Order|Phone|SKU|$)', text, re.DOTALL)
    if ship: data["Ship To"] = ship.group(1).replace("\n", ", ").strip()

    return data

# File Uploader
uploaded_files = st.file_uploader("Drop PDFs here", type="pdf", accept_multiple_files=True)

if uploaded_files:
    if st.button("Extract Data"):
        all_data = []
        progress_bar = st.progress(0)
        
        for idx, file in enumerate(uploaded_files):
            try:
                # Extract
                details = extract_data(file.read())
                details["File Name"] = file.name
                all_data.append(details)
            except Exception as e:
                st.error(f"Error reading {file.name}")
            
            # Update Progress
            progress_bar.progress((idx + 1) / len(uploaded_files))
            
        # Show and Download Result
        df = pd.DataFrame(all_data)
        
        # Organize columns
        cols = ["Ship To", "Order ID", "Phone", "Seller Name", "SKU", "File Name"]
        df = df.reindex(columns=cols)
        
        st.dataframe(df)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "extracted_data.csv", "text/csv")
