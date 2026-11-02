"""
📚 Study Buddy AI — Streamlit Frontend

Your personal AI study assistant.
Upload syllabi, chat with AI agents, get study plans, track attendance.

Run with: streamlit run app.py
"""

import os
import streamlit as st
import requests
from datetime import datetime, timedelta

# ── Page Configuration ─────────────────────────────────────────
st.set_page_config(
    page_title="Study Buddy AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── API Configuration ─────────────────────────────────────────
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# ── Custom Styling ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Global */
    .main { background-color: #0e1117; }
    
    /* Header */
    .app-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .app-header h1 { 
        margin: 0; 
        font-size: 2rem; 
        font-weight: 700; 
    }
    .app-header p { 
        margin: 0.3rem 0 0 0; 
        opacity: 0.85; 
        font-size: 1rem; 
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2a2a4a;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        transition: transform 0.2s;
    }
    .stat-card:hover { transform: translateY(-2px); }
    .stat-card h3 { color: #667eea; margin: 0; font-size: 1.8rem; }
    .stat-card p { color: #a0a0b0; margin: 0.3rem 0 0 0; font-size: 0.85rem; }
    
    /* Chat messages */
    .stChatMessage {
        border-radius: 12px !important;
        margin: 4px 0 !important;
    }
    
    /* Sidebar */
    .css-1d391kg { background-color: #0a0a14; }
    
    /* Success/warning boxes */
    .success-box {
        background: linear-gradient(135deg, #0a3d0a 0%, #1a4a1a 100%);
        border: 1px solid #2d7a2d;
        border-radius: 10px;
        padding: 1rem;
        color: #7dff7d;
    }
    
    /* Upload area */
    .upload-section {
        background: #1a1a2e;
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ───────────────────────────────────────────

def api_call(method: str, endpoint: str, timeout: int = 60, **kwargs):
    """Make an API call to the FastAPI backend with timeout and error handling."""
    url = f"{API_URL}{endpoint}"
    # Allow overriding timeout via kwargs
    timeout = kwargs.pop("timeout", timeout)
    try:
        if method == "GET":
            resp = requests.get(url, timeout=timeout)
        elif method == "POST":
            resp = requests.post(url, timeout=timeout, **kwargs)
        elif method == "PUT":
            resp = requests.put(url, timeout=timeout, **kwargs)
        elif method == "DELETE":
            resp = requests.delete(url, timeout=timeout)
        else:
            return None

        if resp.status_code == 200:
            return resp.json()
        else:
            detail = resp.text
            try:
                err_data = resp.json()
                if isinstance(err_data, dict) and "detail" in err_data:
                    detail = err_data["detail"]
            except Exception:
                pass
            st.error(f"❌ Backend Error ({resp.status_code}): {detail}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(
            f"❌ Cannot connect to backend at `{API_URL}`. "
            f"Make sure FastAPI is running on port 8000: `uvicorn api.main:app --reload --port 8000` "
            f"(or use the provided run_api script)."
        )
        return None
    except requests.exceptions.Timeout:
        st.error(f"⏳ Request to `{endpoint}` timed out after {timeout}s. The server may be restarting or overloaded.")
        return None
    except Exception as e:
        st.error(f"⚠️ Network error while calling {endpoint}: {e}")
        return None


def get_subjects(user_id: int = 1):
    """Load subjects from database."""
    result = api_call("GET", f"/subjects/?user_id={user_id}")
    if result and result.get("subjects"):
        return result["subjects"]
    return []


def create_subject(name: str, user_id: int = 1):
    """Create a new subject."""
    if not name or not name.strip():
        st.error("❌ Subject name cannot be empty.")
        return None
    result = api_call("POST", "/subjects/", json={"name": name.strip(), "user_id": user_id})
    if result:
        st.success(f"✅ Subject '{result['name']}' created successfully!")
        return result
    return None


def rename_subject(subject_id: int, new_name: str):
    """Rename an existing subject."""
    if not new_name or not new_name.strip():
        st.error("❌ Subject name cannot be empty.")
        return None
    result = api_call("PUT", f"/subjects/{subject_id}", json={"name": new_name.strip()})
    if result:
        st.success(f"✅ Subject renamed to '{result['name']}' successfully!")
        return result
    return None


def delete_subject(subject_id: int):
    """Delete a subject."""
    result = api_call("DELETE", f"/subjects/{subject_id}")
    if result:
        st.success(f"✅ {result.get('message', 'Subject deleted successfully!')}")
        return result
    return None


def check_api_health():
    """Check if the backend API is running."""
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


# ── Sidebar ────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎓 Study Buddy AI")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["💬 Chat", "📄 Upload Syllabus", "📅 Study Plans", "📊 Attendance"],
        index=0,
    )

    st.markdown("---")

    # API Status
    api_healthy = check_api_health()
    if api_healthy:
        st.success("🟢 Backend Connected")
    else:
        st.error("🔴 Backend Offline")
        st.caption("Run: `uvicorn api.main:app --reload`")

    st.markdown("---")
    st.caption("Built with Gemini + FastAPI + ChromaDB")
    st.caption("Powered by Gemini 3.8 Flash")


# ══════════════════════════════════════════════════════════════
# PAGE: CHAT
# ══════════════════════════════════════════════════════════════
if page == "💬 Chat":
    # Header
    st.markdown("""
    <div class="app-header">
        <h1>💬 Chat with Study Buddy</h1>
        <p>Ask about study planning, concepts, homework — I'll route you to the right AI agent.</p>
    </div>
    """, unsafe_allow_html=True)

    # Optional context
    with st.expander("⚙️ Chat Settings", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            exam_date = st.date_input(
                "Exam Date (for study planning)",
                value=datetime.now().date() + timedelta(days=30),
            )
        with col2:
            user_id = st.text_input("User ID", value="default")
            # Subject context for chat
            subjects_chat = get_subjects(user_id=1)
            if subjects_chat:
                chat_subject = st.selectbox(
                    "Subject Context",
                    options=[s["id"] for s in subjects_chat],
                    format_func=lambda x: next((s["name"] for s in subjects_chat if s["id"] == x), f"Subject {x}"),
                    key="chat_subject"
                )
            else:
                chat_subject = None
    
    # Subject management (outside any expander)
    with st.expander("📚 Manage Subjects"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Add Subject**")
            new_subj_c = st.text_input("New subject name", key="new_subj_chat")
            if st.button("Add", key="add_subj_chat"):
                if create_subject(new_subj_c, user_id=1):
                    st.rerun()
        with col_b:
            st.markdown("**Rename/Delete Subject**")
            subjects_manage_c = get_subjects(user_id=1)
            if subjects_manage_c:
                sel_subj_c = st.selectbox(
                    "Select subject",
                    options=[s["id"] for s in subjects_manage_c],
                    format_func=lambda x: next((s["name"] for s in subjects_manage_c if s["id"] == x), str(x)),
                    key="manage_subj_chat"
                )
                new_name_subj_c = st.text_input("New name", key="rename_subj_chat")
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("Rename", key="rename_btn_chat"):
                        if rename_subject(sel_subj_c, new_name_subj_c):
                            st.rerun()
                with col_b2:
                    if st.button("Delete", key="delete_btn_chat", type="secondary"):
                        if delete_subject(sel_subj_c):
                            st.rerun()
            else:
                st.info("No subjects to manage")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("agent"):
                st.caption(f"🤖 Handled by: {msg['agent']}")

    # Chat input
    if prompt := st.chat_input("Ask me anything about your studies..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                result = api_call(
                    "POST",
                    "/chat/message",
                    json={
                        "message": prompt,
                        "user_id": user_id,
                        "context": {"exam_date": exam_date.isoformat()},
                    },
                )

                if result:
                    st.markdown(result["response"])
                    st.caption(f"🤖 Handled by: {result['agent_used']}")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["response"],
                        "agent": result["agent_used"],
                    })
                else:
                    st.error("Failed to get a response. Is the backend running?")


# ══════════════════════════════════════════════════════════════
# PAGE: UPLOAD SYLLABUS
# ══════════════════════════════════════════════════════════════
elif page == "📄 Upload Syllabus":
    st.markdown("""
    <div class="app-header">
        <h1>📄 Upload Syllabus</h1>
        <p>Upload your course PDFs — they'll be parsed and indexed for intelligent search.</p>
    </div>
    """, unsafe_allow_html=True)

    # Upload form
    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            help="Upload your syllabus, course outline, or study materials.",
        )
    with col2:
        # Load subjects from DB
        subjects = get_subjects(user_id=1)
        if not subjects:
            st.warning("No subjects found. Add one below.")
            subject_options = []
        else:
            subject_options = [(s["id"], s["name"]) for s in subjects]
        
        if subject_options:
            selected_subject = st.selectbox(
                "Subject",
                options=[s[0] for s in subject_options],
                format_func=lambda x: next((s[1] for s in subject_options if s[0] == x), f"Subject {x}"),
                key="upload_subject"
            )
            subject_name = next((s[1] for s in subject_options if s[0] == selected_subject), "General")
        else:
            subject_name = st.text_input("Subject Name", value="General")
    
    # Subject management (outside any expander)
    with st.expander("📚 Manage Subjects"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Add Subject**")
            new_subj = st.text_input("New subject name", key="new_subj_upload")
            if st.button("Add", key="add_subj_upload"):
                if create_subject(new_subj, user_id=1):
                    st.rerun()
        with col_b:
            st.markdown("**Rename/Delete Subject**")
            subjects_manage = get_subjects(user_id=1)
            if subjects_manage:
                sel_subj = st.selectbox(
                    "Select subject",
                    options=[s["id"] for s in subjects_manage],
                    format_func=lambda x: next((s["name"] for s in subjects_manage if s["id"] == x), str(x)),
                    key="manage_subj_upload"
                )
                new_name_subj = st.text_input("New name", key="rename_subj_upload")
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("Rename", key="rename_btn_upload"):
                        if rename_subject(sel_subj, new_name_subj):
                            st.rerun()
                with col_b2:
                    if st.button("Delete", key="delete_btn_upload", type="secondary"):
                        if delete_subject(sel_subj):
                            st.rerun()
            else:
                st.info("No subjects to manage")

    if uploaded_file:
        if st.button("🚀 Upload & Process", type="primary", use_container_width=True):
            with st.spinner("📖 Parsing PDF and creating embeddings (this may take a minute for large files)..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                result = api_call(
                    "POST",
                    f"/documents/upload?subject_name={subject_name}",
                    files=files,
                    timeout=180,
                )

                if result:
                    st.balloons()
                    st.success(f"✅ {result['message']}")

                    # Show stats
                    c1, c2, c3 = st.columns(3)
                    c1.metric("📄 Pages", result["page_count"])
                    c2.metric("📚 Topics Found", result["topics_found"])
                    c3.metric("🧩 Chunks Created", result["chunks_created"])

                    # Show topics
                    if result.get("topics"):
                        st.markdown("### 📋 Detected Topics")
                        for i, topic in enumerate(result["topics"], 1):
                            st.markdown(f"{i}. {topic}")
                else:
                    st.error("❌ Failed to process and index PDF. Please check the backend console for error details.")

    # List existing documents
    st.markdown("---")
    st.markdown("### 📂 Uploaded Documents")

    docs_result = api_call("GET", "/documents/list")
    if docs_result and docs_result["documents"]:
        for doc in docs_result["documents"]:
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"📄 {doc['filename']}")
            col2.write(f"{doc['size_kb']} KB")
            if col3.button("🗑️", key=f"del_{doc['filename']}"):
                api_call("DELETE", f"/documents/{doc['filename']}")
                st.rerun()

        st.caption(f"Total chunks indexed: {docs_result['total_chunks_indexed']}")
    else:
        st.info("No documents uploaded yet. Upload a syllabus PDF to get started! 📤")


# ══════════════════════════════════════════════════════════════
# PAGE: STUDY PLANS
# ══════════════════════════════════════════════════════════════
elif page == "📅 Study Plans":
    st.markdown("""
    <div class="app-header">
        <h1>📅 Study Plans</h1>
        <p>Generate AI-powered study schedules based on your syllabus and exam dates.</p>
    </div>
    """, unsafe_allow_html=True)

    # Generate new plan
    with st.expander("✨ Generate New Plan", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            plan_request = st.text_area(
                "What do you want to plan?",
                placeholder="e.g., Create a 2-week study plan for my Data Structures exam",
                height=100,
            )
        with col2:
            plan_exam_date = st.date_input(
                "Exam Date",
                value=datetime.now().date() + timedelta(days=21),
            )
            # Load subjects from DB
            subjects_plan = get_subjects(user_id=1)
            if subjects_plan:
                plan_subject_id = st.selectbox(
                    "Subject",
                    options=[s["id"] for s in subjects_plan],
                    format_func=lambda x: next((s["name"] for s in subjects_plan if s["id"] == x), f"Subject {x}"),
                    key="plan_subject_select"
                )
            else:
                st.warning("No subjects found. Add one below.")
                plan_subject_id = st.number_input("Subject ID", value=1, min_value=1)

        if st.button("🚀 Generate Study Plan", type="primary", use_container_width=True):
            if plan_request:
                with st.spinner("📝 Creating your personalized study plan..."):
                    result = api_call(
                        "POST",
                        "/planner/generate",
                        json={
                            "user_id": 1,
                            "subject_id": plan_subject_id,
                            "exam_date": plan_exam_date.isoformat(),
                            "request_text": plan_request,
                        },
                    )

                    if result:
                        st.success(f"✅ Study plan created! (ID: {result['plan_id']})")
                        st.markdown("---")
                        st.markdown(result["plan"])
            else:
                st.warning("Please describe what you'd like to plan.")
    
    # Subject management (outside expander to avoid nesting)
    with st.expander("📚 Manage Subjects"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Add Subject**")
            new_subj_p = st.text_input("New subject name", key="new_subj_plan")
            if st.button("Add", key="add_subj_plan"):
                if create_subject(new_subj_p, user_id=1):
                    st.rerun()
        with col_b:
            st.markdown("**Rename/Delete Subject**")
            subjects_manage_p = get_subjects(user_id=1)
            if subjects_manage_p:
                sel_subj_p = st.selectbox(
                    "Select subject",
                    options=[s["id"] for s in subjects_manage_p],
                    format_func=lambda x: next((s["name"] for s in subjects_manage_p if s["id"] == x), str(x)),
                    key="manage_subj_plan"
                )
                new_name_subj_p = st.text_input("New name", key="rename_subj_plan")
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("Rename", key="rename_btn_plan"):
                        if rename_subject(sel_subj_p, new_name_subj_p):
                            st.rerun()
                with col_b2:
                    if st.button("Delete", key="delete_btn_plan", type="secondary"):
                        if delete_subject(sel_subj_p):
                            st.rerun()
            else:
                st.info("No subjects to manage")

    # View past plans
    st.markdown("---")
    st.markdown("### 📜 Your Study Plans")

    plans_result = api_call("GET", "/planner/1")
    if plans_result and plans_result["plans"]:
        for plan in plans_result["plans"]:
            with st.expander(f"📅 {plan['title'] or 'Untitled Plan'} — {plan.get('exam_date', 'No date')}"):
                st.markdown(plan["content"])
                st.caption(f"Created: {plan.get('created_at', 'Unknown')}")
    else:
        st.info("No study plans yet. Generate your first plan above! ✨")


# ══════════════════════════════════════════════════════════════
# PAGE: ATTENDANCE
# ══════════════════════════════════════════════════════════════
elif page == "📊 Attendance":
    st.markdown("""
    <div class="app-header">
        <h1>📊 Attendance Tracker</h1>
        <p>Track your class attendance and get AI-powered advice.</p>
    </div>
    """, unsafe_allow_html=True)

    # Subject selection
    subjects_att = get_subjects(user_id=1)
    if subjects_att:
        subject_id = st.selectbox(
            "Select Subject",
            options=[s["id"] for s in subjects_att],
            format_func=lambda x: next((s["name"] for s in subjects_att if s["id"] == x), f"Subject {x}"),
            key="attendance_subject"
        )
    else:
        st.warning("No subjects found. Add one below.")
        subject_id = st.number_input("Subject ID", value=1, min_value=1)

    # Subject management (outside - move before/after as needed, but ensure not nested)
    with st.expander("📚 Manage Subjects"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Add Subject**")
            new_subj_a = st.text_input("New subject name", key="new_subj_att")
            if st.button("Add", key="add_subj_att"):
                if create_subject(new_subj_a, user_id=1):
                    st.rerun()
        with col_b:
            st.markdown("**Rename/Delete Subject**")
            subjects_manage_a = get_subjects(user_id=1)
            if subjects_manage_a:
                sel_subj_a = st.selectbox(
                    "Select subject",
                    options=[s["id"] for s in subjects_manage_a],
                    format_func=lambda x: next((s["name"] for s in subjects_manage_a if s["id"] == x), str(x)),
                    key="manage_subj_att"
                )
                new_name_subj_a = st.text_input("New name", key="rename_subj_att")
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("Rename", key="rename_btn_att"):
                        if rename_subject(sel_subj_a, new_name_subj_a):
                            st.rerun()
                with col_b2:
                    if st.button("Delete", key="delete_btn_att", type="secondary"):
                        if delete_subject(sel_subj_a):
                            st.rerun()
            else:
                st.info("No subjects to manage")

    # Mark attendance
    st.markdown("### ✋ Mark Today's Attendance")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Present", use_container_width=True, type="primary"):
            result = api_call(
                "POST",
                "/attendance/mark",
                json={
                    "user_id": 1,
                    "subject_id": subject_id,
                    "attended": True,
                },
            )
            if result:
                st.success(result["message"])
                st.rerun()

    with col2:
        if st.button("❌ Absent", use_container_width=True):
            reason = st.session_state.get("absence_reason", "")
            result = api_call(
                "POST",
                "/attendance/mark",
                json={
                    "user_id": 1,
                    "subject_id": subject_id,
                    "attended": False,
                    "reason": reason,
                },
            )
            if result:
                st.warning(result["message"])
                st.rerun()

    absence_reason = st.text_input("Reason for absence (optional)", key="absence_reason")

    # Display stats
    st.markdown("---")
    st.markdown("### 📈 Attendance Statistics")

    att_result = api_call("GET", f"/attendance/1/{subject_id}")

    if att_result:
        stats = att_result["stats"]

        # Metrics row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📊 Percentage", f"{stats['percentage']}%")
        c2.metric("✅ Present", stats["attended"])
        c3.metric("❌ Absent", stats["absent"])
        c4.metric("📚 Total", stats["total_classes"])

        # Status
        st.markdown(f"**Status:** {stats['status']}")

        if stats["classes_needed_for_75"] > 0:
            st.warning(
                f"⚠️ You need to attend the next **{stats['classes_needed_for_75']}** "
                f"consecutive classes to reach 75%."
            )

        # Progress bar
        st.progress(min(stats["percentage"] / 100, 1.0))

        # AI Advice
        st.markdown("---")
        if st.button("🤖 Get AI Attendance Advice"):
            with st.spinner("Analyzing your attendance..."):
                advice_result = api_call("GET", f"/attendance/advice/1/{subject_id}")
                if advice_result:
                    st.info(advice_result["advice"])

        # Recent records
        if att_result["records"]:
            st.markdown("### 📋 Recent Records")
            for record in att_result["records"][:10]:
                icon = "✅" if record["attended"] else "❌"
                reason_text = f" — {record['reason']}" if record.get("reason") else ""
                st.write(f"{icon} {record['date']}{reason_text}")
    else:
        st.info("No attendance records yet. Start marking your attendance above! ✋")
