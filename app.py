import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

st.set_page_config(page_title="Batch Data Extractor", layout="wide")
st.title("📄 Bulk PDF Data Extractor")
st.markdown("Upload up to 200 PDF files.")

def extract_data_from_pdf(file_bytes):
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    data = {
        "Ship To": "",
        "Order ID": "",
        "Phone": "",
        "Seller Name": "",
        "SKU": ""
    }

    # Regex Patterns (Updated to handle optional spaces before colons)
    
    # Phone
    phone_match = re.search(r'Phone\s*:\s*([\d\s\-]+)', text)
    if phone_match:
        data["Phone"] = phone_match.group(1).strip()

    # Order ID
    order_match = re.search(r'Order ID\s*:\s*([0-9\-]+)', text)
    if order_match:
        data["Order ID"] = order_match.group(1).strip()

    # Seller Name
    seller_match = re.search(r'Seller Name\s*:\s*\n?([^\n]+)', text)
    if seller_match:
        data["Seller Name"] = seller_match.group(1).strip()

    # SKU
    sku_match = re.search(r'SKU\s*:\s*([A-Za-z0-9\-\.]+)', text)
    if sku_match:
        data["SKU"] = sku_match.group(1).strip()

    # Ship To
    ship_match = re.search(r'Ship to\s*:\s*(.*?)(?=Phone\s*:|Order ID\s*:)', text, re.DOTALL)
    if ship_match:
        raw_address = ship_match.group(1).strip()
        clean_address = raw_address.replace("\n", ", ")
        data["Ship To"] = re.sub(r'\s+', ' ', clean_address).strip()

    return data

uploaded_files = st.file_uploader(
    "Upload PDF files", 
    type="pdf", 
    accept_multiple_files=True
)

if uploaded_files:
    if st.button(f"Start Extraction for {len(uploaded_files)} files"):
        
        all_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, pdf_file in enumerate(uploaded_files):
            try:
                status_text.text(f"Processing file {i+1}...")
                
                file_bytes = pdf_file.read()
                extracted_info = extract_data_from_pdf(file_bytes)
                extracted_info["File Name"] = pdf_file.name
                all_data.append(extracted_info)
                
            except Exception as e:
                st.error(f"Error reading {pdf_file.name}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        df = pd.DataFrame(all_data)
        
        cols = ["Ship To", "Order ID", "Phone", "Seller Name", "SKU", "File Name"]
        df = df.reindex(columns=cols)
        
        st.success("Extraction Complete!")
        st.dataframe(df)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="extracted_data.csv",
            mime="text/csv",
        )
