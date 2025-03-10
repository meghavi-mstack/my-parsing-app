# Chemical Document Parsing Comparison

This project demonstrates a Streamlit app for comparing different methods for parsing chemical documents (PDFs). The app uses four parsing methods:
- **Pytesseract OCR**
- **Docling Conversion**
- **PyMuPDF Conversion**
- **Mistral OCR**

It also allows you to view the original PDF alongside parsed outputs. You can upload your own PDF or choose from two example PDFs.

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/my-parsing-app.git
   cd my-parsing-app
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate # On Linux/Mac
   venv\Scripts\activate # On Windows
   ```

3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the project root and add your Mistral API key:
   ```
   MISTRAL_API_KEY=your_api_key_here
   ```

5. **Prepare Example PDFs:**
   Place your example PDF files in the `examples` folder:
   * `examples/Ocr.pdf`
   * `examples/Non_Ocr.pdf`