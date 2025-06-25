# 📄 PDF Form Summarizer

This project extracts structured information from **ADT-1 Auditor Appointment PDFs**, summarizes key insights, and generates **LLM-ready prompts** and human-readable summaries for executive and compliance purposes.

<p align="center">
  <a href="https://formsummarygenerator.streamlit.app/" target="_blank">
    <img src="https://img.shields.io/badge/Launch-App-%23FF4B4B.svg?logo=streamlit&logoColor=white&style=for-the-badge">
  </a>
</p>

---

## 🚀 Features

- 🔍 **PDF Parsing** – Extracts key fields like company name, auditor info, audit period, and more.
- 📦 **Structured JSON Output** – Clean, mapped, and consolidated data.
- 🤖 **LLM Prompt Generation** – Generates contextual prompts for executive, compliance, and business summaries.
- 📝 **Readable Summaries** – Text-based summary generator for reports or presentation.
- 📂 **Batch Processing** – Processes all PDFs in the `pdf/` directory and exports to `structured_data/` and `summary/`.

---

## 🛠️ Tech Stack

- Python 3.10+
- PyPDF2 / pdfminer.six / pdfplumber (for PDF parsing)
- JSON / pathlib / datetime
- No external AI APIs used directly (LLM prompts are prepared for use)

---

## 📁 Project Structure

```bash
.
├── pdf/                     # Input PDF files (ADT-1)
├── structured_data/        # Extracted structured JSON files
├── summary/                # Human-readable text summaries
├── extractor.py            # Core extractor logic
├── summarizer.py           # Summary generator
├── requirements.txt        # Dependencies
└── README.md               # You are here
```


## ⚙️ How to Run (Locally)
### 1. Clone the repository
```
git clone https://github.com/yourusername/auditor-summary-tool.git
cd Form_Summary
```

### 2. (Optional but recommended) Create a virtual environment
```
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Add your PDF files to the `pdf/` folder

### 5. Run the extractor to generate structured JSON files
```
python extractor.py
```

### 6. Run the summarizer to create human-readable summaries
```
python summarizer.py
```

### 7. Check the output folders:
```
- structured_data/ → contains extracted JSON files
- summary/         → contains .txt summaries
```

### 8. (Optional) Run the Streamlit web app locally
```
streamlit run app.py
```
## 📄 Example Summary Output
```
ABC Ltd. (CIN: U12345WB2020PTC012345) has appointed XYZ & Co. (PAN: ABCDE1234F) as auditors to fill a casual vacancy. 
The appointment covers an audit period from 01-Apr-2024 to 31-Mar-2025, spanning 1 financial year. 
This appointment was formalized under Section 139 of the Companies Act, 2013, with the form filed on 20-Jun-2025 
(Certificate Serial: 00123456789).
```

## 🧠 LLM Prompt Example
```
Based on the collected data, generate a concise executive summary:

Company: ABC Ltd. (CIN: U12345WB2020PTC012345)
Auditor: XYZ & Co. (PAN: ABCDE1234F)
Appointment Type: Casual Vacancy
Audit Period: 01-Apr-2024 to 31-Mar-2025
Financial Years: 1

Key Points:
- The company ABC Ltd. has appointed an auditor
- This is a casual vacancy
- The appointed auditor is XYZ & Co.
- Audit period is from 01-Apr-2024 to 31-Mar-2025
- Appointment covers 1 financial year
- Form was filed on 20-Jun-2025
```

## 📌 Future Improvements
- Integration with OpenAI / LLMs for auto-summarization
- OCR support for scanned PDFs

## 🧑‍💻 Author  
🧑‍🔬 **Niloy Sannyal**  
📍 Dhaka, Bangladesh  
📧 niloysannyal@gmail.com  
