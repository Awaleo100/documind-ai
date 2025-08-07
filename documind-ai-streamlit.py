
import streamlit as st
import openai
import PyPDF2
import docx2txt

# Set your OpenAI API key (replace with your actual key or use env variables)
openai.api_key = "ssk-proj-FUGILtun4AttAhJD-RvK7sYRZV1-KrS9vprfZDFmTiMusI1zpaZ0yTps26BBFLHYgVK3rmliO6T3BlbkFJrw7oz0kNQUQL1ilIVYS3dl8MJhy8wjGcZawtNIEQLWe1bjVmZ8TPGt86hRsnwAz_0BfhALQqcA"

st.title("ðŸ“„ DocuMind AI - Document Q&A Assistant")

uploaded_file = st.file_uploader("Upload a document (PDF or DOCX)", type=["pdf", "docx"])

question = st.text_input("Ask a question about the document")

def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_docx(file):
    return docx2txt.process(file)

def ask_gpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert legal document assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

if uploaded_file and question:
    file_type = uploaded_file.name.split(".")[-1].lower()
    if file_type == "pdf":
        text = extract_text_from_pdf(uploaded_file)
    elif file_type == "docx":
        text = extract_text_from_docx(uploaded_file)
    else:
        st.error("Unsupported file type.")
        text = ""

    if text:
        prompt = f"""The following is a document:

{text}

Answer this question based on it:
{question}
"""
        answer = ask_gpt(prompt)
        st.markdown("### âœ… Answer:")
        st.write(answer)
