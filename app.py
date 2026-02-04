import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Batch Data Extractor", layout="wide")
st.title("📄 Bulk PDF Data Extractor")
st.markdown("Upload up to 200 PDF files to extract: **Ship To, Order ID, Phone, Seller Name, and SKU**.")

# --- 2. EXTRACTION LOGIC ---
def extract_data_from_pdf(file_bytes):
    """
    Extracts specific fields from a PDF file using layout-specific regex patterns.
    """
    text = ""
    # Open PDF from memory
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            # Extract text from page
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    # Initialize data dictionary
    data = {
        "Ship To": "",
        "Order ID": "",
        "Phone": "",
        "Seller Name": "",
        "SKU": ""
    }

    # --- REGEX PATTERNS ---
    
    # 1. PHONE
    # Captures number after "Phone:" (handles spaces and dashes)
    phone_match = re.search(r'Phone:\s*([0-9]+)', text)
    if phone_match:
        data["Phone"] = phone_match.group(1).strip()

    # 2. ORDER ID
    # Captures ID after "Order ID:"
    order_match = re.search(r'Order ID:\s*([0-9\-]+)', text)
    if order_match:
        data["Order ID"] = order_match.group(1).strip()

    # 3. SELLER NAME
    # Captures text for seller name, handling potential line break after the label
    seller_match = re.search(r'Seller Name:\s*\n?([^\n]+)', text)
    if seller_match:
        data["Seller Name"] = seller_match.group(1).strip()

    # 4. SKU
    # Captures alphanumeric SKU code
    sku_match = re.search(r'SKU:\s*([A-Za-z0-9\-\.]+)', text)
    if sku_match:
        data["SKU"] = sku_match.group(1).strip()

    # 5. SHIP TO (Multi-line Address Block)
    # Captures all text between "Ship to:" and the next key field (Phone or Order ID)
    ship_match = re.search(r'Ship to:\s*(.*?)(?=Phone:|Order ID:)', text, re.DOTALL)
    if ship_match:
        # Clean address: replace newlines with commas for CSV compatibility
        raw_address = ship_match.group(1).strip()
        clean_address = raw_address.replace("\n", ", ")
        data["Ship To"] = re.sub(r'\s+', ' ', clean_address).strip()

    return data

# --- 3. BATCH PROCESSING UI ---

uploaded_files = st.file_uploader(
    "Upload PDF files (Max 200)", 
    type="pdf", 
    accept_multiple_files=True
)

if uploaded_files:
    if st.button(f"Start Extraction for {len(uploaded_files)} files"):
        
        all_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Process each file
        for i, pdf_file in enumerate(uploaded_files):
            try:
                status_text.text(f"Processing file {i+1} of {len(uploaded_files)}...")
                
                # Read and Extract
                file_bytes = pdf_file.read()
                extracted_info = extract_data_from_pdf(file_bytes)
                
                # Add Metadata
                extracted_info["File Name"] = pdf_file.name
                all_data.append(extracted_info)
                
            except Exception as e:
                st.error(f"Error reading {pdf_file.name}: {e}")
            
            # Update Progress
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        # --- 4. DISPLAY & DOWNLOAD ---
        
        # Create DataFrame
        df = pd.DataFrame(all_data)
        
        # Organize Columns
        cols = ["Ship To", "Order ID", "Phone", "Seller Name", "SKU", "File Name"]
        df = df.reindex(columns=cols)
        
        st.success("Extraction Complete!")
        
        # Preview Data
        st.dataframe(df)
        
        # Download Button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name="extracted_data.csv",
            mime="text/csv",
        )
