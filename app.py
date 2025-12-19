import streamlit as st
from rag_backend import HRPolicyAssistant, ROLE_ACCESS
from doc_ingest import extract_text, chunk_text

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Secure HR Policy Assistant",
    page_icon="🔐",
    layout="wide",
)

# ---------------- LOAD BACKEND ----------------
@st.cache_resource
def load_assistant():
    return HRPolicyAssistant(enable_llm=True)

assistant = load_assistant()

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("🔒 Access Control")

    role = st.selectbox(
        "Select Role",
        list(ROLE_ACCESS.keys())
    )

    st.caption(f"Access scope: {', '.join(ROLE_ACCESS[role])}")

    st.divider()

    st.header("📄 Upload HR Policy")

    uploaded_file = st.file_uploader(
        "Upload PDF or DOCX",
        type=["pdf", "docx"]
    )

    sensitivity = st.selectbox(
        "Policy Sensitivity",
        ["public", "employee", "manager", "confidential"]
    )

    if st.button("Securely Ingest"):
        if not uploaded_file:
            st.warning("Please upload a document.")
        else:
            with st.spinner("Encrypting and indexing securely..."):
                text = extract_text(uploaded_file)
                for chunk in chunk_text(text):
                    assistant.ingest_text(
                        chunk,
                        sensitivity,
                        source=uploaded_file.name
                    )
            st.success("Policy securely ingested.")

# ---------------- MAIN ----------------
st.title("🔐 Secure HR Policy Assistant")
st.caption("Encrypted, role-aware HR assistant powered by CyborgDB + Groq")

st.markdown(f"**Active Role:** `{role}`")

query = st.text_input(
    "Ask a policy question",
    placeholder="e.g. What are the office working hours?"
)

if st.button("Ask Assistant", type="primary"):
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Retrieving authorized information..."):
            answer = assistant.ask(query, role)

        st.subheader("🤖 Answer")

        if "cannot answer" in answer.lower():
            st.warning(answer)
        elif "DB Error" in answer:
            st.error(answer)
        else:
            st.success(answer)
