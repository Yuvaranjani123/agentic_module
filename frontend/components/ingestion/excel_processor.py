"""
Excel Processing UI Components

Handles single Excel upload workflow for premium rate workbooks.
"""
import streamlit as st
import os
import requests
from typing import Any


def render_excel_upload_workflow(
    uploaded_file: Any,
    product_name: str,
    base_output_dir: str,
    django_api: str
) -> None:
    """
    Render complete Excel upload workflow for premium rate workbooks.
    
    Args:
        uploaded_file: Streamlit uploaded file object (Excel)
        product_name: Product database name
        base_output_dir: Base output directory path
        django_api: Django API base URL
    """
    st.header("📊 Premium Excel Upload")
    
    # Check if product name is provided
    if not product_name or not product_name.strip():
        st.error("❌ Please enter a Product Database Name in the sidebar before uploading")
        st.stop()
    
    # Display file info
    _render_excel_info(uploaded_file, product_name)
    st.divider()
    
    # Upload confirmation
    st.subheader("📤 Upload Premium Workbook")
    
    st.info("""
    **What happens next:**
    - Excel file will be saved to `media/premium_workbooks/`
    - File will be registered in the premium workbook registry
    - This product's premium calculator will use this Excel file
    """)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🚀 Upload Excel", type="primary"):
            _handle_excel_upload(uploaded_file, product_name, django_api)
    
    with col2:
        st.caption(f"Target: `{product_name}_premium_rates.xlsx`")


def _render_excel_info(uploaded_file: Any, product_name: str):
    """Display Excel file information."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Excel File", uploaded_file.name)
    with col2:
        st.metric("🏷️ Product", product_name)
    with col3:
        st.metric("💾 File Size", f"{uploaded_file.size / 1024:.1f} KB")
    
    # Show file preview info
    with st.expander("📋 File Details", expanded=False):
        st.write(f"**Original Filename:** {uploaded_file.name}")
        st.write(f"**Target Filename:** `{product_name}_premium_rates.xlsx`")
        st.write(f"**File Type:** {uploaded_file.type}")
        st.write(f"**Size:** {uploaded_file.size:,} bytes")


def _handle_excel_upload(uploaded_file: Any, product_name: str, django_api: str):
    """
    Handle Excel file upload to Django backend.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        product_name: Product database name
        django_api: Django API base URL
    """
    with st.spinner("Uploading premium Excel workbook..."):
        try:
            # Prepare multipart form data
            files = {
                'excel': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
            }
            
            # Use product name (without '_premium_chart') as doc_name
            # The backend will append '_premium_rates' to create the filename
            # We need to match the registry format: 'activ_assure_premium_chart'
            # So we send doc_name as '{product_name}_premium_chart'
            doc_name = f"{product_name.lower()}_premium_chart"
            
            data = {
                'doc_name': doc_name
            }
            
            # Call Django API
            response = requests.post(
                f"{django_api}/api/upload_premium_excel/",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                st.success("✅ Premium Excel uploaded successfully!")
                
                # Show upload details
                with st.expander("📋 Upload Details", expanded=True):
                    st.write(f"**Registry Key:** `{doc_name}`")
                    st.write(f"**Filename:** `{result.get('filename')}`")
                    st.write(f"**Saved Path:** `{result.get('excel_path')}`")
                    st.write(f"**Message:** {result.get('message')}")
                
                st.info(f"""
                **Next Steps:**
                1. ✅ Excel file is now registered in the premium calculator
                2. 🧮 The system can now calculate premiums for **{product_name}**
                3. 💬 Test it in the Agentic Query interface!
                
                **Example Query:** "Calculate premium for {product_name} for age 30"
                """)
                
                # Show success metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("✅ Status", "Uploaded")
                with col2:
                    st.metric("📁 Registry", "Updated")
                with col3:
                    st.metric("🧮 Calculator", "Ready")
                
            else:
                error_msg = response.json().get('error', 'Unknown error')
                st.error(f"❌ Upload failed: {error_msg}")
                st.write(f"**Status Code:** {response.status_code}")
                
        except requests.exceptions.Timeout:
            st.error("❌ Upload timed out. Please check your connection and try again.")
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to Django backend. Please ensure it's running.")
            st.write(f"**API URL:** {django_api}")
        except Exception as e:
            st.error(f"❌ Upload error: {str(e)}")
            st.exception(e)


def render_workflow_overview():
    """Render workflow overview for Excel uploads."""
    st.info("👆 Please upload an Excel file to get started")
    
    st.subheader("📊 Excel Upload Workflow")
    
    workflow_steps = [
        "📤 **Upload Excel** - Select your premium rate workbook",
        "🏷️ **Set Product Name** - Associate with a product",
        "📁 **Save to Registry** - File is registered in the system",
        "🧮 **Calculator Ready** - Premium calculations available",
        "💬 **Test Queries** - Use agentic interface to calculate premiums"
    ]
    
    for step in workflow_steps:
        st.markdown(step)
    
    st.divider()
    
    st.subheader("📋 Excel File Requirements")
    
    st.write("""
    **Your Excel file should contain:**
    - Age-based premium rates
    - Sum insured options
    - Policy type variations
    - Clear column headers
    
    **Supported Formats:**
    - `.xlsx` (Excel 2007+)
    - `.xls` (Excel 97-2003)
    """)
