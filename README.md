# 🕸️ RDF Navigator v4

An industry-ready RDF Knowledge Graph tool — no server required.  
Built with **rdflib + Oxigraph + Streamlit**.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📥 Smart Import | CSV, XLSX, JSON → RDF Turtle automatically |
| 🔍 Graph Explorer | Browse nodes, navigate relationships |
| 📊 SPARQL Suite | Predefined + custom SPARQL queries |
| 🛤️ Multi-Hop Paths | Find how any two resources connect (1–4 hops) |
| 🤖 AI Assistant | Ask questions in plain English → auto SPARQL (Gemini) |
| 🕸️ Graph View | Interactive PyVis visualization with dynamic colors |
| 🔀 RDF Diff | Snapshot & compare graph changes over time |
| 🧬 Auto-Ontology | Generate OWL ontology from your data automatically |
| 🧠 Reasoning | Apply OWL/RDFS rules to infer new facts |
| ⬇️ Export | Download any result as CSV or Excel |

---

## 🚀 Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/rdf-navigator.git
cd rdf-navigator

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your Gemini API key (optional, for AI features)
cp .env.example .env
# Edit .env and add: GEMINI_API_KEY=your_key_here

# 5. Run
streamlit run rdf_navigator_v4.py
```

---

## ☁️ Deploy to Streamlit Community Cloud (Free Public Link)

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "RDF Navigator v4"
git remote add origin https://github.com/YOUR_USERNAME/rdf-navigator.git
git push -u origin main
```

### Step 2 — Deploy
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repo → branch: `main` → file: `rdf_navigator_v4.py`
5. Click **"Advanced settings"** → add secret:
   ```
   GEMINI_API_KEY = "your_key_here"
   ```
6. Click **Deploy**

Your app will be live at:  
`https://YOUR_USERNAME-rdf-navigator-rdf-navigator-v4-XXXXX.streamlit.app`

---

## 📁 Project Structure

```
rdf-navigator/
├── rdf_navigator_v4.py        ← Main app (production)
├── rdf_navigator_v3.py        ← Previous version (reference)
├── rdf_navigator_enhanced.py  ← Enhanced version (reference)
├── rdf_navigator_original.py  ← Original version (reference)
├── requirements.txt           ← Python dependencies
├── .env                       ← API keys (never commit this!)
├── .env.example               ← Template for env vars
├── .gitignore                 ← Excludes .env and cache files
├── rdf_registry.json          ← Auto-generated file metadata
└── README.md
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Optional | Google Gemini key for AI features |

---

## 🏗️ Architecture

```
User Browser
    ↓
Streamlit (Python)
    ↓
OxigraphStore (embedded in-memory)
    ↓ (rdflib Graph synced)
RDFNavigator / SPARQL Engine
```

No Apache Fuseki server needed. All data is embedded in the running process.

> **Note:** Data resets on app restart (Streamlit Cloud).  
> For persistence, export your graph as TTL using the sidebar button and re-import on next session.  
> For production persistence, connect to a hosted triple store like GraphDB Cloud or Stardog.

---

## 📦 Dependencies

- [rdflib](https://rdflib.readthedocs.io/) — RDF graph engine
- [pyoxigraph](https://pyoxigraph.readthedocs.io/) — Fast embedded triple store
- [pyvis](https://pyvis.readthedocs.io/) — Interactive graph visualization
- [owlrl](https://owl-rl.readthedocs.io/) — OWL/RDFS reasoning
- [google-generativeai](https://ai.google.dev/) — Gemini AI for NL→SPARQL
- [streamlit](https://streamlit.io/) — Web UI framework
