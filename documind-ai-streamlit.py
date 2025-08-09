import streamlit as st
import tempfile
import PyPDF2
import docx2txt
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("📄 DocuMind AI - Document Q&A Assistant")

uploaded_file = st.file_uploader("Upload a document (PDF or DOCX)", type=["pdf", "docx"])
question = st.text_input("Ask a question about the document")

# ---------------------------
# File Processing Functions
# ---------------------------
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_text_from_docx(file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
        return docx2txt.process(tmp_path)
    except Exception as e:
        return f"Error reading DOCX: {e}"

# ---------------------------
# Token-friendly chunking
# ---------------------------
def chunk_text(text, max_chars=8000):
    """Split text into chunks to avoid exceeding model context length."""
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

# ---------------------------
# GPT Query Function
# ---------------------------
def ask_gpt(document_text, question):
    try:
        chunks = chunk_text(document_text)
        answers = []

        for i, chunk in enumerate(chunks, start=1):
            prompt = f"""You are an expert legal document assistant.
The following is part {i} of a document:

{chunk}

Answer this question based only on this text:
{question}
"""
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for analyzing legal and formal documents."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            answers.append(response.choices[0].message.content.strip())

        # Combine answers if multiple chunks
        if len(answers) > 1:
            summary_prompt = f"""The following are partial answers to the same question from different parts of a document:
{chr(10).join(answers)}

Provide one clear, concise final answer:"""
            summary_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a concise summarizer."},
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=500,
                temperature=0.2
            )
            return summary_response.choices[0].message.content.strip()
        else:
            return answers[0]

    except Exception as e:
        return f"Error: {e}"

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
        answer = ask_gpt(text, question)
        st.markdown("### ✅ Answer:")
        st.write(answer)
    else:
        st.error(text)
