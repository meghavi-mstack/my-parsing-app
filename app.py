import streamlit as st
import tempfile
import base64
import ssl
import os
from io import BytesIO

# Required libraries for parsing
import pytesseract
from pdf2image import convert_from_path
from docling.document_converter import DocumentConverter
import pymupdf4llm
from mistralai import Mistral
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ----- Parsing Functions -----

def parse_with_pytesseract(pdf_stream):
    """Parse PDF using pytesseract OCR."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_stream.read())
        tmp_path = tmp.name
    images = convert_from_path(tmp_path)
    ocr_output = ""
    for i, img in enumerate(images):
        text = pytesseract.image_to_string(img)
        ocr_output += f"### Page {i+1}\n{text}\n\n"
    return ocr_output

def parse_with_docling(pdf_stream):
    """Parse PDF using docling.document_converter."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_stream.read())
        tmp_path = tmp.name
    ssl._create_default_https_context = ssl._create_unverified_context
    converter = DocumentConverter()
    result = converter.convert(tmp_path)
    docling_md = result.document.export_to_markdown()
    return docling_md

def parse_with_pymupdf(pdf_stream):
    """Parse PDF using pymupdf4llm."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_stream.read())
        tmp_path = tmp.name
    md_text = pymupdf4llm.to_markdown(tmp_path)
    return md_text

def parse_with_mistral(pdf_stream):
    """Parse PDF using the Mistral OCR API."""
    # Write the PDF stream to a temporary file.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_stream.read())
        tmp_path = tmp.name

    # Get the API key from environment variables.
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        return "Mistral API key is not set in environment variables."

    client = Mistral(api_key=api_key)

    # Upload the file to Mistral.
    with open(tmp_path, "rb") as file:
        uploaded_pdf = client.files.upload(
            file={"file_name": os.path.basename(tmp_path), "content": file},
            purpose="ocr"
        )

    # Retrieve a signed URL for processing.
    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)

    # Process OCR.
    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={"type": "document_url", "document_url": signed_url.url},
    )

    # Construct the markdown output.
    output = ""
    for page in ocr_response.pages:
        output += page.markdown + "\n\n"
    return output

def display_pdf(file_bytes):
    """Display PDF by encoding it in base64 and embedding it in an iframe."""
    base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# ----- Caching Helper Functions for Example PDFs -----

def get_cache_filename(example_path, method_slug):
    """Create a cache file path based on the PDF name and method."""
    base = os.path.splitext(os.path.basename(example_path))[0]
    return os.path.join("cache", f"{base}_{method_slug}.md")

def get_cached_conversion(example_path, method_slug, parser_function):
    """Return cached conversion if available; otherwise, parse and save to cache."""
    cache_file = get_cache_filename(example_path, method_slug)
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            result = f.read()
        return result
    else:
        with open(example_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_stream = BytesIO(pdf_bytes)
        result = parser_function(pdf_stream)
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(result)
        return result

# ----- Ensure Cache Directory Exists -----

if not os.path.exists("cache"):
    os.makedirs("cache")

# ----- Streamlit App Layout -----

st.title("Chemical Document Parsing Comparison")

# Sidebar for PDF Selection (left sidebar)
st.sidebar.header("PDF Selection")
uploaded_file = st.sidebar.file_uploader("Upload a PDF", type=["pdf"])
example_choice = st.sidebar.radio("Or select an example PDF",
                                  ("Example OCR PDF", "Example Non-OCR PDF"))

# Determine PDF source and load bytes
if uploaded_file is not None:
    pdf_source = "uploaded"
    pdf_bytes = uploaded_file.read()
    st.sidebar.success("PDF uploaded successfully!")
else:
    pdf_source = "example"
    # Update file paths as needed.
    example_path = "examples/Ocr.pdf" if example_choice == "Example OCR PDF" else "examples/Non_Ocr.pdf"
    try:
        with open(example_path, "rb") as f:
            pdf_bytes = f.read()
        st.sidebar.info(f"Using {example_choice}")
    except Exception as e:
        st.sidebar.error(f"Example file not found: {example_path}")
        pdf_bytes = None

# Process the PDF and cache conversion results
if pdf_bytes:
    if pdf_source == "uploaded":
        if "results" not in st.session_state:
            with st.spinner("Processing uploaded PDF, please wait..."):
                st.session_state.results = {}
                for method_name, parser in [
                    ("Pytesseract OCR", parse_with_pytesseract),
                    ("Docling Conversion", parse_with_docling),
                    ("PyMuPDF Conversion", parse_with_pymupdf),
                    ("Mistral OCR", parse_with_mistral)
                ]:
                    pdf_stream = BytesIO(pdf_bytes)
                    st.session_state.results[method_name] = parser(pdf_stream)
                st.session_state.results["Original Document"] = pdf_bytes
        results = st.session_state.results
    else:
        # Use a separate session state key for each example file.
        example_key = f"results_example_{example_choice.replace(' ', '_')}"
        if example_key not in st.session_state:
            with st.spinner("Processing example PDF, please wait..."):
                st.session_state[example_key] = {}
                for method_name, parser, slug in [
                    ("Pytesseract OCR", parse_with_pytesseract, "pytesseract"),
                    ("Docling Conversion", parse_with_docling, "docling"),
                    ("PyMuPDF Conversion", parse_with_pymupdf, "pymupdf"),
                    ("Mistral OCR", parse_with_mistral, "mistral")
                ]:
                    st.session_state[example_key][method_name] = get_cached_conversion(example_path, slug, parser)
                st.session_state[example_key]["Original Document"] = pdf_bytes
        results = st.session_state[example_key]

    # Only show method options if the conversion has completed
    if "Original Document" not in results:
        st.sidebar.info("Processing document... please wait.")
        st.info("Processing document... please wait.")
    else:
        st.sidebar.header("Method Options")
        selected_method = st.sidebar.radio("Select a parsing method", list(results.keys()))
        st.header(selected_method)
        if selected_method == "Original Document":
            display_pdf(results["Original Document"])
        else:
            st.markdown(results[selected_method])
else:
    st.info("Please upload a PDF or select an example from the sidebar.")
