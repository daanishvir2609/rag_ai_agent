cat > /mnt/user-data/outputs/README.md << 'EOF'
# Restaurant Review AI Agent

A fully local AI agent that answers questions about restaurant reviews using RAG (Retrieval Augmented Generation) and MCP (Model Context Protocol). Everything runs on your own machine — no paid APIs, no internet connection required after setup.

---

## What this system does

You can ask the agent questions like:
- *"What are the biggest complaints from customers?"*
- *"Is the restaurant getting better or worse over time?"*
- *"What do people love most about this place?"*
- *"What is the overall average rating?"*

The agent reads real customer reviews from a database, reasons about which tool to use, retrieves relevant evidence, and gives you a grounded answer — not a guess.

---

## How it works (simple overview)

```
You type a question
        ↓
agent.py — the AI brain (LLaMA 3.1 running locally)
        ↓
Decides which tool to call
        ↓
server.py — the MCP tool server (runs separately)
        ↓
Searches the review database
        ↓
Returns real data to the AI
        ↓
AI writes an answer based on actual reviews
```

---

## Prerequisites — what you need to install before anything else

### 1. Python 3.11 or 3.12
Check your version:
```bash
python3 --version
```

**Important:** This project does NOT work on Python 3.14 due to a compatibility issue with some dependencies. If you have 3.14, download 3.11 or 3.12 from python.org.

### 2. Ollama
Ollama lets you run AI models locally on your machine.

- Download from: **https://ollama.com**
- Install it like any normal Mac/Windows application
- After installing, open a terminal and run:

```bash
ollama serve
```

Leave this running. Then in a new terminal, download the two models this project needs:

```bash
ollama pull llama3.1:8b
ollama pull mxbai-embed-large
```

`llama3.1:8b` is the AI that answers your questions (~5GB download).
`mxbai-embed-large` is the model that converts reviews into searchable vectors (~700MB download).

These downloads only happen once. After that they live on your machine permanently.

---

## Setup — step by step

### Step 1 — Get the code

Clone the repository:
```bash
git clone <repository-link>
cd rag_ai_agent
```

Or if you downloaded a zip, unzip it and open a terminal in that folder.

### Step 2 — Create a virtual environment

A virtual environment is an isolated Python installation just for this project. It keeps the project's packages separate from everything else on your machine.

```bash
python3 -m venv venv
```

### Step 3 — Activate the virtual environment

**Mac/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

You will see `(venv)` appear at the start of your terminal line. This means it's active. You must do this every time you open a new terminal to work on this project.

### Step 4 — Install all required packages

```bash
pip install -r requirements.txt
```

This reads the `requirements.txt` file and installs every package the project needs. It may take a few minutes.

### Step 5 — Add your CSV file

Make sure the file `realistic_restaurant_reviews.csv` is in the project folder. This is the review data the agent reads from. The CSV must have these columns:

```
Title, Review, Rating, Date
```

---

## File structure — what each file does

```
rag_ai_agent/
│
├── server.py          ← MCP tool server — run this first
├── agent.py           ← AI agent — run this second
├── vector.py          ← Database setup — imported by server.py
├── requirements.txt   ← Package list
└── realistic_restaurant_reviews.csv  ← Your review data
```

**`vector.py`** reads the CSV, converts every review into a vector (a list of numbers representing its meaning), and saves them to a local database folder called `chrome_langchain_db`. This only happens on the first run — after that it loads the existing database.

**`server.py`** runs as a separate process and exposes 4 tools over HTTP on port 8000. The tools are: semantic review search, rating filter, statistics calculator, and trend analyser. Any MCP-compatible AI client can connect to this server.

**`agent.py`** connects to the server, fetches the available tools, and starts the conversation loop. It uses LLaMA 3.1 to reason about which tool to call, calls it via the server, and uses the results to write answers.

---

## Running the system

You need **two terminals open at the same time**. In VSCode you can open a split terminal with `Ctrl+Shift+`` ` (backtick).

### Terminal 1 — Start the MCP server

```bash
source venv/bin/activate
python3 server.py
```

Wait until you see:
```
Uvicorn running on http://127.0.0.1:8000
```

Leave this terminal running. Do not close it.

### Terminal 2 — Start the agent

```bash
source venv/bin/activate
python3 agent.py
```

You will see:
```
==================================================
  Pizza Restaurant Review Agent (MCP)
  Powered by LLaMA 3.1 + LangGraph + MCP
==================================================
Ask anything about the restaurant. Type 'q' to quit.
```

Now type your questions. Type `q` to quit.

---

## What the 4 tools do

The agent has 4 tools it can choose from. It picks automatically based on your question — you never need to specify which tool to use.

| Tool | What it does | Example question that triggers it |
|---|---|---|
| `review_retriever_tool` | Searches reviews by meaning/topic | "What do people say about the pizza?" |
| `rating_filter_tool` | Filters reviews by star rating | "What are the biggest complaints?" |
| `review_stats_tool` | Calculates overall statistics | "What is the average rating?" |
| `review_trend_tool` | Analyses ratings over time | "Is the restaurant improving?" |

---

## Good questions to try

```
What is the overall rating of the restaurant?
What are the biggest complaints from customers?
What do people love most about this place?
Is the restaurant getting better or worse over time?
What do customers say about the pizza quality?
What do people say about the service?
Give me a full summary — quality, rating, and trend
What percentage of customers give 5 stars?
Are recent customers happier than early customers?
Should I go to this restaurant?
```

---

## Troubleshooting

**`ModuleNotFoundError`**
You are not inside the virtual environment. Run `source venv/bin/activate` and try again.

**`connection refused` or MCP error**
The server is not running. Make sure `python3 server.py` is running in Terminal 1 before you start `agent.py`.

**`ollama: command not found`**
Ollama is not installed. Download it from https://ollama.com and install it.

**Model not found error**
You haven't pulled the models yet. Run:
```bash
ollama pull llama3.1:8b
ollama pull mxbai-embed-large
```

**Slow responses**
The model is running entirely on your CPU. This is normal — responses take 10-30 seconds depending on your machine. This is the tradeoff for running fully locally with no API costs.

**Python 3.14 errors**
Downgrade to Python 3.11 or 3.12. Python 3.14 has compatibility issues with some dependencies this project uses.

---

## Technology stack

| Component | Technology | Purpose |
|---|---|---|
| AI Model | LLaMA 3.1 8B via Ollama | Reasoning and answer generation |
| Embedding Model | mxbai-embed-large via Ollama | Converting text to vectors |
| Vector Database | Chroma | Storing and searching review vectors |
| Agent Framework | LangGraph | ReAct agent loop |
| Tool Protocol | MCP (FastMCP) | Exposing tools as a server |
| LLM Integration | LangChain | Connecting all components |
| Language | Python 3.11/3.12 | Everything |