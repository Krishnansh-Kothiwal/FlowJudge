# FlowJudge

**FlowJudge** is a validation-driven LLM orchestration workflow for structured startup/product summary generation. Built with **Streamlit** and **LangGraph**, it demonstrates how iterative validation, critique, and repair loops can improve the consistency and reliability of structured LLM outputs.

![FlowJudge Design](https://img.shields.io/badge/Design-Minimalist%20Dark-0a0a0a?style=for-the-badge)
![Built with LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-blue?style=for-the-badge)
![Powered by Gemini](https://img.shields.io/badge/LLM-Gemini%203.1-blue?style=for-the-badge)

## Workflow Architecture

FlowJudge uses a coordinated LangGraph workflow where each stage focuses on a specific part of the generation and validation pipeline.

- **Planning Stage**: Creates the generation instructions.
- **Generator Node**: Produces the initial structured JSON output.
- **Schema Validation Node**: Uses Pydantic validation to verify schema correctness. Invalid outputs are routed to the repair stage.
- **Quality Critique Node**: Evaluates clarity, specificity, realism, and overall output quality.
- **Repair Node**: Uses validation or critique feedback to iteratively improve failed outputs.

### Validation Loop

The workflow can move through multiple repair and validation cycles before returning the final structured result.

```text
Generate
→ Validate
→ Critique
→ Repair
→ Retry
```

If retry limits are exceeded, the workflow surfaces the failure state instead of silently accepting invalid output.

---

## Features

- **Minimalist Streamlit UI** with execution trace visualization
- **LangGraph workflow orchestration**
- **Structured JSON generation**
- **Strict Pydantic schema validation**
- **Iterative repair loops**
- **Provider fallback handling**
- **Execution logs and validation feedback**
- **Multi-stage output refinement**

---

## Example Schema

The current implementation generates structured startup/product summaries using the following schema:

```json
{
  "title": "string",
  "summary": "string",
  "target_users": ["string"],
  "core_features": ["string"],
  "risks": ["string"]
}
```

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Krishnansh-Kothiwal/FlowJudge.git
cd FlowJudge
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### macOS / Linux

```bash
source .venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Copy the example environment file:

```bash
copy .env.example .env
```

Add your API keys inside `.env`:

```env
GOOGLE_API_KEY=your_key_here
NVIDIA_API_KEY=your_key_here

GENERATOR_MODELS=gemini-3.1-flash-lite
CRITIC_MODELS=gemini-3.1-flash-lite
REPAIR_MODELS=gemini-3.1-flash-lite
```

---

### 5. Run the Application

```bash
streamlit run app.py
```

---

## Project Structure

```text
flowjudge/
│
├── app.py          # Streamlit frontend
├── graph.py        # LangGraph workflow orchestration
├── nodes.py        # Workflow node implementations
├── llm.py          # Provider handling and fallback logic
├── schemas.py      # Pydantic schemas
├── requirements.txt
├── .env.example
└── README.md
```

---

## Execution Trace

FlowJudge exposes workflow execution traces directly inside the UI, including:

- active workflow stage
- provider usage
- validation results
- critique feedback
- retry behavior
- repair attempts

This makes it easier to inspect how outputs evolve across refinement cycles.

---

## Current Limitations

- Current schema is fixed to startup/product summaries
- Provider retries are sequential
- Validation is schema-based only
- Workflow is optimized for demonstration purposes rather than production deployment

---

## Future Improvements

- Dynamic schema generation
- Adaptive model selection
- Parallel validation stages
- Streaming responses
- Persistent workflow memory
- Cost-aware provider selection

---

## License

MIT License
