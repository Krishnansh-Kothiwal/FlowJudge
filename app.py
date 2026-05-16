import json
from html import escape

import streamlit as st
from dotenv import load_dotenv

from graph import build_graph


load_dotenv(override=True)

PHASES = [
    ("planner", "Planner Agent", "Decides what the JSON should contain."),
    ("generator", "Generator Agent", "Creates the first structured JSON draft."),
    ("schema_verifier", "Schema Verifier", "Checks strict Pydantic validity."),
    ("quality_critic", "Quality Critic", "Judges usefulness and specificity."),
    ("repair", "Repair Agent", "Fixes schema or quality problems when needed."),
    ("final", "Final Output", "Presents the validated result and trace."),
]


def initial_state(task: str) -> dict:
    return {
        "task": task,
        "plan": "",
        "raw_output": "",
        "repaired_output": "",
        "current_output": "",
        "validated": False,
        "quality_passed": False,
        "final": None,
        "schema_error": None,
        "quality_feedback": None,
        "retries": 0,
        "provider_used": "",
        "provider_history": [],
        "repair_history": [],
        "logs": [],
    }


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg-color: #050505;
            --surface-color: #121212;
            --border-color: #2a2a2a;
            --text-main: #ffffff;
            --text-muted: #888888;
            --accent: #ffffff;
            --accent-hover: #cccccc;
        }

        .stApp {
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
        }

        header { visibility: hidden; }

        .stTextArea textarea {
            background-color: var(--surface-color) !important;
            border: 1px solid var(--border-color) !important;
            color: var(--text-main) !important;
            border-radius: 12px !important;
            padding: 16px !important;
            font-size: 1.1rem !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5) !important;
            transition: all 0.3s ease;
        }
        
        .stTextArea textarea:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 1px var(--accent) !important;
        }

        .stTextArea label {
            display: none !important;
        }

        .stButton > button {
            background-color: var(--text-main) !important;
            color: var(--bg-color) !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            padding: 0.5rem 2rem !important;
            transition: all 0.2s ease !important;
        }
        
        .stButton > button:hover {
            background-color: var(--accent-hover) !important;
            transform: translateY(-1px);
        }

        /* Back button styling */
        .back-btn > .stButton > button {
            background-color: transparent !important;
            color: var(--text-muted) !important;
            border: 1px solid var(--border-color) !important;
        }
        .back-btn > .stButton > button:hover {
            color: var(--text-main) !important;
            border-color: var(--text-main) !important;
        }

        .landing-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 45vh;
            text-align: center;
            animation: fadeIn 0.8s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .landing-title {
            font-size: 5rem;
            font-weight: 800;
            letter-spacing: -0.04em;
            margin-bottom: 0.5rem;
            color: var(--text-main);
            background: linear-gradient(180deg, #ffffff 0%, #a0a0a0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .landing-subtitle {
            color: var(--text-muted);
            font-size: 1.2rem;
            margin-bottom: 3rem;
            letter-spacing: 0.02em;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--border-color) !important;
            background-color: var(--surface-color) !important;
            border-radius: 12px !important;
        }

        .fj-section-title {
            color: var(--text-main);
            font-size: 1.1rem;
            font-weight: 600;
            margin: 0 0 8px;
            letter-spacing: -0.01em;
        }

        .fj-muted {
            color: var(--text-muted);
            font-size: 0.9rem;
            margin: 0 0 12px;
        }
        
        .fj-field {
            border-top: 1px solid var(--border-color);
            padding: 12px 0;
        }
        .fj-field:first-child {
            border-top: 0;
            padding-top: 0;
        }
        .fj-label {
            color: var(--text-muted);
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }
        .fj-value {
            color: var(--text-main);
            font-size: 0.95rem;
            line-height: 1.5;
        }
        .fj-list { margin: 0; padding-left: 1.2rem; color: var(--text-main); }
        .fj-list li { margin: 4px 0; }

        .fj-phase {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: var(--surface-color);
            padding: 12px 16px;
            margin-bottom: 10px;
            transition: all 0.3s ease;
        }
        .fj-phase-active {
            border-color: var(--text-main);
            box-shadow: 0 0 15px rgba(255,255,255,0.1);
        }
        .fj-phase-done {
            border-color: #333;
            opacity: 0.7;
        }
        .fj-phase-skipped {
            opacity: 0.4;
            border-style: dashed;
        }
        .fj-phase-name {
            font-weight: 600;
            font-size: 0.95rem;
            margin-bottom: 4px;
            color: var(--text-main);
        }
        .fj-phase-note {
            color: var(--text-muted);
            font-size: 0.85rem;
        }

        .fj-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 8px;
        }
        .fj-chip {
            border: 1px solid var(--border-color);
            background: var(--surface-color);
            color: var(--text-main);
            border-radius: 999px;
            padding: 4px 12px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        .fj-chip-ok { border-color: #2ea043; color: #3fb950; background: rgba(46, 160, 67, 0.1); }
        .fj-chip-warn { border-color: #d29922; color: #e3b341; background: rgba(210, 153, 34, 0.1); }
        .fj-chip-bad { border-color: #f85149; color: #ff7b72; background: rgba(248, 81, 73, 0.1); }

        .fj-route {
            border-left: 2px solid var(--text-muted);
            background: rgba(255,255,255,0.03);
            padding: 10px 14px;
            margin: 8px 0;
            border-radius: 0 6px 6px 0;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.85rem;
            color: var(--text-main);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, subtitle: str | None = None) -> None:
    st.markdown(f'<div class="fj-section-title">{escape(title)}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="fj-muted">{escape(subtitle)}</p>', unsafe_allow_html=True)


def status_chip(label: str, status: str) -> str:
    class_name = {
        "ok": "fj-chip fj-chip-ok",
        "warn": "fj-chip fj-chip-warn",
        "bad": "fj-chip fj-chip-bad",
    }.get(status, "fj-chip")
    return f'<span class="{class_name}">{escape(label)}</span>'


def phase_board(active: str | None, completed: list[str], skipped_repair: bool = False) -> str:
    cards = []
    for key, name, note in PHASES:
        if key in completed:
            class_name = "fj-phase fj-phase-done"
            state = "Done"
        elif key == active:
            class_name = "fj-phase fj-phase-active"
            state = "Running"
        elif key == "repair" and skipped_repair:
            class_name = "fj-phase fj-phase-skipped"
            state = "Skipped"
        else:
            class_name = "fj-phase"
            state = "Waiting"

        cards.append(
            f"""
            <div class="{class_name}">
                <div class="fj-phase-name">{escape(name)} · {escape(state)}</div>
                <div class="fj-phase-note">{escape(note)}</div>
            </div>
            """
        )
    return "".join(cards)


def list_items(items: list[str]) -> str:
    return "<ul class=\"fj-list\">" + "".join(f"<li>{escape(str(item))}</li>" for item in items) + "</ul>"


def show_json_block(label: str, value: str | dict | None) -> None:
    with st.expander(label, expanded=False):
        if isinstance(value, dict):
            st.json(value)
        else:
            st.code(value or "No output available.", language="json")


def show_final_output(final: dict | None) -> None:
    if not final:
        st.info("No final validated output is available.")
        return

    rows = [
        ("Title", escape(str(final.get("title", "")))),
        ("Summary", escape(str(final.get("summary", "")))),
        ("Target Users", list_items(final.get("target_users", []))),
        ("Core Features", list_items(final.get("core_features", []))),
        ("Risks", list_items(final.get("risks", []))),
    ]

    for label, value in rows:
        st.markdown(
            f"""
            <div class="fj-field">
                <div class="fj-label">{escape(label)}</div>
                <div class="fj-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def provider_route(result: dict) -> str:
    providers = result.get("provider_history", [])
    if not providers:
        return "No provider route recorded."
    return " -> ".join(providers)


def run_workflow(task: str, progress_slot, message_slot) -> dict:
    flow = build_graph()
    state = initial_state(task)
    completed: list[str] = []
    progress = st.progress(0, text="Starting workflow...")
    total_steps = len(PHASES)

    progress_slot.markdown(phase_board("planner", completed), unsafe_allow_html=True)

    for event in flow.stream(state):
        for node_name, update in event.items():
            if isinstance(update, dict):
                state.update(update)
            if node_name not in completed:
                completed.append(node_name)

            next_active = None
            for key, _, _ in PHASES:
                if key not in completed:
                    next_active = key
                    break

            repair_was_skipped = "repair" not in completed and (
                state.get("validated") and state.get("quality_passed")
            )
            visible_completed = completed.copy()
            if next_active is None and "final" not in visible_completed:
                visible_completed.append("final")

            progress_value = min((len(visible_completed) / total_steps), 1.0)
            progress.progress(progress_value, text=f"Completed {node_name.replace('_', ' ')}")
            progress_slot.markdown(
                phase_board(next_active, visible_completed, skipped_repair=repair_was_skipped),
                unsafe_allow_html=True,
            )
            message_slot.info(state.get("logs", ["Workflow is running..."])[-1])

    if "final" not in completed:
        completed.append("final")
    progress.progress(1.0, text="Workflow complete")
    progress_slot.markdown(
        phase_board(None, completed, skipped_repair="repair" not in completed),
        unsafe_allow_html=True,
    )
    message_slot.success("FlowJudge finished. Full output is ready below.")
    return state


st.set_page_config(page_title="FlowJudge", page_icon="FJ", layout="centered")
inject_styles()

if "has_run" not in st.session_state:
    st.session_state.has_run = False
if "task_input" not in st.session_state:
    st.session_state.task_input = ""

if not st.session_state.has_run:
    st.markdown(
        """
        <div class="landing-wrapper">
            <div class="landing-title">FlowJudge</div>
            <div class="landing-subtitle">Intelligent structured output generation</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    task = st.text_area(
        "Prompt",
        value=st.session_state.task_input,
        height=140,
        placeholder="Describe the JSON you want to generate. e.g., 'Create a startup summary for an AI tool...'",
        label_visibility="collapsed",
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Generate", use_container_width=True):
            if task.strip():
                st.session_state.task_input = task.strip()
                st.session_state.has_run = True
                st.rerun()
            else:
                st.warning("Please enter a prompt before generating.")

else:
    col1, col2 = st.columns([0.15, 0.85], vertical_alignment="center")
    with col1:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if st.button("← Back"):
            st.session_state.has_run = False
            st.session_state.pop("last_result", None)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div style="font-size: 1.5rem; font-weight: 700; color: white;">FlowJudge</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f"**Prompt:** {escape(st.session_state.task_input)}")
    st.markdown("---")
    
    progress_slot = st.empty()
    message_slot = st.empty()

    if "last_result" not in st.session_state:
        try:
            result = run_workflow(st.session_state.task_input, progress_slot, message_slot)
            st.session_state["last_result"] = result
        except RuntimeError as exc:
            st.session_state.pop("last_result", None)
            message_slot.error(str(exc))
        except Exception as exc:
            st.session_state.pop("last_result", None)
            message_slot.error(f"Workflow failed: {exc}")

    result = st.session_state.get("last_result")
    
    if result:
        validated = result.get("validated", False)
        quality_passed = result.get("quality_passed", False)
        repaired = bool(result.get("repair_history", []))

        st.markdown(
            f"""
            <div class="fj-chip-row">
                {status_chip("Schema passed" if validated else "Schema failed", "ok" if validated else "bad")}
                {status_chip("Quality passed" if quality_passed else "Quality pending or failed", "ok" if quality_passed else "warn")}
                {status_chip("Repair used" if repaired else "No repair", "warn" if repaired else "ok")}
                {status_chip(f"Retries: {result.get('retries', 0)}", "warn" if result.get("retries", 0) else "ok")}
            </div>
            <br>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("Final Output")
        with st.container(border=True):
            show_final_output(result.get("final"))
            show_json_block("Raw Final JSON", result.get("final"))

        trace_col, artifact_col = st.columns([1, 1], gap="large")

        with trace_col:
            st.subheader("Workflow Trace")
            with st.container(border=True):
                section_title("Planner Decision")
                st.write(result.get("plan") or "No plan created.")

            with st.container(border=True):
                section_title("Provider Route")
                st.markdown(f'<div class="fj-route">{escape(provider_route(result))}</div>', unsafe_allow_html=True)

            with st.container(border=True):
                section_title("Verifier and Critic")
                if result.get("schema_error"):
                    st.warning(result["schema_error"])
                else:
                    st.success("Schema verifier passed.")

                if result.get("quality_feedback"):
                    st.write(result["quality_feedback"])
                else:
                    st.info("Quality critic did not run.")

            with st.container(border=True):
                section_title("Execution Log")
                for index, entry in enumerate(result.get("logs", []), start=1):
                    st.markdown(f"**{index}.** {entry}")

        with artifact_col:
            st.subheader("Generated Artifacts")
            with st.container(border=True):
                section_title("Generator Output")
                show_json_block("Raw Generator JSON", result.get("raw_output", ""))

                section_title("Repair Output")
                if repaired:
                    for repair in result.get("repair_history", []):
                        st.markdown(f'<div class="fj-route">{escape(repair)}</div>', unsafe_allow_html=True)
                    show_json_block("Latest Repaired JSON", result.get("repaired_output", ""))
                else:
                    st.info("Repair was not needed for this run.")
