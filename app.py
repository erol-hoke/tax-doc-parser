import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import tempfile
import os

# Page config
st.set_page_config(
    page_title="Tax Document Parser",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = []
if 'parser' not in st.session_state:
    st.session_state.parser = None
if 'extractor' not in st.session_state:
    st.session_state.extractor = None

# Lazy load the processors only when needed
def get_parser():
    if st.session_state.parser is None:
        with st.spinner("Loading document parser (first time only)..."):
            from document_parser import TaxDocumentParser
            st.session_state.parser = TaxDocumentParser()
    return st.session_state.parser

def get_extractor():
    if st.session_state.extractor is None:
        with st.spinner("Loading LLM extractor..."):
            from llm_extractor import TaxDataExtractor
            st.session_state.extractor = TaxDataExtractor()
    return st.session_state.extractor

# Sidebar - Document Type and Field Configuration
st.sidebar.header("📋 Document Configuration")

# Predefined document types with common fields
DOCUMENT_TYPES = {
    "W-2": [
        "employer_name", "employer_ein", "employee_ssn", "employee_name",
        "wages_tips_other", "federal_income_tax_withheld", 
        "social_security_wages", "social_security_tax_withheld",
        "medicare_wages", "medicare_tax_withheld", "state", "state_income"
    ],
    "1099-INT": [
        "payer_name", "payer_tin", "recipient_name", "recipient_tin",
        "interest_income", "early_withdrawal_penalty", "interest_on_us_savings_bonds",
        "federal_income_tax_withheld", "investment_expenses"
    ],
    "1099-DIV": [
        "payer_name", "total_ordinary_dividends", "qualified_dividends",
        "capital_gain_distributions", "federal_income_tax_withheld",
        "section_199a_dividends", "nondividend_distributions"
    ],
    "1099-MISC": [
        "payer_name", "recipient_name", "rents", "royalties", 
        "other_income", "federal_income_tax_withheld", "nonemployee_compensation"
    ],
    "1099-NEC": [
        "payer_name", "payer_tin", "recipient_name", "recipient_tin",
        "nonemployee_compensation", "federal_income_tax_withheld"
    ],
    "UK-PAYE-Payslip": [
        # Employee & Employer Info
        "employer_name", "employer_paye_reference", "employee_name", 
        "national_insurance_number", "tax_code", "ni_category",
        # Pay Period Info
        "pay_date", "pay_period", "tax_year",
        # Earnings (for Foreign Earned Income Exclusion - Form 2555)
        "gross_pay", "basic_pay", "overtime_pay", "bonus", 
        "commission", "taxable_benefits", "benefits_in_kind",
        # Deductions - Critical for Foreign Tax Credit (Form 1116)
        "paye_tax_withheld", "national_insurance_employee",
        "national_insurance_employer",
        # Pension (may need reporting on Form 8938/FBAR)
        "pension_contribution_employee", "pension_contribution_employer",
        "pension_scheme_name",
        # Student Loan (not deductible for US taxes, but good to track)
        "student_loan_deduction", "student_loan_plan_type",
        # Other Deductions
        "other_deductions", "attachment_of_earnings",
        # Net Pay
        "net_pay",
        # Year-to-Date Totals (important for annual US filing)
        "ytd_gross_pay", "ytd_paye_tax", "ytd_national_insurance",
        "ytd_pension_contributions"
    ],
    "UK-P60": [
        # Annual summary - critical for US tax filing
        "employer_name", "employer_paye_reference", "employee_name",
        "national_insurance_number", "tax_code",
        "tax_year", 
        # Total Pay & Tax (for Form 1116 Foreign Tax Credit)
        "total_pay_in_year", "total_tax_in_year",
        # National Insurance (may qualify as creditable foreign tax)
        "total_ni_contributions", "ni_category",
        # Pension
        "total_pension_contributions",
        # Student Loan
        "total_student_loan_deductions",
        # Statutory Payments
        "statutory_maternity_pay", "statutory_paternity_pay",
        "statutory_sick_pay"
    ],
    "UK-P45": [
        # Leaving certificate - needed when changing jobs mid-year
        "employer_name", "employer_paye_reference", "employee_name",
        "national_insurance_number", "tax_code", "leaving_date",
        "total_pay_to_date", "total_tax_to_date",
        "student_loan_deduction_to_date"
    ],
    "Custom": []
}

doc_type = st.sidebar.selectbox(
    "Document Type",
    options=list(DOCUMENT_TYPES.keys())
)

# Field selection/customization
st.sidebar.subheader("Fields to Extract")

if doc_type == "Custom":
    custom_fields = st.sidebar.text_area(
        "Enter field names (one per line)",
        placeholder="field_name_1\nfield_name_2\nfield_name_3"
    )
    fields_to_extract = [f.strip() for f in custom_fields.split('\n') if f.strip()]
else:
    default_fields = DOCUMENT_TYPES[doc_type]
    fields_to_extract = st.sidebar.multiselect(
        "Select fields",
        options=default_fields,
        default=default_fields
    )
    
    # Option to add custom fields
    additional_fields = st.sidebar.text_input("Add custom field")
    if additional_fields:
        fields_to_extract.append(additional_fields)

# Main content
st.title("📄 Tax Document Parser")
st.markdown("Upload your tax documents and extract data automatically using local AI.")

# File uploader
uploaded_files = st.file_uploader(
    "Upload Documents",
    type=['pdf', 'png', 'jpg', 'jpeg', 'tiff'],
    accept_multiple_files=True
)

# Process button
if uploaded_files and fields_to_extract:
    if st.button("🔍 Extract Data", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing: {uploaded_file.name}")
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            try:
                # Parse document
                parsed = parser.parse_document(tmp_path)
                
                # Extract fields using LLM
                extracted = extractor.extract_fields(
                    parsed['markdown'],
                    fields_to_extract,
                    doc_type
                )
                
                # Add metadata
                extracted['_source_file'] = uploaded_file.name
                extracted['_document_type'] = doc_type
                
                st.session_state.extracted_data.append(extracted)
                
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            
            finally:
                os.unlink(tmp_path)
            
            progress_bar.progress((idx + 1) / len(uploaded_files))
        
        status_text.text("✅ Processing complete!")
        st.rerun()

# Display results table
if st.session_state.extracted_data:
    st.header("📊 Extracted Data")
    
    # Convert to DataFrame
    df = pd.DataFrame(st.session_state.extracted_data)
    
    # Configure AgGrid for editing
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, sortable=True, filter=True)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    grid_options = gb.build()
    
    # Display editable grid
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        fit_columns_on_grid_load=True,
        height=400
    )
    
    # Update session state with edited data
    st.session_state.extracted_data = grid_response['data'].to_dict('records')
    
    # Summary section
    st.header("📈 Summary")
    
    # Calculate numeric summaries
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    if len(numeric_cols) > 0:
        summary_df = df[numeric_cols].sum().to_frame(name='Total')
        summary_df = summary_df.T
        st.dataframe(summary_df, use_container_width=True)
    
    # Export options
    st.header("💾 Export")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            "tax_data.csv",
            "text/csv"
        )
    
    with col2:
        json_str = df.to_json(orient='records', indent=2)
        st.download_button(
            "📥 Download JSON",
            json_str,
            "tax_data.json",
            "application/json"
        )
    
    with col3:
        # Excel export
        import io
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        st.download_button(
            "📥 Download Excel",
            buffer.getvalue(),
            "tax_data.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # Clear data button
    if st.button("🗑️ Clear All Data"):
        st.session_state.extracted_data = []
        st.rerun()

else:
    st.info("👆 Upload documents and click 'Extract Data' to begin.")

# Footer
st.markdown("---")
st.markdown("*All processing happens locally on your machine. Your data never leaves your computer.*")