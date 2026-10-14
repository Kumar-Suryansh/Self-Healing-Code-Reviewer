import ast
import json
import os
import re
from datetime import datetime
from typing import TypedDict

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

load_dotenv()

# ============================================================
# Page Configuration & Styling
# ============================================================
st.set_page_config(
    page_title="Self-Healing Code Reviewer",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Self-Healing Code Reviewer")
st.caption("Powered by LangGraph & Groq LPUs")

# ============================================================
# Sidebar Configuration
# ============================================================
st.sidebar.header("Configuration")

env_key = os.getenv("GROQ_API_KEY", "")
api_key = st.sidebar.text_input("Groq API Key", value=env_key, type="password")
selected_lang = st.sidebar.selectbox("Target Language", ["Python", "C++", "Java", "Go", "JavaScript"])
max_attempts = st.sidebar.slider("Max Generation Attempts", min_value=1, max_value=4, value=2)

if not api_key:
    st.warning("Please supply your Groq API Key in the sidebar or via .env to proceed.")
    st.stop()


# ============================================================
# Dynamic Model Discovery (Prevents 404 Model Errors)
# ============================================================
@st.cache_resource(show_spinner=False)
def resolve_groq_model(key: str) -> str:
    preferred = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b",
        "qwen/qwen3.6-27b",
        "allam-2-7b"
    ]
    try:
        client = Groq(api_key=key)
        live_models = [m.id for m in client.models.list().data]

        for pref in preferred:
            if pref in live_models:
                return pref

        excluded = ["whisper", "guard", "audio", "safeguard", "orpheus"]
        for m in live_models:
            if not any(k in m.lower() for k in excluded):
                return m
        return live_models[0]
    except Exception as e:
        st.sidebar.error(f"Model resolution error: {e}")
        return "openai/gpt-oss-120b"


active_model = resolve_groq_model(api_key)
st.sidebar.success(f"Active Model: `{active_model}`")

# ============================================================
# LangGraph Setup
# ============================================================
class CodeReviewState(TypedDict, total=False):
    task: str
    language: str
    code: str
    critique: str
    status: str
    iterations: int


llm = ChatGroq(model=active_model, api_key=api_key, temperature=0.1)


def invoke_model(messages: list[HumanMessage | SystemMessage]) -> str:
    try:
        response = llm.invoke(messages)
    except Exception as error:
        raise RuntimeError(f"Groq request failed: {error}") from error
    return response.content.strip()


def extract_code(response: str) -> str:
    match = re.fullmatch(r"```(?:\w+)?\s*\n?(.*?)\n?```", response, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else response.strip()


def parse_review(response: str) -> tuple[str, str]:
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL | re.IGNORECASE)
    payload = match.group(1) if match else response
    try:
        review = json.loads(payload)
        status = str(review["status"]).upper()
        critique = str(review.get("critique", "None")).strip()
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        return "NEEDS_FIX", f"Reviewer returned invalid JSON: {error}"

    if status not in {"APPROVED", "NEEDS_FIX"}:
        return "NEEDS_FIX", f"Reviewer returned unsupported status: {status}"
    return status, critique or "None"


def generator_node(state: CodeReviewState) -> dict:
    task = state["task"]
    lang = state.get("language", "Python")
    current_code = state.get("code", "")
    critique = state.get("critique", "")
    iteration = state.get("iterations", 0) + 1

    if current_code:
        prompt = (
            f"Task:\n{task}\n\nLanguage: {lang}\n\nCurrent code:\n```{lang.lower()}\n{current_code}\n```\n\n"
            f"Reviewer feedback:\n{critique}\n\n"
            f"Return only corrected, complete {lang} code. Do not include Markdown fences or explanations."
        )
    else:
        prompt = (
            f"Write clean, production-ready {lang} code for this task:\n{task}\n\n"
            f"Return only complete {lang} code. Do not include Markdown fences or explanations."
        )

    code = extract_code(invoke_model([HumanMessage(content=prompt)]))
    return {"code": code, "iterations": iteration}


def validator_node(state: CodeReviewState) -> dict:
    code = state["code"]
    lang = state.get("language", "Python")
    iteration = state["iterations"]

    if lang.lower() == "python":
        try:
            ast.parse(code)
        except SyntaxError as error:
            status = "MAX_ITERATIONS_REACHED" if iteration >= max_attempts else "NEEDS_FIX"
            return {
                "status": status,
                "critique": f"Syntax error at line {error.lineno}: {error.msg}",
            }

    messages = [
        SystemMessage(
            content=(
                f"You are a strict senior {lang} code reviewer. Assess correctness, edge cases, "
                "memory management, and performance. Return only valid JSON with exactly these fields: "
                '{"status": "APPROVED" or "NEEDS_FIX", "critique": "specific feedback or None"}.'
            )
        ),
        HumanMessage(content=f"Task:\n{state['task']}\n\nCode to review:\n```{lang.lower()}\n{code}\n```"),
    ]
    review_status, critique = parse_review(invoke_model(messages))

    if review_status == "NEEDS_FIX" and iteration >= max_attempts:
        review_status = "MAX_ITERATIONS_REACHED"
        critique = f"Maximum generation attempts reached. Last critique: {critique}"

    return {"status": review_status, "critique": critique}


def route_decision(state: CodeReviewState) -> str:
    return "fix" if state["status"] == "NEEDS_FIX" else "end"


workflow = StateGraph(CodeReviewState)
workflow.add_node("generator", generator_node)
workflow.add_node("validator", validator_node)
workflow.set_entry_point("generator")
workflow.add_edge("generator", "validator")
workflow.add_conditional_edges("validator", route_decision, {"fix": "generator", "end": END})
app = workflow.compile()

# ============================================================
# Streamlit Interactive Interface
# ============================================================
user_task = st.text_area(
    "Coding Task / Problem Statement",
    value="Round Robin Scheduling algorithm handling arrival time, burst time, and time quantum.",
    height=100
)

start_button = st.button("Generate & Review Code", type="primary")

if start_button:
    if not user_task.strip():
        st.error("Please enter a task statement.")
        st.stop()

    initial_state: CodeReviewState = {
        "task": user_task.strip(),
        "language": selected_lang
    }

    st.subheader("Autonomous Review Progress")
    progress_container = st.container()
    final_state = dict(initial_state)

    with st.spinner("Reviewer agent is active..."):
        try:
            for step_output in app.stream(initial_state):
                for node_name, updates in step_output.items():
                    final_state.update(updates)
                    with progress_container:
                        if node_name == "generator":
                            st.write(f"⚙️ **[Generator]**: Iteration `{updates.get('iterations', 1)}` code generated.")
                        elif node_name == "validator":
                            decision = updates.get("status")
                            badge = "🟢" if decision == "APPROVED" else "🟡"
                            st.write(f"{badge} **[Validator]**: Decision: `{decision}`")
                            with st.expander("View Validator Feedback"):
                                st.write(updates.get("critique", "None"))
        except Exception as e:
            st.error(f"Execution Error: {e}")
            st.stop()

    st.divider()

    # Results Section
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"Final Validated Code ({selected_lang})")
        st.code(final_state.get("code", ""), language=selected_lang.lower())

    with col2:
        st.subheader("Review Summary")
        st.metric("Final Status", final_state.get("status", "UNKNOWN"))
        st.metric("Total Iterations", final_state.get("iterations", 0))

        report_txt = (
            f"TASK:\n{user_task}\n\n"
            f"LANGUAGE: {selected_lang}\n"
            f"STATUS: {final_state.get('status')}\n"
            f"ITERATIONS: {final_state.get('iterations')}\n\n"
            f"CRITIQUE:\n{final_state.get('critique')}\n\n"
            f"FINAL CODE:\n{final_state.get('code')}\n"
        )

        st.download_button(
            label="📥 Download Report (.txt)",
            data=report_txt,
            file_name=f"code_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )