# FlowJudge

**FlowJudge** is a sleek, multi-agent workflow designed to generate high-quality, validated, and critiqued structured JSON outputs. Built with **Streamlit** and **LangGraph**, it demonstrates an agentic approach to data generation where specialized agents collaborate to ensure schema precision and semantic quality.

![FlowJudge Design](https://img.shields.io/badge/Design-Minimalist%20Dark-0a0a0a?style=for-the-badge)
![Built with LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-blue?style=for-the-badge)
![Powered by Gemini](https://img.shields.io/badge/Intelligence-Gemini%203.1-blue?style=for-the-badge)

## ⚡ Agentic Architecture

FlowJudge isn't just a prompt chain—it's a self-correcting autonomous workflow. The system orchestrates five specialized agents:

- **Planner Agent**: Decides the JSON structure and requirements based on the user task.
- **Generator Agent**: Produces the initial structured JSON draft.
- **Schema Verifier**: Performs strict Pydantic validation. If the schema is invalid, it triggers the **Repair Agent**.
- **Quality Critic**: Evaluates the semantic quality (specificity, realism, and tone). If quality is low, it triggers the **Repair Agent**.
- **Repair Agent**: Uses failure feedback (schema errors or critic notes) to iteratively fix the output.

### The Feedback Loop
The workflow can loop through repair and verification cycles automatically until the output satisfies all constraints or the retry limit is reached.

## 🛠️ Features

- **Premium UI**: A minimalist, high-contrast dark theme focused on user experience.
- **Multi-Model Routing**: Supports NVIDIA NIM (Kimi, Gemma) and Google Gemini with automatic failover logic.
- **Execution Trace**: View the full multi-agent "thought process," including planner decisions, provider routes, and execution logs.
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
- `nodes.py`: Implementation of individual agent logic (Planner, Generator, etc.).
- `llm.py`: Multi-provider routing and fallback handling.
- `schemas.py`: Pydantic models for data validation.

## 📄 Resume Bullet

- Engineered **FlowJudge**, an agentic multi-agent workflow using **LangGraph** and **Streamlit** to automate the generation, validation, and semantic critique of structured JSON datasets, implementing iterative self-repair loops and multi-provider fallback logic (Gemini & NVIDIA NIM).

---
*Designed for precision. Built for intelligence.*
