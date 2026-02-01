import streamlit as st
import pandas as pd
import tempfile
import os

st.warning("🚨 RUNNING FEATURE BRANCH VERSION v3 (OCR)")
# Page config
st.set_page_config(
    page_title="Tax Document Parser",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = []

# Sidebar - Document Type and Field Configuration
st.sidebar.header("📋 Document Configuration")

DOCUMENT_TYPES = {
    "W-2": [
        "employer_name", "employer_ein", "employee_ssn", "employee_name",
        "wages_tips_other", "federal_income_tax_withheld", 
        "social_security_wages", "social_security_tax_withheld",
        "medicare_wages", "medicare_tax_withheld", "state", "state_income"
    ],
    "1099-NEC": [
        "payer_name", "payer_tin", "recipient_name", "recipient_tin",
        "nonemployee_compensation", "federal_income_tax_withheld"
    ],
    "UK-PAYE-Payslip": [
        "employer_name", "employee_name", "national_insurance_number", 
        "tax_code", "pay_date", "gross_pay", "basic_pay", 
        "paye_tax_withheld", "national_insurance_employee",
        "pension_contribution_employee", "student_loan_deduction",
        "net_pay", "ytd_gross_pay", "ytd_paye_tax"
    ],
    "UK-P60": [
        "employer_name", "employee_name", "national_insurance_number",
        "tax_code", "tax_year", "total_pay_in_year", "total_tax_in_year",
        "total_ni_contributions"
    ],
    "Custom": []
}

doc_type = st.sidebar.selectbox("Document Type", options=list(DOCUMENT_TYPES.keys()))

st.sidebar.subheader("Fields to Extract")

if doc_type == "Custom":
    custom_fields = st.sidebar.text_area("Enter field names (one per line)")
    fields_to_extract = [f.strip() for f in custom_fields.split('\n') if f.strip()]
else:
    default_fields = DOCUMENT_TYPES[doc_type]
    fields_to_extract = st.sidebar.multiselect("Select fields", options=default_fields, default=default_fields)

# Main content
st.title("📄 Tax Document Parser")
st.markdown("Upload your tax documents and extract data automatically using local AI.")

uploaded_files = st.file_uploader(
    "Upload Documents",
    type=['pdf', 'png', 'jpg', 'jpeg', 'tiff'],
    accept_multiple_files=True
)

# Show what's selected
if uploaded_files:
    st.write(f"**Files uploaded:** {[f.name for f in uploaded_files]}")
if fields_to_extract:
    st.write(f"**Fields to extract:** {len(fields_to_extract)} fields")

# Process button
if uploaded_files and fields_to_extract:
    if st.button("🔍 Extract Data", type="primary"):
        st.write("Button clicked! Starting extraction...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Load Docling
        status_text.text("Loading document parser...")
        st.write("⏳ Loading Docling (this may take a minute on first run)...")
        
        try:
            from document_parser import TaxDocumentParser
            parser = TaxDocumentParser()
            st.write("✅ Document parser loaded!")
        except Exception as e:
            st.error(f"❌ Failed to load document parser: {e}")
            st.stop()
        
        # Step 2: Load Ollama
        status_text.text("Loading LLM extractor...")
        st.write("⏳ Loading LLM extractor...")
        
        try:
            from llm_extractor import TaxDataExtractor
            extractor = TaxDataExtractor()
            st.write("✅ LLM extractor loaded!")
        except Exception as e:
            st.error(f"❌ Failed to load LLM extractor: {e}")
            st.stop()
        
        # Step 3: Process each file
        for idx, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing: {uploaded_file.name}")
            st.write(f"📄 Processing: {uploaded_file.name}")
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            st.write(f"  - Saved to temp: {tmp_path}")
            
            try:
                # Parse document
                st.write("  - Parsing document...")
                parsed = parser.parse_document(tmp_path)
                st.write(f"  - ✅ Parsed! Got {len(parsed['markdown'])} characters")
                
                # Show preview of parsed content
                with st.expander("Preview parsed content"):
                    st.text(parsed['markdown'][:1000] + "..." if len(parsed['markdown']) > 1000 else parsed['markdown'])
                
                # Extract fields
                st.write("  - Extracting fields with LLM...")
                extracted = extractor.extract_fields(
                    parsed['markdown'],
                    fields_to_extract,
                    doc_type
                )
                st.write(f"  - ✅ Extracted: {extracted}")
                
                extracted['_source_file'] = uploaded_file.name
                extracted['_document_type'] = doc_type
                
                st.session_state.extracted_data.append(extracted)
                
            except Exception as e:
                st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
            
            finally:
                os.unlink(tmp_path)
            
            progress_bar.progress((idx + 1) / len(uploaded_files))
        
        status_text.text("✅ Processing complete!")
        st.success("Done! Scroll down to see results.")

# Display results
if st.session_state.extracted_data:
    st.header("📊 Extracted Data")
    df = pd.DataFrame(st.session_state.extracted_data)
    st.dataframe(df, use_container_width=True)
    
    # Export
    st.header("💾 Export")
    csv = df.to_csv(index=False)
    st.download_button("📥 Download CSV", csv, "tax_data.csv", "text/csv")
    
    if st.button("🗑️ Clear All Data"):
        st.session_state.extracted_data = []
        st.rerun()
else:
    st.info("👆 Upload documents and click 'Extract Data' to begin.")

st.markdown("---")
st.markdown("*All processing happens locally. Your data never leaves your computer.*")