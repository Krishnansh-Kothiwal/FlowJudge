# FlowJudge

**FlowJudge** is a sleek agentic validation workflow designed for startup/product summary JSON generation with validation and critique. Built with **Streamlit** and **LangGraph**, it demonstrates an agentic approach to data generation where specialized nodes collaborate to ensure schema precision and semantic quality.

![FlowJudge Design](https://img.shields.io/badge/Design-Minimalist%20Dark-0a0a0a?style=for-the-badge)
![Built with LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-blue?style=for-the-badge)
![Powered by Gemini](https://img.shields.io/badge/Intelligence-Gemini%203.1-blue?style=for-the-badge)

## ⚡ Agentic Architecture

FlowJudge isn't just a prompt chain—it's a self-correcting agentic validation workflow. The system orchestrates five coordinated workflow nodes:

- **Planner Node**: Creates a fixed generation plan.
- **Generator Node**: Produces the initial structured JSON draft.
- **Schema Verifier**: Performs strict Pydantic validation. If the schema is invalid, it triggers the **Repair Node**.
- **Quality Critic**: Evaluates the semantic quality (specificity, realism, and tone). If quality is low, it triggers the **Repair Node**.
- **Repair Node**: Uses failure feedback (schema errors or critic notes) to iteratively fix the output.

### The Feedback Loop
The workflow can loop through repair and verification cycles automatically until the output satisfies all constraints. If retries are exhausted, the app surfaces failure state.

## 🛠️ Features

- **Premium UI**: A minimalist, high-contrast dark theme focused on user experience.
- **Configurable provider fallback chain**: Supports NVIDIA NIM (Kimi, Gemma) and Google Gemini for generation and repair.
- **Execution Trace**: View the execution trace, including planner decisions, provider routes, and execution logs.
- **Strict Validation**: Uses Pydantic to enforce rigid data schemas.

## 🚀 Setup

1. **Clone and Navigate**:
   ```bash
   cd flowjudge
   ```

2. **Environment Setup**:
   Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # macOS/Linux
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration**:
   Copy the example environment file and add your API keys:
   ```bash
   copy .env.example .env
   ```
   Open `.env` and add your `NVIDIA_API_KEY` and `GEMINI_API_KEY`.

5. **Launch the App**:
   ```bash
   streamlit run app.py
   ```

## 📖 Project Structure

- `app.py`: Streamlit frontend with premium minimalist styling.
- `graph.py`: LangGraph workflow orchestration and state management.
- `nodes.py`: Implementation of individual node logic (Planner, Generator, etc.).
- `llm.py`: Multi-provider fallback handling.
- `schemas.py`: Pydantic models for data validation.

---
*Designed for precision. Built for intelligence.*
