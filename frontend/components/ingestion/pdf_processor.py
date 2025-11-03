"""
PDF Processing UI Components

Handles single PDF upload workflow including analysis, extraction, review, and embedding.
"""
import streamlit as st
import os
import pandas as pd
from typing import Dict, Any


def render_pdf_upload_workflow(
    pipeline: Any,
    uploaded_file: Any,
    selected_doc_type: str,
    base_output_dir: str
) -> None:
    """
    Render complete single PDF upload and processing workflow.
    
    Args:
        pipeline: StreamlitRAGPipeline instance
        uploaded_file: Streamlit uploaded file object
        selected_doc_type: Document type (policy, brochure, etc.)
        base_output_dir: Base output directory path
    """
    # Check if product name is provided
    if not st.session_state.product_name or not st.session_state.product_name.strip():
        st.error("❌ Please enter a Product Database Name in the sidebar before processing")
        st.stop()
    
    # Save uploaded file temporarily
    temp_pdf_path = os.path.join(base_output_dir, "temp", uploaded_file.name)
    os.makedirs(os.path.dirname(temp_pdf_path), exist_ok=True)
    
    with open(temp_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    pipeline.setup_directories(temp_pdf_path, base_output_dir)
    
    # Display file info
    _render_file_info(uploaded_file, pipeline)
    st.divider()
    
    # Step 1: PDF Analysis
    _render_analysis_step(pipeline)
    
    if st.session_state.analysis_complete:
        analysis = st.session_state.analysis_result
        
        # Step 2: Content Extraction
        _render_extraction_step(pipeline, analysis)
        
        # Step 3: Human Review (for tables)
        if analysis["has_tables"]:
            _render_review_step(pipeline)
        
        # Step 4: Chunking and Embedding
        if (not analysis["has_tables"]) or st.session_state.review_complete:
            _render_embedding_step(pipeline, analysis, selected_doc_type)


def _render_file_info(uploaded_file, pipeline):
    """Display file information metrics."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📄 PDF File", uploaded_file.name)
    with col2:
        st.metric("📁 Output Folder", pipeline.pdf_name)
    with col3:
        st.metric("💾 File Size", f"{uploaded_file.size / 1024:.1f} KB")


def _render_analysis_step(pipeline):
    """Render PDF analysis step."""
    st.header("🔍 Step 1: PDF Analysis")
    
    if st.button("Analyze PDF Content", type="primary"):
        with st.spinner("Analyzing PDF content..."):
            analysis = pipeline.analyze_pdf_content()
            st.session_state.analysis_complete = True
            st.session_state.analysis_result = analysis
    
    if st.session_state.analysis_complete:
        analysis = st.session_state.analysis_result
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📖 Total Pages", analysis["total_pages"])
        with col2:
            st.metric("📊 Tables Found", analysis["table_count"])
        with col3:
            st.metric("📈 Tables/Page", analysis["tables_per_page"])
        with col4:
            workflow = "Table Workflow" if analysis["has_tables"] else "Text-Only Workflow"
            st.metric("⚙️ Workflow", workflow)
        
        if analysis["has_tables"]:
            st.success(f"✅ {analysis['table_count']} tables detected - Using table extraction workflow")
        else:
            st.info("ℹ️ No tables detected - Using text-only extraction")
        
        st.divider()


def _render_extraction_step(pipeline, analysis):
    """Render content extraction step."""
    st.header("📤 Step 2: Content Extraction")
    
    existing = pipeline.check_existing_extractions()
    
    if existing["has_csv_files"] or existing["has_text_files"]:
        st.warning("⚠️ Existing extractions found!")
        col1, col2 = st.columns(2)
        with col1:
            if existing["has_csv_files"]:
                st.write(f"📊 {existing['csv_file_count']} CSV files (tables)")
        with col2:
            if existing["has_text_files"]:
                st.write(f"📄 {existing['text_file_count']} text files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        force_table_reextract = st.checkbox("Force re-extract tables", value=False)
        if st.button("Extract Tables", disabled=not analysis["has_tables"]):
            with st.spinner("Extracting tables..."):
                success, message = pipeline.extract_tables(force_table_reextract)
                if success:
                    st.success(message)
                else:
                    st.info(message)
                st.session_state.extraction_complete = True
    
    with col2:
        force_text_reextract = st.checkbox("Force re-extract text", value=False)
        if st.button("Extract Text"):
            with st.spinner("Extracting text..."):
                success, message = pipeline.extract_text_content(force_text_reextract)
                if success:
                    st.success(message)
                else:
                    st.info(message)
                st.session_state.extraction_complete = True


def _render_review_step(pipeline):
    """Render human review step for tables."""
    st.divider()
    st.header("👤 Step 3: Human Review (Tables)")
    
    review_completed = pipeline.check_manual_review_status()
    
    if review_completed:
        st.success("✅ Manual review already completed")
        st.session_state.review_complete = True
    else:
        table_mapping = pipeline.load_table_mapping()
        extracted_tables = pipeline.get_extracted_tables()
        
        if not table_mapping.empty:
            st.subheader("📊 Table File Mapping")
            st.write("Review and edit the table filenames if needed:")
            
            # Editable table mapping
            edited_mapping = st.data_editor(
                table_mapping,
                num_rows="fixed",
                disabled=["page_num", "table_idx"],
                key="table_mapping_editor"
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Save Mapping"):
                    pipeline.save_table_mapping(edited_mapping)
                    st.success("Table mapping saved!")
            
            with col2:
                if st.button("✅ Complete Review"):
                    pipeline.save_table_mapping(edited_mapping)
                    pipeline.mark_review_completed()
                    st.success("Review marked as complete!")
                    st.session_state.review_complete = True
                    st.rerun()
            
            with col3:
                if st.button("📄 Switch to Text-Only"):
                    pipeline.has_tables_flag = False
                    st.info("Switched to text-only mode")
            
            # Display extracted table files
            if extracted_tables:
                st.subheader("📁 Extracted Table Files")
                for table_file in extracted_tables:
                    with st.expander(f"📊 {table_file}"):
                        try:
                            df = pd.read_csv(os.path.join(pipeline.output_dir, table_file))
                            st.dataframe(df.head(10), use_container_width=True)
                            st.write(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
                        except Exception as e:
                            st.error(f"Error reading file: {e}")
        else:
            st.warning("⚠️ No table mapping found. Please extract tables first.")


def _render_embedding_step(pipeline, analysis, selected_doc_type):
    """Render chunking and embedding step."""
    st.divider()
    st.header("🧠 Step 4: Chunking & Embedding")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Output Directory:** `{pipeline.output_dir}`")
    with col2:
        st.write(f"**ChromaDB Directory:** `{pipeline.chroma_db_dir}`")
    
    # Check extraction status
    current_extractions = pipeline.check_existing_extractions()
    
    # Warnings
    _show_extraction_warnings(analysis, current_extractions)
    
    # Show extraction status
    if current_extractions["has_text_files"] or current_extractions["has_csv_files"]:
        _show_extraction_status(analysis, current_extractions)
        _show_content_preview(pipeline.output_dir, current_extractions)
    
    # Disable button if missing extractions
    disable_chunking = not current_extractions["has_text_files"] and not current_extractions["has_csv_files"]
    
    if disable_chunking:
        st.error("🚫 **Cannot proceed:** No content extracted. Please complete Step 2 first.")
    
    if st.button("🚀 Start Chunking & Embedding", type="primary", disabled=disable_chunking):
        with st.spinner("Processing chunks and generating embeddings..."):
            chunker, message = pipeline.chunk_and_embed(selected_doc_type)
            
            if chunker:
                st.success(message)
                st.session_state.chunker_embedder = chunker
                st.session_state.embedding_complete = True
                
                # Display results
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Total Chunks", chunker.collection.count())
                with col2:
                    st.metric("💾 Database", "ChromaDB")
                with col3:
                    st.metric("✅ Status", "Complete")
            else:
                st.error(message)


def _show_extraction_warnings(analysis, current_extractions):
    """Show warnings for missing extractions."""
    if analysis["has_tables"] and not current_extractions["has_csv_files"]:
        st.warning("⚠️ **Tables detected but not extracted!** Please extract tables in Step 2.")
    
    if not current_extractions["has_text_files"]:
        st.warning("⚠️ **No text files found!** Please extract text in Step 2.")
    
    if analysis["has_tables"] and current_extractions["has_csv_files"] and not current_extractions["has_text_files"]:
        st.error("🚨 **Critical:** Only tables extracted, no text content!")


def _show_extraction_status(analysis, current_extractions):
    """Show extraction status summary."""
    st.subheader("📋 Extraction Status Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if current_extractions["has_text_files"]:
            st.success(f"✅ Text: {current_extractions['text_file_count']} files")
        else:
            st.error("❌ Text: Not extracted")
    
    with col2:
        if analysis["has_tables"]:
            if current_extractions["has_csv_files"]:
                st.success(f"✅ Tables: {current_extractions['csv_file_count']} files")
            else:
                st.error("❌ Tables: Not extracted")
        else:
            st.info("➖ Tables: None detected")
    
    with col3:
        if analysis["has_tables"]:
            review_status = "✅ Complete" if st.session_state.review_complete else "⏳ Pending"
            st.write(f"**Review:** {review_status}")
        else:
            st.info("**Review:** Not needed")


def _show_content_preview(output_dir, current_extractions):
    """Show preview of content to be chunked."""
    with st.expander("📑 Content to be Chunked", expanded=False):
        st.write("**The following content will be included in chunking and embedding:**")
        
        if current_extractions["has_text_files"]:
            st.write(f"📝 **Text Content:** {current_extractions['text_file_count']} text files")
            text_files = [f for f in os.listdir(output_dir) if f.endswith("_text.txt")]
            for text_file in text_files[:3]:
                st.write(f"   • {text_file}")
            if len(text_files) > 3:
                st.write(f"   • ... and {len(text_files) - 3} more files")
        
        if current_extractions["has_csv_files"]:
            st.write(f"📊 **Table Content:** {current_extractions['csv_file_count']} table files")
            csv_files = [f for f in os.listdir(output_dir) if f.endswith(".csv") and f != "table_file_map.csv"]
            for csv_file in csv_files[:3]:
                st.write(f"   • {csv_file}")
            if len(csv_files) > 3:
                st.write(f"   • ... and {len(csv_files) - 3} more files")


def render_workflow_overview():
    """Render workflow overview for initial screen."""
    st.info("👆 Please upload a PDF file to get started")
    
    st.subheader("🔄 Workflow Overview")
    
    workflow_steps = [
        "📤 **Upload PDF** - Select your document",
        "🔍 **Analysis** - Detect tables and content structure", 
        "📊 **Extraction** - Extract tables and text content",
        "👤 **Review** - Human-in-the-loop table verification (if tables found)",
        "🧠 **Processing** - Chunk content and generate embeddings",
        "🔎 **Query** - Search and retrieve relevant information"
    ]
    
    for step in workflow_steps:
        st.markdown(step)
