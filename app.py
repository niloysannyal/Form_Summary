import streamlit as st
import tempfile
import json
import os
from pathlib import Path
from extractor import Extractor
from summarizer import Summary


def main():
    st.set_page_config(
        page_title="PDF Form Summarizer",
        page_icon="📄",
        layout="wide"
    )

    st.title("📄 ADT-1 PDF Form Summarizer")
    st.markdown("Upload an ADT-1 PDF form to extract and generate a summary")

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Upload an ADT-1 form PDF to process"
    )

    if uploaded_file is not None:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        try:
            # Show processing status
            with st.spinner("Processing PDF..."):
                # Step 1: Extract data from PDF using extractor.py
                st.info("🔍 Extracting data from PDF...")
                extractor = Extractor(tmp_file_path)
                llm_ready_data = extractor.extract_for_llm_summary()

                # Step 2: Create temporary JSON for summarizer
                with tempfile.NamedTemporaryFile(mode='w', suffix=".json", delete=False) as tmp_json:
                    json.dump(llm_ready_data, tmp_json, indent=2, ensure_ascii=False)
                    tmp_json_path = tmp_json.name

                # Step 3: Generate summary using summarizer.py
                st.info("📝 Generating summary...")
                summarizer = Summary(tmp_json_path)
                summary = summarizer.generate_summary()

            # Display results
            st.success("✅ PDF processed successfully!")

            # Create two columns for better layout
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("📋 Executive Summary")
                st.markdown(f"**{summary}**")

                # Add copy button for summary
                if st.button("📋 Copy Summary to Clipboard"):
                    st.code(summary, language="text")
                    st.success("Summary displayed above for copying!")

            with col2:
                st.subheader("📊 Extraction Details")
                metadata = llm_ready_data['extraction_metadata']
                st.metric("Fields Extracted", metadata['total_fields_extracted'])
                st.metric("Processed Fields", metadata['processed_fields'])
                st.info(f"**Processed:** {metadata['timestamp'][:19]}")

            # Optional: Show key details in expandable sections
            st.markdown("---")
            st.subheader("📖 Detailed Information")

            col3, col4 = st.columns(2)

            with col3:
                with st.expander("🏢 Company Information"):
                    company = llm_ready_data['structured_data']['company_information']
                    for key, value in company.items():
                        if value != "Not specified":
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")

                with st.expander("📅 Appointment Details"):
                    appointment = llm_ready_data['structured_data']['appointment_details']
                    for key, value in appointment.items():
                        if value != "Not specified" and value != False:
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")

            with col4:
                with st.expander("👨‍💼 Auditor Information"):
                    auditor = llm_ready_data['structured_data']['auditor_information']
                    for key, value in auditor.items():
                        if value != "Not specified" and value != False:
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")

                with st.expander("📋 Compliance Information"):
                    compliance = llm_ready_data['structured_data']['compliance_information']
                    for key, value in compliance.items():
                        if value != "Not specified" and value != []:
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")

            # Show raw extracted fields if needed
            with st.expander("🔧 Raw Extracted Fields (Debug)"):
                raw_fields = llm_ready_data['raw_fields']
                if raw_fields:
                    st.json(raw_fields)
                else:
                    st.info("No raw fields extracted")

            # Download options
            st.markdown("---")
            st.subheader("💾 Download Options")

            col5, col6 = st.columns(2)

            with col5:
                # Download summary as text
                summary_bytes = summary.encode('utf-8')
                st.download_button(
                    label="📄 Download Summary (.txt)",
                    data=summary_bytes,
                    file_name=f"summary_{uploaded_file.name[:-4]}.txt",
                    mime="text/plain"
                )

            with col6:
                # Download structured data as JSON
                json_bytes = json.dumps(llm_ready_data, indent=2, ensure_ascii=False).encode('utf-8')
                st.download_button(
                    label="📊 Download Data (.json)",
                    data=json_bytes,
                    file_name=f"extracted_data_{uploaded_file.name[:-4]}.json",
                    mime="application/json"
                )

        except FileNotFoundError as e:
            st.error("❌ Required modules not found!")
            st.error("Please ensure both `extractor.py` and `summarizer.py` are in the same directory as this app.")
            st.code("Files needed:\n- extractor.py\n- summarizer.py\n- app.py")

        except Exception as e:
            st.error(f"❌ Error processing PDF: {str(e)}")
            st.error("Please ensure the uploaded file is a valid ADT-1 form PDF.")

            # Show detailed error in expander for debugging
            with st.expander("🐛 Debug Information"):
                st.code(f"Error Type: {type(e).__name__}")
                st.code(f"Error Message: {str(e)}")
                import traceback
                st.code(f"Traceback:\n{traceback.format_exc()}")

        finally:
            # Clean up temporary files
            try:
                os.unlink(tmp_file_path)
            except:
                pass
            try:
                os.unlink(tmp_json_path)
            except:
                pass

    else:
        # Instructions when no file is uploaded
        st.info("👆 Please upload a PDF file to get started")

        st.markdown("### 📋 Instructions:")
        st.markdown("""
        1. **Upload** an ADT-1 form PDF using the file uploader above
        2. **Wait** for the processing to complete
        3. **View** the generated executive summary
        4. **Explore** detailed information in the expandable sections
        5. **Download** the summary or structured data as needed
        """)

        st.markdown("### 📁 Required Files:")
        st.code("""
Directory structure:
├── app.py          (this file)
├── extractor.py    (PDF extraction module)
├── summarizer.py   (Summary generation module)
        """)

    # Add footer
    st.markdown("---")
    st.markdown(
        "📄 **ADT-1 Form Summarizer** - Extracts key information from auditor appointment forms and generate summary | "
        "Built with Streamlit"
    )


if __name__ == "__main__":
    main()
