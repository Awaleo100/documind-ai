import streamlit as st
import tempfile
import PyPDF2
import docx2txt
import groq 

# Initialize Groq client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("📄 DocuMind AI - Document Q&A Assistant (Groq Edition)")

uploaded_file = st.file_uploader("Upload a document (PDF or DOCX)", type=["pdf", "docx"])
question = st.text_input("Ask a question about the document")

# ---------------------------
# File Processing Functions
# ---------------------------
def extract_text_from_pdf(file):
    """Extract text from PDF file."""
    try:
        reader = PyPDF2.PdfReader(file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_text_from_docx(file):
    """Extract text from DOCX file."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
        return docx2txt.process(tmp_path)
    except Exception as e:
        return f"Error reading DOCX: {e}"

# ---------------------------
# Chunking Function
# ---------------------------
def chunk_text(text, max_chars=8000):
    """Split text into chunks to avoid exceeding model context length."""
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

# ---------------------------
# Groq Query Function
# ---------------------------
def ask_groq(document_text, question):
    """Send the document and question to Groq for analysis."""
    chunks = chunk_text(document_text)
    answers = []

    for i, chunk in enumerate(chunks, start=1):
        prompt = f"""You are an expert legal document assistant.
The following is part {i} of a document:

{chunk}

Answer this question based only on this text:
{question}
"""
        resp = client.chat.completions.create(
            model="mixtral-8x7b-32768",  # Or "llama3-70b-8192"
            messages=[
                {"role": "system", "content": "You are a helpful assistant for analyzing legal and formal documents."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        answers.append(resp.choices[0].message.content.strip())

    if len(answers) > 1:
        summary_prompt = f"""The following are partial answers from different parts of a document:
{chr(10).join(answers)}

Provide one clear, concise final answer:"""
        summary_resp = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "You are a concise summarizer."},
                {"role": "user", "content": summary_prompt}
            ],
            max_tokens=500,
            temperature=0.2
        )
        return summary_resp.choices[0].message.content.strip()
    else:
        return answers[0] if answers else "No answer could be generated."

# ---------------------------
# Main App Logic
# ---------------------------
if uploaded_file and question:
    file_type = uploaded_file.name.split(".")[-1].lower()

    if file_type == "pdf":
        text = extract_text_from_pdf(uploaded_file)
    elif file_type == "docx":
        text = extract_text_from_docx(uploaded_file)
    else:
        st.error("Unsupported file type.")
        text = ""

    if text and not text.startswith("Error"):
        answer = ask_groq(text, question)
        st.markdown("### ✅ Answer:")
        st.write(answer)
    else:
        st.error(text)
