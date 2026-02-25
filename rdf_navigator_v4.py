"""
RDF Navigator v4 — Production Ready
=====================================
Backend   : Oxigraph (embedded, no separate server needed)
Deployment: Streamlit Community Cloud
New Features:
  1. Export results as CSV / Excel
  2. Graph Statistics Dashboard
  3. Multi-hop Path Explorer
  4. Saved SPARQL Queries
  5. RDF Diff Tool
  6. Auto-Ontology Generator
  7. AI Natural Language → SPARQL (Groq — Free)
  8. Semantic Reasoning (owlrl)
  9. Dynamic Graph Visualization (PyVis)
"""

import streamlit as st
import pandas as pd
import io
import os
import re
import json
import hashlib
import random
import tempfile
from datetime import datetime
from collections import defaultdict

# --- rdflib (always available) ---
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, OWL, XSD
from rdflib.namespace import NamespaceManager

# --- Optional dependencies with graceful degradation ---
try:
    import pyoxigraph as ox
    OXIGRAPH_AVAILABLE = True
except ImportError:
    OXIGRAPH_AVAILABLE = False

try:
    from pyvis.network import Network
    import streamlit.components.v1 as components
    PYVIS_AVAILABLE = True
except ImportError:
    PYVIS_AVAILABLE = False

try:
    import owlrl
    OWLRL_AVAILABLE = True
except ImportError:
    OWLRL_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title=" RDF Navigator",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🕸️"
)

st.markdown("""
<style>
/* ── Global ────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stDeployButton { display: none; }
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* ── Header / Title ────────────────────────────────────── */
.app-header {
    background: linear-gradient(135deg, #1565C0 0%, #0D47A1 60%, #01579B 100%);
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 24px;
    color: white;
    display: flex;
    align-items: center;
    gap: 16px;
}
.app-header h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    color: white !important;
    letter-spacing: -0.5px;
}
.app-header p {
    margin: 4px 0 0 0;
    font-size: 0.9rem;
    opacity: 0.85;
    color: white !important;
}

/* ── Metric Cards ──────────────────────────────────────── */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
    border: 1px solid #BBDEFB;
    border-left: 4px solid #1565C0;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(21,101,192,0.08);
    transition: transform 0.2s, box-shadow 0.2s;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(21,101,192,0.15);
}
div[data-testid="metric-container"] label {
    color: #1565C0 !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #0D47A1 !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

/* ── Tabs ──────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #E3F2FD;
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 500;
    font-size: 0.88rem;
    color: #1565C0;
    background: transparent;
    border: none;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: #1565C0 !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(21,101,192,0.3);
}

/* ── Buttons ───────────────────────────────────────────── */
.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    font-size: 0.88rem;
    border: 1.5px solid #1565C0;
    color: #1565C0;
    background: white;
    transition: all 0.2s;
    padding: 6px 16px;
}
.stButton > button:hover {
    background: #1565C0;
    color: white;
    box-shadow: 0 2px 8px rgba(21,101,192,0.3);
    transform: translateY(-1px);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1565C0, #0D47A1);
    color: white;
    border: none;
    box-shadow: 0 2px 8px rgba(21,101,192,0.3);
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #0D47A1, #01579B);
    box-shadow: 0 4px 16px rgba(21,101,192,0.4);
}

/* ── Sidebar ───────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D47A1 0%, #1565C0 40%, #1976D2 100%);
    border-right: none;
}
[data-testid="stSidebar"] * {
    color: white !important;
}
[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: rgba(255,255,255,0.15) !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    border-radius: 8px;
    color: white !important;
}
[data-testid="stSidebar"] .stTextInput > div > div > input::placeholder {
    color: rgba(255,255,255,0.6) !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.4);
    color: white! important;
    width: 100%;
    border-radius: 8px;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.25);
    transform: none;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: rgba(229,57,53,0.8);
    border: 1px solid rgba(229,57,53,0.5);
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.2) !important;
}
[data-testid="stSidebar"] [data-testid="stDownloadButton"] button {
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.4);
    color: white !important;
    width: 100%;
    border-radius: 8px;
}

/* ── Expander ──────────────────────────────────────────── */
div[data-testid="stExpander"] {
    border: 1px solid #BBDEFB;
    border-radius: 10px;
    overflow: hidden;
}
div[data-testid="stExpander"] summary {
    background: #E3F2FD;
    padding: 12px 16px;
    font-weight: 600;
    color: #1565C0;
}

/* ── Dataframe ─────────────────────────────────────────── */
div[data-testid="stDataFrame"] {
    border: 1px solid #BBDEFB;
    border-radius: 10px;
    overflow: hidden;
}

/* ── Alerts ────────────────────────────────────────────── */
div[data-testid="stAlert"] {
    border-radius: 8px;
    border-left-width: 4px;
}

/* ── Chat ──────────────────────────────────────────────── */
div[data-testid="stChatMessage"] {
    border-radius: 12px;
    margin-bottom: 8px;
    border: 1px solid #E3F2FD;
}

/* ── Code blocks ───────────────────────────────────────── */
div[data-testid="stCodeBlock"] {
    border-radius: 8px;
    border: 1px solid #BBDEFB;
}

/* ── Mobile responsive ─────────────────────────────────── */
@media (max-width: 768px) {
    .block-container { padding: 0.5rem 0.5rem 2rem; }
    .app-header { padding: 16px; }
    .app-header h1 { font-size: 1.4rem; }
    div[data-testid="metric-container"] { padding: 10px 12px; }
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# FEATURE 1 — OXIGRAPH BACKEND
# Replaces Apache Fuseki entirely.
# Uses an in-memory rdflib Graph as fallback.
# ============================================================
class OxigraphStore:
    """
    Embedded triple store using Oxigraph (pyoxigraph).
    Falls back to rdflib in-memory Graph if pyoxigraph is not installed.
    Both expose the same interface so the rest of the app is backend-agnostic.
    """
    def __init__(self):
        if OXIGRAPH_AVAILABLE:
            self._store = ox.Store()
            self._backend = "oxigraph"
        else:
            self._store = Graph()
            self._backend = "rdflib"
        self._graph = Graph()  # rdflib graph kept in sync for SPARQL

    def get_backend_name(self) -> str:
        return self._backend

    def upload_ttl(self, ttl_data: str) -> bool:
        """Parse TTL and add to the store."""
        try:
            g = Graph()
            g.parse(data=ttl_data, format="turtle")
            for triple in g:
                self._graph.add(triple)
            return True
        except Exception as e:
            st.error(f"Upload error: {e}")
            return False

    def get_graph(self) -> Graph:
        return self._graph

    def clear(self):
        self._graph = Graph()
        if OXIGRAPH_AVAILABLE:
            self._store = ox.Store()

    def serialize(self, fmt="turtle") -> str:
        return self._graph.serialize(format=fmt)

    def triple_count(self) -> int:
        return len(self._graph)


# ============================================================
# SESSION STATE — Single source of truth
# ============================================================
def init_session():
    defaults = {
        "store": OxigraphStore(),
        "file_registry": [],
        "current_uri": None,
        "nav_history": [],
        "chat_history": [],
        "saved_queries": [],
        "diff_snapshot": None,      # For RDF Diff
        "diff_snapshot_label": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

store: OxigraphStore = st.session_state.store


# ============================================================
# FILE MANAGER
# ============================================================
class FileManager:
    STORAGE = "rdf_registry.json"

    @staticmethod
    def add(filename, ttl_data, triple_count, file_size, namespace, file_id):
        record = {
            "id": file_id,
            "filename": filename,
            "upload_time": datetime.now().isoformat(),
            "triple_count": triple_count,
            "file_size": file_size,
            "namespace": namespace,
            "ttl_preview": ttl_data[:2000],
        }
        st.session_state.file_registry.append(record)
        FileManager._persist()
        return file_id

    @staticmethod
    def delete(file_id):
        st.session_state.file_registry = [
            f for f in st.session_state.file_registry if f["id"] != file_id
        ]
        FileManager._persist()

    @staticmethod
    def get_all():
        return sorted(st.session_state.file_registry,
                      key=lambda x: x["upload_time"], reverse=True)

    @staticmethod
    def _persist():
        try:
            with open(FileManager.STORAGE, "w") as f:
                json.dump(st.session_state.file_registry, f, indent=2)
        except Exception:
            pass


# ============================================================
# DATA CONVERTER  (CSV / XLSX / JSON → Turtle)
# ============================================================
class DataToRDFConverter:
    def __init__(self, namespace="http://example.org/data#", prefix="ex"):
        self.namespace = namespace if namespace.endswith(("#", "/")) else namespace + "#"
        self.prefix = prefix

    def clean(self, text) -> str:
        if pd.isna(text) or text is None:
            return ""
        return str(text).strip().replace("\\", "\\\\").replace('"', '\\"')

    def is_date(self, val) -> bool:
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
            try:
                datetime.strptime(str(val), fmt)
                return True
            except ValueError:
                continue
        return False

    def format_date(self, val) -> str:
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
            try:
                return datetime.strptime(str(val), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return str(val)

    def load_file(self, uploaded_file):
        name = uploaded_file.name.lower()
        try:
            if name.endswith(".csv"):
                return pd.read_csv(uploaded_file)
            elif name.endswith((".xlsx", ".xls")):
                return pd.read_excel(uploaded_file)
            elif name.endswith(".json"):
                return pd.read_json(uploaded_file)
        except Exception as e:
            st.error(f"Could not load {uploaded_file.name}: {e}")
        return None

    def convert(self, df: pd.DataFrame, id_col: str,
                ignore_cols=None, source_id=None) -> tuple[str, int]:
        ignore_cols = ignore_cols or []
        out = io.StringIO()
        out.write(f"@prefix {self.prefix}: <{self.namespace}> .\n")
        out.write("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n")
        out.write("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n")

        count = 0
        df = df.reset_index(drop=True)
        entity_type = re.sub(r"[^a-zA-Z0-9]", "", id_col.strip().title())

        for idx, row in df.iterrows():
            val = row[id_col]
            if pd.isna(val) or not str(val).strip():
                continue
            subj = f"{self.prefix}:{entity_type}_{re.sub(r'[^a-zA-Z0-9_]', '_', str(val).strip())}_{idx}"
            lines = [f"{subj} a {self.prefix}:{entity_type}"]
            count += 1

            if source_id:
                lines.append(f'    {self.prefix}:sourceFile "{source_id}"')

            for col in df.columns:
                if col == id_col or col in ignore_cols:
                    continue
                v = row[col]
                if pd.isna(v) or str(v).strip() == "":
                    continue
                pred = f"{self.prefix}:{re.sub(r'[^a-zA-Z0-9_]', '_', col.strip())}"
                if isinstance(v, float):
                    lines.append(f'    {pred} "{v}"^^xsd:float')
                elif isinstance(v, int):
                    lines.append(f'    {pred} "{v}"^^xsd:integer')
                elif self.is_date(v):
                    lines.append(f'    {pred} "{self.format_date(v)}"^^xsd:date')
                else:
                    lines.append(f'    {pred} "{self.clean(v)}"')
                count += 1

            out.write(" ;\n".join(lines) + " .\n\n")

        return out.getvalue(), count


# ============================================================
# RDF NAVIGATOR CORE
# ============================================================
class RDFNavigator:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.namespaces = {str(p): str(n) for p, n in graph.namespaces()}

    def shorten(self, uri) -> str:
        uri = str(uri)
        for pfx, ns in self.namespaces.items():
            if uri.startswith(ns):
                return f"{pfx}:{uri[len(ns):]}" if pfx else uri[len(ns):]
        return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]

    def expand(self, uri: str) -> str:
        if ":" in uri and not uri.startswith("http"):
            try:
                pfx, local = uri.split(":", 1)
                if pfx in self.namespaces:
                    return self.namespaces[pfx] + local
            except Exception:
                pass
        return uri

    def sparql(self, query: str) -> tuple[list, str | None]:
        try:
            return list(self.graph.query(query)), None
        except Exception as e:
            return [], str(e)

    def get_triples(self, uri: str) -> list:
        ref = URIRef(uri)
        result = []
        for s, p, o in self.graph.triples((ref, None, None)):
            result.append(("out", s, p, o))
        for s, p, o in self.graph.triples((None, None, ref)):
            result.append(("in", s, p, o))
        return result

    def search(self, keyword: str) -> list[str]:
        safe = re.sub(r'["\\\n]', "", keyword)
        res, _ = self.sparql(f"""
        SELECT DISTINCT ?s WHERE {{
            ?s ?p ?o .
            FILTER(regex(str(?s), "{safe}", "i") || regex(str(?o), "{safe}", "i"))
        }} LIMIT 30""")
        return [str(r[0]) for r in res]

    def all_resources(self, limit=100) -> list[str]:
        uris = set()
        for s, _, o in self.graph:
            if isinstance(s, URIRef): uris.add(str(s))
            if isinstance(o, URIRef): uris.add(str(o))
        return sorted(list(uris))[:limit]


# ============================================================
# FEATURE 1 CONTINUED — GRAPH STATS DASHBOARD
# ============================================================
def get_graph_stats(graph: Graph) -> dict:
    stats = {"total_triples": len(graph), "classes": set(), "predicates": set(),
             "instances": set(), "literal_count": 0}
    for s, p, o in graph:
        stats["predicates"].add(str(p))
        if isinstance(s, URIRef):
            stats["instances"].add(str(s))
        if p == RDF.type and isinstance(o, URIRef):
            stats["classes"].add(str(o))
        if isinstance(o, Literal):
            stats["literal_count"] += 1
    return {
        "Total Triples": stats["total_triples"],
        "Unique Classes": len(stats["classes"]),
        "Unique Predicates": len(stats["predicates"]),
        "Resource Nodes": len(stats["instances"]),
        "Literal Values": stats["literal_count"],
    }


# ============================================================
# FEATURE 2 — EXPORT (CSV / EXCEL)
# ============================================================
def df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

def df_to_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()

def export_buttons(df: pd.DataFrame, label: str = "results"):
    """Render CSV + Excel download buttons under any dataframe."""
    c1, c2 = st.columns([1, 1])
    with c1:
        st.download_button(
            f"⬇️ Download CSV",
            data=df_to_csv(df),
            file_name=f"{label}_{datetime.now().strftime('%H%M%S')}.csv",
            mime="text/csv",
            key=f"csv_{label}_{random.randint(0,99999)}"
        )
    with c2:
        if EXCEL_AVAILABLE:
            st.download_button(
                f"⬇️ Download Excel",
                data=df_to_excel(df),
                file_name=f"{label}_{datetime.now().strftime('%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"xlsx_{label}_{random.randint(0,99999)}"
            )
        else:
            st.caption("Install `openpyxl` for Excel export")


# ============================================================
# FEATURE 3 — MULTI-HOP PATH EXPLORER
# ============================================================
def find_paths(graph: Graph, uri1: str, uri2: str, max_hops: int = 3) -> list[dict]:
    """
    BFS-based multi-hop path finder between two resources.
    Returns a list of path dicts with hop count and steps.
    """
    if max_hops < 1 or max_hops > 4:
        max_hops = 3

    visited = set()
    # Each queue item: (current_uri, path_so_far)
    queue = [{"uri": uri1, "path": [{"node": uri1, "via": None}]}]
    found_paths = []

    while queue:
        item = queue.pop(0)
        curr = item["uri"]
        path = item["path"]

        if len(path) - 1 > max_hops:
            continue
        if curr in visited:
            continue
        visited.add(curr)

        # Find all neighbours
        ref = URIRef(curr)
        neighbours = []
        for s, p, o in graph.triples((ref, None, None)):
            if isinstance(o, URIRef):
                neighbours.append((str(o), str(p), "→"))
        for s, p, o in graph.triples((None, None, ref)):
            if isinstance(s, URIRef):
                neighbours.append((str(s), str(p), "←"))

        for nbr_uri, pred, direction in neighbours:
            new_path = path + [{"node": nbr_uri, "via": pred, "direction": direction}]
            if nbr_uri == uri2:
                found_paths.append({
                    "hops": len(new_path) - 1,
                    "path": new_path
                })
                if len(found_paths) >= 10:
                    return found_paths
            else:
                queue.append({"uri": nbr_uri, "path": new_path})

    return found_paths


# ============================================================
# FEATURE 4 — SAVED SPARQL QUERIES
# ============================================================
def save_query(name: str, query: str):
    for q in st.session_state.saved_queries:
        if q["name"] == name:
            q["query"] = query
            q["updated"] = datetime.now().isoformat()
            return
    st.session_state.saved_queries.append({
        "name": name,
        "query": query,
        "created": datetime.now().isoformat()
    })

def delete_saved_query(name: str):
    st.session_state.saved_queries = [
        q for q in st.session_state.saved_queries if q["name"] != name
    ]


# ============================================================
# FEATURE 5 — RDF DIFF TOOL
# ============================================================
def compute_diff(graph_a: Graph, graph_b: Graph) -> dict:
    """
    Compares two rdflib graphs.
    Returns triples only in A (removed), only in B (added), and common.
    """
    set_a = set((str(s), str(p), str(o)) for s, p, o in graph_a)
    set_b = set((str(s), str(p), str(o)) for s, p, o in graph_b)
    return {
        "added": list(set_b - set_a),
        "removed": list(set_a - set_b),
        "common": len(set_a & set_b),
    }


# ============================================================
# FEATURE 6 — AUTO ONTOLOGY GENERATOR
# ============================================================
def generate_ontology(graph: Graph, namespace: str, prefix: str) -> str:
    """
    Analyzes the loaded graph and auto-generates a basic OWL ontology:
    - Declares all detected rdf:type values as owl:Class
    - Declares all predicates as owl:DatatypeProperty or owl:ObjectProperty
    - Infers rdfs:domain from usage patterns
    """
    ns = namespace if namespace.endswith(("#", "/")) else namespace + "#"
    classes = defaultdict(set)      # class → set of instances
    obj_props = defaultdict(set)    # predicate → set of (domain_class, range_class)
    data_props = defaultdict(set)   # predicate → set of domain_classes
    instance_types = {}             # instance_uri → class_uri

    for s, p, o in graph:
        if p == RDF.type and isinstance(o, URIRef):
            classes[str(o)].add(str(s))
            instance_types[str(s)] = str(o)

    for s, p, o in graph:
        if p == RDF.type:
            continue
        pred = str(p)
        domain_cls = instance_types.get(str(s))
        if isinstance(o, URIRef):
            range_cls = instance_types.get(str(o))
            obj_props[pred].add((domain_cls, range_cls))
        elif isinstance(o, Literal):
            data_props[pred].add(domain_cls)

    out = io.StringIO()
    out.write(f"@prefix {prefix}: <{ns}> .\n")
    out.write("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
    out.write("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n")
    out.write("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n")
    out.write(f"<{ns}> a owl:Ontology ;\n")
    out.write(f'    rdfs:label "Auto-generated Ontology" ;\n')
    out.write(f'    rdfs:comment "Generated by RDF Navigator v4 on {datetime.now().strftime("%Y-%m-%d")}" .\n\n')

    # Classes
    out.write("# ── Classes ─────────────────────────────────\n")
    for cls_uri, instances in sorted(classes.items()):
        short = cls_uri.split("#")[-1] if "#" in cls_uri else cls_uri.split("/")[-1]
        out.write(f"<{cls_uri}> a owl:Class ;\n")
        out.write(f'    rdfs:label "{short}" ;\n')
        out.write(f'    rdfs:comment "Detected {len(instances)} instance(s)" .\n\n')

    # Object Properties
    out.write("# ── Object Properties ───────────────────────\n")
    for pred, pairs in sorted(obj_props.items()):
        short = pred.split("#")[-1] if "#" in pred else pred.split("/")[-1]
        out.write(f"<{pred}> a owl:ObjectProperty ;\n")
        out.write(f'    rdfs:label "{short}" ;\n')
        domains = set(d for d, r in pairs if d)
        ranges  = set(r for d, r in pairs if r)
        if domains:
            out.write(f"    rdfs:domain <{list(domains)[0]}> ;\n")
        if ranges:
            out.write(f"    rdfs:range <{list(ranges)[0]}> ;\n")
        out.write(f'    rdfs:comment "Detected object property" .\n\n')

    # Datatype Properties
    out.write("# ── Datatype Properties ─────────────────────\n")
    for pred, doms in sorted(data_props.items()):
        short = pred.split("#")[-1] if "#" in pred else pred.split("/")[-1]
        out.write(f"<{pred}> a owl:DatatypeProperty ;\n")
        out.write(f'    rdfs:label "{short}" ;\n')
        valid_doms = [d for d in doms if d]
        if valid_doms:
            out.write(f"    rdfs:domain <{valid_doms[0]}> ;\n")
        out.write("    rdfs:range xsd:string .\n\n")

    return out.getvalue()


# ============================================================
# AI — GROQ GraphRAG (Free, No billing risk)
# Get free API key at https://console.groq.com
# ============================================================
class GraphRAG:
    """
    Converts natural language to SPARQL using Groq (free tier).
    Model: llama3-70b-8192 — fast, accurate, completely free.
    No credit card required at console.groq.com
    """
    # Best free models available on Groq (in preference order)
    PREFERRED_MODELS = [
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]

    def __init__(self, api_key: str, graph: Graph):
        self.client = None
        self.model_name = "Not configured"
        self.graph = graph

        if not GROQ_AVAILABLE:
            self.model_name = "groq package not installed"
            return
        if not api_key:
            self.model_name = "No API key provided"
            return
        try:
            self.client = Groq(api_key=api_key)
            # Test connection by listing models
            models = self.client.models.list()
            available = [m.id for m in models.data]
            self.model_name = next(
                (m for m in self.PREFERRED_MODELS if m in available),
                available[0] if available else "llama3-70b-8192"
            )
        except Exception as e:
            self.model_name = f"Error: {e}"
            self.client = None

    def _schema(self) -> str:
        """
        Returns a summary of the graph schema for use in AI prompts.
        graph.query() returns a result object directly — NOT a tuple.
        """
        try:
            res = self.graph.query(
                "SELECT DISTINCT ?type ?p WHERE { ?s a ?type . ?s ?p ?o . } LIMIT 80"
            )
            lines = []
            for r in res:
                try:
                    lines.append(f"Type: {r.type} -> Property: {r.p}")
                except Exception:
                    pass
            return "\n".join(lines) if lines else "No schema detected yet — import data first."
        except Exception as e:
            return f"Schema unavailable: {e}"

    def ask(self, question: str, history: list = None) -> tuple[str, str]:
        if not self.client:
            return "NO_MODEL", f"Groq not configured: {self.model_name}"

        ctx = "\n".join(
            f"{'USER' if m['role']=='user' else 'AI'}: {m['content']}"
            for m in (history or [])[-5:]
        )
        prompt = f"""You are a SPARQL expert. Convert the question to a valid SPARQL SELECT query.

GRAPH SCHEMA:
{self._schema()}

CONVERSATION HISTORY:
{ctx}

QUESTION: "{question}"

RULES:
1. Return ONLY the SPARQL query — no markdown, no explanation, no backticks.
2. Use prefixes found in the schema.
3. Always use SELECT queries.
4. Keep queries simple and valid."""

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a SPARQL expert. Return ONLY valid SPARQL queries with no explanation or markdown."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,   # Low temperature = more deterministic SPARQL
                max_tokens=512,
            )
            q = response.choices[0].message.content
            # Clean up any markdown the model might add anyway
            q = q.replace("```sparql", "").replace("```sql", "").replace("```", "").strip()
            return "SUCCESS", q
        except Exception as e:
            return "ERROR", str(e)


# ============================================================
# REASONING ENGINE
# ============================================================
class ReasoningEngine:
    def run(self, graph: Graph, ontology_ttl: str) -> tuple[bool, any]:
        if not OWLRL_AVAILABLE:
            return False, "Install owlrl: `pip install owlrl`"
        try:
            g = Graph()
            for t in graph:
                g.add(t)
            initial = len(g)
            g.parse(data=ontology_ttl, format="turtle")
            owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(g)
            new_triples = len(g) - initial
            if new_triples > 0:
                for t in g:
                    graph.add(t)
            return True, new_triples
        except Exception as e:
            return False, str(e)


# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown("""
<div style="text-align:center; padding: 8px 0 4px 0;">
    <h2 style="margin:0; font-size:1.3rem; font-weight:700;">🕸️ RDF Navigator</h2>
    <p style="margin:4px 0 0 0; font-size:0.75rem; opacity:0.8;">Knowledge Graph Explorer</p>
</div>
""", unsafe_allow_html=True)
st.sidebar.caption(f"Backend: **{store.get_backend_name().upper()}** ({'✅' if OXIGRAPH_AVAILABLE else '⚠️ rdflib fallback'})")
st.sidebar.divider()

# Namespace
st.sidebar.subheader("Data Namespace")

st.markdown("""
<style>
section[data-testid="stSidebar"] .stExpander,
section[data-testid="stSidebar"] .stExpander * {
    color: black !important;
}
</style>
""", unsafe_allow_html=True)
#this is the CSS for the example 
with st.sidebar.expander("📝 View Examples"):
    st.markdown("""
    **Namespace URI:** The unique "web address" for your data entities.
    * *Format:* `http://{domain}/{project}#`
    * *Example:* `http://mycompany.com/finance#`
    
    **Prefix:** A short nickname for the namespace.
    * *Example:* `fin` (for finance)
    """)



custom_ns = st.sidebar.text_input("Namespace URI", value="http://example.org/data#")
custom_prefix = st.sidebar.text_input("Prefix", value="ex")
if not custom_ns.endswith(("#", "/")):
    custom_ns += "#"
converter = DataToRDFConverter(namespace=custom_ns, prefix=custom_prefix)

st.sidebar.divider()

# AI
st.sidebar.subheader("AI Assistant (Groq)")
env_key = os.getenv("GROQ_API_KEY", "")
groq_key = env_key or st.sidebar.text_input(
    "Groq API Key", type="password",
    help="Get FREE key at https://console.groq.com — no credit card needed!"
)
if env_key:
    st.sidebar.success("🔑 Key loaded from .env")
elif groq_key:
    st.sidebar.success("🔑 Groq API Key entered")
else:
    st.sidebar.info("💡 Get a free key at console.groq.com")

st.sidebar.divider()

# Controls
if st.sidebar.button("🗑️ Clear All Data", type="primary"):
    store.clear()
    st.session_state.file_registry = []
    st.session_state.current_uri = None
    st.session_state.nav_history = []
    st.session_state.diff_snapshot = None
    st.rerun()

ttl_export = store.serialize("turtle")
st.sidebar.download_button(
    "⬇️ Export Full Graph (TTL)",
    data=ttl_export.encode("utf-8"),
    file_name=f"graph_export_{datetime.now().strftime('%Y%m%d_%H%M')}.ttl",
    mime="text/turtle"
)

# ============================================================
# MAIN
# ============================================================
st.markdown("""
<div class="app-header">
    <div>
        <h1>🕸️ RDF Navigator</h1>
        <p>Embedded Oxigraph &nbsp;·&nbsp; No server required &nbsp;·&nbsp; Deploy anywhere</p>
    </div>
</div>
""", unsafe_allow_html=True)

graph = store.get_graph()
navigator = RDFNavigator(graph)
# Pass the store so GraphRAG always gets the latest graph
groq_key = groq_key if "groq_key" in dir() else env_key
rag = GraphRAG(groq_key, store.get_graph()) if groq_key else None
reasoner = ReasoningEngine()

# Show AI status in sidebar
if rag and rag.client:
    st.sidebar.success(f"🤖 AI Ready: {rag.model_name}")
elif groq_key and rag:
    st.sidebar.error(f"❌ AI Error: {rag.model_name}")

# ============================================================
# STATS DASHBOARD (always visible at top)
# ============================================================
st.markdown(
    "<p style='font-size:0.78rem; font-weight:600; color:#1565C0; "
    "text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>"
    "📊 Graph Statistics</p>",
    unsafe_allow_html=True
)
stats = get_graph_stats(graph)
cols = st.columns(len(stats))
for col, (label, val) in zip(cols, stats.items()):
    col.metric(label, f"{val:,}")

st.divider()

# ============================================================
# DATA IMPORT
# ============================================================
with st.expander("📥 Smart Data Import — CSV · XLSX · JSON", expanded=store.triple_count() == 0):
    uploaded = st.file_uploader(
        "Upload files", type=["csv", "xlsx", "xls", "json"],
        accept_multiple_files=True
    )
    if uploaded:
        for file in uploaded:
            st.markdown(f"#### 📄 `{file.name}`")
            try:
                file.seek(0)
                df = converter.load_file(file)
            except Exception as e:
                st.error(str(e))
                continue
            if df is None:
                continue

            c1, c2 = st.columns([2, 1])
            with c1:
                st.dataframe(df.head(5), use_container_width=True)
            with c2:
                default_idx = next(
                    (i for i, c in enumerate(df.columns)
                     if any(k in c.lower() for k in ["id", "code", "key", "name"])), 0
                )
                id_col = st.selectbox("Primary Key", df.columns,
                                      index=default_idx, key=f"id_{file.name}")
                ignore = st.multiselect("Ignore Columns",
                                        [c for c in df.columns if c != id_col],
                                        key=f"ign_{file.name}")
                if st.button(f"🚀 Import", key=f"imp_{file.name}", type="primary"):
                    fid = hashlib.md5(f"{file.name}{datetime.now()}".encode()).hexdigest()
                    ttl, count = converter.convert(df, id_col, ignore, fid)
                    if store.upload_ttl(ttl):
                        FileManager.add(file.name, ttl, count,
                                        getattr(file, "size", len(ttl)),
                                        custom_ns, fid)
                        st.success(f"✅ Imported {count:,} triples!")
                        st.rerun()

# ============================================================
# TABS
# ============================================================
tabs = st.tabs([
    "🔍  Explorer",
    "📊  SPARQL",
    "🛤️  Paths",
    "🤖  AI Chat",
    "🕸️  Graph",
    "🔀  Diff",
    "🧬  Ontology",
    "📁  Files"
])

tab_explorer, tab_sparql, tab_path, tab_ai, tab_graph, tab_diff, tab_onto, tab_files = tabs


# ──────────────────────────────────────────────────────────────
# TAB: EXPLORER
# ──────────────────────────────────────────────────────────────
with tab_explorer:
    st.subheader("Browse the Knowledge Graph")

    kw = st.text_input("🔎 Keyword Search", placeholder="e.g., 'Australia', 'Customer_01'")
    if kw:
        matches = navigator.search(kw)
        if matches:
            sel = st.selectbox("Results:", matches, format_func=navigator.shorten)
            if st.button("Navigate →"):
                st.session_state.current_uri = sel
                st.session_state.nav_history.append(sel)
                st.rerun()
        else:
            st.warning("No matches found.")

    st.divider()

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        uri_val = st.text_input("Full URI or prefix (e.g., ex:MyNode)",
                                value=st.session_state.current_uri or "")
    with c2:
        st.write(""); st.write("")
        if st.button("🔍 Go"):
            st.session_state.current_uri = navigator.expand(uri_val)
            st.session_state.nav_history.append(st.session_state.current_uri)
            st.rerun()
    with c3:
        st.write(""); st.write("")
        if st.button("🎲 Random"):
            pool = navigator.all_resources()
            if pool:
                pick = random.choice(pool)
                st.session_state.current_uri = pick
                st.session_state.nav_history.append(pick)
                st.rerun()

    all_res = navigator.all_resources(50)
    if all_res:
        chosen = st.selectbox("Or pick from list:",
                              [""] + all_res,
                              format_func=lambda x: navigator.shorten(x) if x else "— select —")
        if chosen and chosen != st.session_state.current_uri:
            st.session_state.current_uri = chosen
            st.session_state.nav_history.append(chosen)
            st.rerun()

    if st.session_state.current_uri:
        uri = st.session_state.current_uri
        triples = navigator.get_triples(uri)
        st.divider()
        st.subheader(f"📌 {navigator.shorten(uri)}")
        st.caption(f"`{uri}`")

        if triples:
            st.success(f"{len(triples)} triples found")
            outgoing = [(s, p, o) for d, s, p, o in triples if d == "out"]
            incoming = [(s, p, o) for d, s, p, o in triples if d == "in"]

            c1, c2 = st.columns(2)
            with c1:
                st.info(f"➡️ Outgoing ({len(outgoing)})")
                rows = []
                for s, p, o in outgoing:
                    rows.append({
                        "Predicate": navigator.shorten(p),
                        "Object": navigator.shorten(o),
                        "_uri": str(o)
                    })
                if rows:
                    df_out = pd.DataFrame(rows)
                    st.dataframe(df_out[["Predicate", "Object"]], use_container_width=True)
                    uri_opts = [r["_uri"] for r in rows if isinstance(o, URIRef) or r["_uri"].startswith("http")]
                    if uri_opts:
                        pick_o = st.selectbox("Visit object:", uri_opts,
                                              format_func=navigator.shorten, key="pick_out")
                        if st.button("Go →", key="go_out"):
                            st.session_state.current_uri = pick_o
                            st.session_state.nav_history.append(pick_o)
                            st.rerun()
                    export_buttons(df_out[["Predicate", "Object"]], "outgoing")

            with c2:
                st.success(f"⬅️ Incoming ({len(incoming)})")
                rows_in = []
                for s, p, o in incoming:
                    rows_in.append({
                        "Subject": navigator.shorten(s),
                        "Predicate": navigator.shorten(p),
                        "_uri": str(s)
                    })
                if rows_in:
                    df_in = pd.DataFrame(rows_in)
                    st.dataframe(df_in[["Subject", "Predicate"]], use_container_width=True)
                    uri_in_opts = [r["_uri"] for r in rows_in if r["_uri"].startswith("http")]
                    if uri_in_opts:
                        pick_i = st.selectbox("Visit subject:", uri_in_opts,
                                              format_func=navigator.shorten, key="pick_in")
                        if st.button("Go →", key="go_in"):
                            st.session_state.current_uri = pick_i
                            st.session_state.nav_history.append(pick_i)
                            st.rerun()
                    export_buttons(df_in[["Subject", "Predicate"]], "incoming")
        else:
            st.warning("No triples found for this URI.")

    # Navigation History
    history = list(dict.fromkeys(reversed(st.session_state.nav_history)))[:6]
    if history:
        st.divider()
        st.caption("🕓 Recent Navigation")
        hcols = st.columns(len(history))
        for i, (hcol, res) in enumerate(zip(hcols, history)):
            with hcol:
                if st.button(navigator.shorten(res)[:20], key=f"h_{i}"):
                    st.session_state.current_uri = res
                    st.rerun()


# ──────────────────────────────────────────────────────────────
# TAB: SPARQL SUITE  (with Saved Queries — Feature 4)
# ──────────────────────────────────────────────────────────────
with tab_sparql:
    st.subheader("SPARQL Query Suite")

    # Predefined queries
    with st.expander("🔗 Find Connections Between Two Resources", expanded=True):
        c1, c2 = st.columns(2)
        r1 = c1.text_input("Resource 1 URI / prefix", key="conn_r1")
        r2 = c2.text_input("Resource 2 URI / prefix", key="conn_r2")
        if st.button("Find", key="conn_btn"):
            u1, u2 = navigator.expand(r1), navigator.expand(r2)
            q = f"""
            SELECT DISTINCT ?connection_type ?path ?intermediate WHERE {{
                {{ <{u1}> ?path <{u2}> . BIND("direct" AS ?connection_type) BIND("—" AS ?intermediate) }}
                UNION
                {{ <{u1}> ?p1 ?intermediate . ?intermediate ?p2 <{u2}> .
                   FILTER(?intermediate != <{u1}> && ?intermediate != <{u2}>)
                   BIND("2-hop" AS ?connection_type)
                   BIND(CONCAT(STR(?p1), " → ", STR(?p2)) AS ?path) }}
                UNION
                {{ <{u1}> ?p1 ?mid . <{u2}> ?p2 ?mid .
                   FILTER(?p1 = ?p2)
                   BIND("shared node" AS ?connection_type)
                   BIND(STR(?p1) AS ?path) BIND(STR(?mid) AS ?intermediate) }}
            }} ORDER BY ?connection_type
            """
            res, err = navigator.sparql(q)
            if err:
                st.error(err)
            elif res:
                df = pd.DataFrame([{
                    "Type": str(r[0]),
                    "Path": navigator.shorten(str(r[1])),
                    "Intermediate": navigator.shorten(str(r[2]))
                } for r in res])
                st.dataframe(df, use_container_width=True)
                export_buttons(df, "connections")
            else:
                st.info("No connections found.")

    with st.expander("⚠️ Priority & Risk Analysis"):
        atype = st.selectbox("Type", ["High Priority Incidents", "Module Risk Assessment"])
        if st.button("Run", key="risk_btn"):
            if atype == "High Priority Incidents":
                q = f"""
                PREFIX ex: <{custom_ns}>
                SELECT ?incident ?customer ?severity ?priority ?status WHERE {{
                    ?incident a ex:IncidentReport .
                    ?incident ex:belongsToCustomer ?customer .
                    ?incident ex:severity ?severity .
                    ?incident ex:priority ?priority .
                    ?incident ex:status ?status .
                    FILTER(?priority IN ("P0","P1"))
                }} ORDER BY ?priority"""
                cols_names = ["Incident", "Customer", "Severity", "Priority", "Status"]
            else:
                q = f"""
                PREFIX ex: <{custom_ns}>
                SELECT ?module (COUNT(?incident) AS ?count) WHERE {{
                    ?incident a ex:IncidentReport .
                    ?incident ex:mentionsFunction ?module .
                }} GROUP BY ?module ORDER BY DESC(?count)"""
                cols_names = ["Module", "Incident Count"]
            res, err = navigator.sparql(q)
            if err:
                st.error(err)
            elif res:
                df = pd.DataFrame([[navigator.shorten(str(v)) for v in r] for r in res],
                                  columns=cols_names)
                st.dataframe(df, use_container_width=True)
                export_buttons(df, "risk")
            else:
                st.info("No data found.")

    st.divider()

    # Custom SPARQL editor + Saved Queries
    st.subheader("⚡ Custom SPARQL Editor")

    # Load saved query
    if st.session_state.saved_queries:
        saved_names = ["— new query —"] + [q["name"] for q in st.session_state.saved_queries]
        selected_saved = st.selectbox("Load saved query:", saved_names, key="load_saved")
        if selected_saved != "— new query —":
            saved_q = next(q for q in st.session_state.saved_queries if q["name"] == selected_saved)
            default_q = saved_q["query"]
            if st.button("🗑️ Delete this saved query"):
                delete_saved_query(selected_saved)
                st.rerun()
        else:
            default_q = "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 25"
    else:
        default_q = "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 25"

    custom_q = st.text_area("SPARQL Query:", value=default_q, height=160)

    save_col, run_col = st.columns([2, 1])
    with save_col:
        save_name = st.text_input("Save as (optional name):", key="save_name_input")
        if st.button("💾 Save Query") and save_name:
            save_query(save_name, custom_q)
            st.success(f"Saved as '{save_name}'")

    with run_col:
        st.write("")
        run_q = st.button("▶️ Run", type="primary")

    if run_q:
        res, err = navigator.sparql(custom_q)
        if err:
            st.error(f"SPARQL error: {err}")
        elif res:
            try:
                cols_q = [str(v) for v in res[0].labels]
            except Exception:
                cols_q = [f"col_{i}" for i in range(len(res[0]))]
            df_q = pd.DataFrame([[str(v) for v in r] for r in res], columns=cols_q)
            st.dataframe(df_q, use_container_width=True)
            st.caption(f"{len(df_q)} rows")
            export_buttons(df_q, "custom_query")
        else:
            st.info("No results.")


# ──────────────────────────────────────────────────────────────
# TAB: MULTI-HOP PATH EXPLORER  (Feature 3)
# ──────────────────────────────────────────────────────────────
with tab_path:
    st.subheader("🛤️ Multi-Hop Path Explorer")
    st.caption("Discover how two resources are connected across multiple relationship hops.")

    pc1, pc2, pc3 = st.columns([2, 2, 1])
    with pc1:
        path_r1 = st.text_input("Start Resource (URI or prefix)", key="path_r1",
                                placeholder="e.g., ex:Customer_A")
    with pc2:
        path_r2 = st.text_input("End Resource (URI or prefix)", key="path_r2",
                                placeholder="e.g., ex:Module_B")
    with pc3:
        max_hops = st.selectbox("Max Hops", [1, 2, 3, 4], index=1)

    if st.button("🔍 Find All Paths", type="primary", key="path_btn"):
        if path_r1 and path_r2:
            u1 = navigator.expand(path_r1)
            u2 = navigator.expand(path_r2)
            with st.spinner("Searching paths..."):
                paths = find_paths(graph, u1, u2, max_hops)
            if paths:
                st.success(f"Found {len(paths)} path(s) between the two resources")
                for i, p in enumerate(paths, 1):
                    with st.expander(f"Path {i} — {p['hops']} hop(s)"):
                        steps = []
                        for j, step in enumerate(p["path"]):
                            node_label = navigator.shorten(step["node"])
                            if step["via"]:
                                pred_label = navigator.shorten(step["via"])
                                direction = step.get("direction", "→")
                                steps.append({
                                    "Step": j,
                                    "Node": node_label,
                                    "Via Predicate": pred_label,
                                    "Direction": direction
                                })
                            else:
                                steps.append({
                                    "Step": j,
                                    "Node": node_label,
                                    "Via Predicate": "— start —",
                                    "Direction": ""
                                })
                        df_path = pd.DataFrame(steps)
                        st.dataframe(df_path, use_container_width=True)

                        # Visual path string
                        path_str = ""
                        for step in p["path"]:
                            if step["via"]:
                                path_str += f" **{step.get('direction','→')}[{navigator.shorten(step['via'])}]→** "
                            path_str += f"`{navigator.shorten(step['node'])}`"
                        st.markdown(path_str)
            else:
                st.warning(f"No paths found within {max_hops} hops.")
        else:
            st.warning("Enter both resources.")


# ──────────────────────────────────────────────────────────────
# TAB: AI ASSISTANT  (Feature — Gemini GraphRAG)
# ──────────────────────────────────────────────────────────────
with tab_ai:
    st.subheader("🤖 Natural Language → SPARQL")

    hdr1, hdr2 = st.columns([1, 3])
    with hdr1:
        if st.button("🧹 Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
    with hdr2:
        if st.session_state.chat_history:
            report = f"RDF Navigator Session Report — {datetime.now()}\n{'='*50}\n"
            for m in st.session_state.chat_history:
                report += f"\n[{m['role'].upper()}] {m['content']}\n"
                if "sql" in m:
                    report += f"SPARQL:\n{m['sql']}\n"
            st.download_button("📥 Download Chat Report", report,
                               file_name=f"session_{datetime.now().strftime('%H%M')}.txt")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sql" in msg:
                st.code(msg["sql"], language="sparql")
            if "df" in msg and msg["df"] is not None:
                st.dataframe(msg["df"])

    if prompt := st.chat_input("Ask anything about your graph..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            if not rag:
                st.error("Add your free Groq API Key in the sidebar (get one at console.groq.com).")
            else:
                with st.spinner("🤔 Generating SPARQL query..."):
                    # Always use latest graph for schema detection
                    rag.graph = store.get_graph()  # Refresh graph reference
                    status, sparql_code = rag.ask(prompt, st.session_state.chat_history)

                if status == "NO_MODEL":
                    st.error("⚠️ " + sparql_code)
                elif status == "ERROR":
                    st.error(f"❌ Groq API Error: {sparql_code}")
                    st.info("Common causes: invalid Groq API key, rate limit hit, or no internet. Get a free key at console.groq.com")
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": f"API Error: {sparql_code}"})
                elif status == "SUCCESS":
                    # Show the generated query
                    with st.expander("🔍 Generated SPARQL Query", expanded=False):
                        st.code(sparql_code, language="sparql")

                    # Validate it looks like a SELECT query
                    if not sparql_code.strip().upper().startswith("SELECT"):
                        st.warning("⚠️ AI returned a non-SELECT query. Trying to run it anyway...")

                    # Execute the query
                    res, err = navigator.sparql(sparql_code)

                    if err:
                        # Try to give helpful error context
                        reply = f"I generated this query but it failed to execute. Error: {err}"
                        st.error(f"❌ Query Error: {err}")
                        st.info("💡 Tip: Try rephrasing your question or check if data is imported.")
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": reply, "sql": sparql_code})

                    elif res and len(res) > 0:
                        try:
                            cols_ai = [str(v) for v in res[0].labels]
                        except Exception:
                            cols_ai = [f"col_{i}" for i in range(len(res[0]))]
                        df_ai = pd.DataFrame([[str(v) for v in r] for r in res], columns=cols_ai)

                        reply = f"Found **{len(df_ai)}** result(s) for your query."
                        st.success(f"✅ {reply}")
                        st.dataframe(df_ai, use_container_width=True)
                        export_buttons(df_ai, "ai_result")
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": reply,
                            "sql": sparql_code,
                            "df": df_ai
                        })
                    else:
                        reply = "The query ran successfully but returned no results. This could mean the data doesn't match the query conditions, or the graph is empty."
                        st.info(f"ℹ️ {reply}")
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": reply, "sql": sparql_code})


# ──────────────────────────────────────────────────────────────
# TAB: GRAPH VISUALIZATION  (Fixed + Dynamic Colors)
# ──────────────────────────────────────────────────────────────
with tab_graph:
    if not PYVIS_AVAILABLE:
        st.error("Install PyVis: `pip install pyvis`")
    elif not st.session_state.current_uri:
        st.info("Select a resource in the Explorer tab first.")
    else:
        curr = st.session_state.current_uri
        gc1, gc2, gc3 = st.columns([1, 1, 2])
        show_lit = gc1.checkbox("Show Literals", True)
        hier_lay = gc2.checkbox("Tree Layout", False)

        triples_v = navigator.get_triples(curr)
        preds = list(set(
            [navigator.shorten(str(t[2])) for t in triples_v if t[0] == "out"] +
            [navigator.shorten(str(t[2])) for t in triples_v if t[0] == "in"]
        ))
        palette = ["#FFB3BA","#BAE1FF","#BAFFC9","#FFFFBA","#FFDFBA",
                   "#D5BAFF","#BFFCC6","#C9C9FF","#FFD6A5","#CAFFBF"]
        color_map = {p: palette[i % len(palette)] for i, p in enumerate(preds)}

        with gc3:
            legend = " ".join(
                f"<span style='background:{c};padding:2px 8px;border-radius:4px;font-size:11px'>{p}</span>"
                for p, c in list(color_map.items())[:8]
            )
            st.markdown(legend, unsafe_allow_html=True)

        net = Network(height="600px", width="100%", bgcolor="white", font_color="black")
        net.add_node(curr, label=navigator.shorten(curr),
                     color="#333333", size=35, shape="ellipse")

        cnt = 0
        for direction, s, p, o in triples_v:
            if cnt >= 80:
                break
            pred_lbl = navigator.shorten(str(p))
            nc = color_map.get(pred_lbl, "#aaaaaa")

            if direction == "out":
                if isinstance(o, Literal):
                    if not show_lit:
                        continue
                    nid = f"lit_{abs(hash(str(o)))}"
                    net.add_node(nid, label=str(o)[:40], color=nc, size=12, shape="box")
                    net.add_edge(curr, nid, label=pred_lbl, color=nc)
                elif isinstance(o, URIRef):
                    nid = str(o)
                    net.add_node(nid, label=navigator.shorten(nid), color=nc, size=20)
                    net.add_edge(curr, nid, label=pred_lbl, color=nc)
            else:  # "in"
                if isinstance(s, URIRef):
                    nid = str(s)
                    net.add_node(nid, label=navigator.shorten(nid), color=nc, size=20)
                    net.add_edge(nid, curr, label=pred_lbl, color=nc)
            cnt += 1

        opts = ('{"layout":{"hierarchical":{"enabled":true,"direction":"UD","sortMethod":"directed"}}}'
                if hier_lay else
                '{"physics":{"forceAtlas2Based":{"gravitationalConstant":-50,"springLength":120},'
                '"minVelocity":0.75,"solver":"forceAtlas2Based"}}')
        net.set_options(opts)

        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False,
                                             suffix=".html", encoding="utf-8") as f:
                net.save_graph(f.name)
                tmp = f.name
            with open(tmp, "r", encoding="utf-8") as f:
                html = f.read()
            os.unlink(tmp)
            components.html(html, height=620)
        except Exception as e:
            st.error(f"Visualization error: {e}")


# ──────────────────────────────────────────────────────────────
# TAB: RDF DIFF  (Feature 5)
# ──────────────────────────────────────────────────────────────
with tab_diff:
    st.subheader("🔀 RDF Diff Tool")
    st.caption("Take a snapshot of your current graph, import more data, then compare to see what changed.")

    d1, d2 = st.columns(2)
    with d1:
        st.markdown("**Step 1 — Take a Snapshot**")
        snap_label = st.text_input("Snapshot label", value=f"snapshot_{datetime.now().strftime('%H%M%S')}")
        if st.button("📸 Take Snapshot", type="primary"):
            snap_graph = Graph()
            for t in graph:
                snap_graph.add(t)
            st.session_state.diff_snapshot = snap_graph
            st.session_state.diff_snapshot_label = snap_label
            st.success(f"Snapshot taken: {len(snap_graph)} triples saved as '{snap_label}'")

        if st.session_state.diff_snapshot:
            st.info(f"Current snapshot: **{st.session_state.diff_snapshot_label}** "
                    f"({len(st.session_state.diff_snapshot)} triples)")

    with d2:
        st.markdown("**Step 2 — Compare**")
        st.caption("Import more data (use Import section above), then click Compare.")
        if st.button("🔍 Compare to Snapshot", type="primary"):
            if not st.session_state.diff_snapshot:
                st.warning("Take a snapshot first.")
            else:
                diff = compute_diff(st.session_state.diff_snapshot, graph)
                st.success(f"Common triples: **{diff['common']:,}**")
                if diff["added"]:
                    st.markdown(f"#### ✅ Added ({len(diff['added'])} triples)")
                    df_add = pd.DataFrame(diff["added"], columns=["Subject", "Predicate", "Object"])
                    df_add = df_add.applymap(navigator.shorten)
                    st.dataframe(df_add, use_container_width=True)
                    export_buttons(df_add, "diff_added")
                else:
                    st.info("No new triples added.")

                if diff["removed"]:
                    st.markdown(f"#### ❌ Removed ({len(diff['removed'])} triples)")
                    df_rem = pd.DataFrame(diff["removed"], columns=["Subject", "Predicate", "Object"])
                    df_rem = df_rem.applymap(navigator.shorten)
                    st.dataframe(df_rem, use_container_width=True)
                    export_buttons(df_rem, "diff_removed")
                else:
                    st.info("No triples removed.")

    # Upload TTL to compare directly
    st.divider()
    st.markdown("**Or compare two TTL files directly:**")
    ttl_a = st.file_uploader("TTL File A (baseline)", type=["ttl"], key="diff_a")
    ttl_b = st.file_uploader("TTL File B (new version)", type=["ttl"], key="diff_b")
    if ttl_a and ttl_b and st.button("Compare Files"):
        ga, gb = Graph(), Graph()
        ga.parse(data=ttl_a.read().decode(), format="turtle")
        gb.parse(data=ttl_b.read().decode(), format="turtle")
        diff = compute_diff(ga, gb)
        c1, c2, c3 = st.columns(3)
        c1.metric("Common", diff["common"])
        c2.metric("➕ Added", len(diff["added"]))
        c3.metric("➖ Removed", len(diff["removed"]))
        if diff["added"]:
            df_fa = pd.DataFrame(diff["added"], columns=["Subject", "Predicate", "Object"])
            st.markdown("**Added:**")
            st.dataframe(df_fa, use_container_width=True)
            export_buttons(df_fa, "file_diff_added")
        if diff["removed"]:
            df_fr = pd.DataFrame(diff["removed"], columns=["Subject", "Predicate", "Object"])
            st.markdown("**Removed:**")
            st.dataframe(df_fr, use_container_width=True)
            export_buttons(df_fr, "file_diff_removed")


# ──────────────────────────────────────────────────────────────
# TAB: AUTO-ONTOLOGY GENERATOR  (Feature 6)
# ──────────────────────────────────────────────────────────────

def build_ontology_graph_html(onto_ttl: str) -> str:
    """
    Parses the generated ontology TTL and builds an interactive
    PyVis network showing:
      - Classes        → large ellipse nodes  (blue)
      - Object Props   → medium diamond nodes (orange)
      - Datatype Props → small box nodes      (green)
      - rdfs:subClassOf edges (red dashed)
      - rdfs:domain / rdfs:range edges (grey)
    """
    if not PYVIS_AVAILABLE:
        return ""

    g = Graph()
    try:
        g.parse(data=onto_ttl, format="turtle")
    except Exception:
        return ""

    net = Network(
        height="580px", width="100%",
        bgcolor="#1a1a2e",           # dark background looks great for ontologies
        font_color="white",
        directed=True
    )
    net.set_options("""
    {
        "layout": {
            "hierarchical": {
                "enabled": true,
                "direction": "UD",
                "sortMethod": "directed",
                "levelSeparation": 120,
                "nodeSpacing": 160
            }
        },
        "physics": { "enabled": false },
        "edges": {
            "smooth": { "type": "cubicBezier" },
            "arrows": { "to": { "enabled": true, "scaleFactor": 0.8 } }
        }
    }
    """)

    added_nodes = set()

    def short(uri):
        uri = str(uri)
        return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]

    def add_node_once(uri, label, color, shape, size):
        if uri not in added_nodes:
            net.add_node(uri, label=label, color=color,
                         shape=shape, size=size, font={"size": 13})
            added_nodes.add(uri)

    OWL_NS   = "http://www.w3.org/2002/07/owl#"
    RDFS_NS  = "http://www.w3.org/2000/01/rdf-schema#"

    # --- Pass 1: Add typed nodes ---
    for s, p, o in g:
        s_str, o_str = str(s), str(o)

        if str(p) == f"{RDF}type":
            if o_str == f"{OWL_NS}Class":
                add_node_once(s_str, short(s_str), "#4a90d9", "ellipse", 28)
            elif o_str == f"{OWL_NS}ObjectProperty":
                add_node_once(s_str, short(s_str), "#f5a623", "diamond", 20)
            elif o_str == f"{OWL_NS}DatatypeProperty":
                add_node_once(s_str, short(s_str), "#7ed321", "box", 16)

    # --- Pass 2: Add relationship edges ---
    for s, p, o in g:
        s_str, p_str, o_str = str(s), str(p), str(o)

        if isinstance(o, Literal):
            continue

        if p_str == f"{RDFS_NS}subClassOf":
            # Ensure both nodes exist
            add_node_once(s_str, short(s_str), "#4a90d9", "ellipse", 28)
            add_node_once(o_str, short(o_str), "#4a90d9", "ellipse", 28)
            net.add_edge(s_str, o_str,
                         label="subClassOf",
                         color="#e74c3c",
                         dashes=True,
                         width=2)

        elif p_str == f"{RDFS_NS}domain":
            add_node_once(o_str, short(o_str), "#4a90d9", "ellipse", 28)
            if s_str in added_nodes:
                net.add_edge(s_str, o_str,
                             label="domain",
                             color="#aaaaaa",
                             width=1)

        elif p_str == f"{RDFS_NS}range":
            add_node_once(o_str, short(o_str), "#4a90d9", "ellipse", 28)
            if s_str in added_nodes:
                net.add_edge(s_str, o_str,
                             label="range",
                             color="#9b59b6",
                             width=1)

    # If nothing was added, return empty
    if not added_nodes:
        return ""

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".html", encoding="utf-8"
        ) as f:
            net.save_graph(f.name)
            tmp = f.name
        with open(tmp, "r", encoding="utf-8") as f:
            html = f.read()
        os.unlink(tmp)
        return html
    except Exception:
        return ""


with tab_onto:
    st.subheader("🧬 Auto-Ontology Generator")
    st.caption("Analyzes your loaded graph and generates a formal OWL ontology automatically.")

    if store.triple_count() == 0:
        st.warning("⚠️ Import some data first — the graph is currently empty.")
    else:
        # --- Controls row ---
        oc1, oc2, oc3 = st.columns([1, 1, 1])
        with oc1:
            onto_ns = st.text_input("Ontology Namespace", value=custom_ns)
        with oc2:
            onto_prefix = st.text_input("Ontology Prefix", value=custom_prefix)
        with oc3:
            st.write("")
            st.write("")
            if st.button("🧬 Generate Ontology", type="primary", use_container_width=True):
                current_graph = store.get_graph()
                if len(current_graph) == 0:
                    st.error("Graph appears empty — try re-importing your data.")
                else:
                    with st.spinner(f"Analyzing {len(current_graph):,} triples..."):
                        try:
                            onto_ttl = generate_ontology(current_graph, onto_ns, onto_prefix)
                            st.session_state["generated_ontology"] = onto_ttl
                            st.success(f"✅ Ontology generated from {len(current_graph):,} triples!")
                        except Exception as e:
                            st.error(f"Generation failed: {e}")

        # --- Output section with sub-tabs ---
        if "generated_ontology" in st.session_state:
            onto_out = st.session_state["generated_ontology"]

            st.divider()

            # Action buttons row
            btn1, btn2, btn3 = st.columns([1, 1, 1])
            with btn1:
                st.download_button(
                    "⬇️ Download Ontology (.ttl)",
                    data=onto_out.encode("utf-8"),
                    file_name=f"ontology_{datetime.now().strftime('%Y%m%d_%H%M')}.ttl",
                    mime="text/turtle",
                    use_container_width=True
                )
            with btn2:
                if st.button("📥 Load into Graph", use_container_width=True):
                    if store.upload_ttl(onto_out):
                        st.success("✅ Ontology loaded into graph!")
                        st.rerun()
            with btn3:
                # Quick stats about the ontology
                onto_g = Graph()
                try:
                    onto_g.parse(data=onto_out, format="turtle")
                    n_classes = sum(1 for _, _, o in onto_g if str(o) == "http://www.w3.org/2002/07/owl#Class")
                    n_obj     = sum(1 for _, _, o in onto_g if str(o) == "http://www.w3.org/2002/07/owl#ObjectProperty")
                    n_data    = sum(1 for _, _, o in onto_g if str(o) == "http://www.w3.org/2002/07/owl#DatatypeProperty")
                    st.info(f"📦 {n_classes} Classes · {n_obj} Object Props · {n_data} Data Props")
                except Exception:
                    pass

            st.divider()

            # Sub-tabs: TTL view vs Graph view
            view_ttl, view_graph = st.tabs(["📄 TTL Source", "🕸️ Ontology Graph"])

            # --- TTL Source sub-tab ---
            with view_ttl:
                st.caption("Raw Turtle representation of your ontology:")
                st.code(
                    onto_out[:4000] +
                    ("\n\n# ... (truncated — download for full ontology)" if len(onto_out) > 4000 else ""),
                    language="turtle"
                )

            # --- Ontology Graph sub-tab ---
            with view_graph:
                if not PYVIS_AVAILABLE:
                    st.error("Install PyVis to use graph view: `pip install pyvis`")
                else:
                    st.caption(
                        "Visual map of your ontology. "
                        "🔵 Blue = Class · 🟠 Orange = Object Property · 🟢 Green = Datatype Property · "
                        "🔴 Red dashed = subClassOf"
                    )

                    with st.spinner("Building ontology graph..."):
                        onto_html = build_ontology_graph_html(onto_out)

                    if onto_html:
                        components.html(onto_html, height=600)
                    else:
                        st.warning(
                            "Could not build graph — this usually means the ontology has "
                            "no class hierarchy or property relationships yet. "
                            "Try importing richer data or loading the ontology back into "
                            "the graph and running the Reasoner first."
                        )


# ──────────────────────────────────────────────────────────────
# TAB: FILES & REASONING
# ──────────────────────────────────────────────────────────────
with tab_files:
    files_sub, reasoning_sub = st.tabs(["📁 Files", "🧠 Reasoning"])

    with files_sub:
        files = FileManager.get_all()
        if files:
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Files", len(files))
            mc2.metric("Total Triples", f"{sum(f.get('triple_count',0) for f in files):,}")
            mc3.metric("Total Size", f"{sum(f.get('file_size',0) for f in files):,} bytes")
            st.divider()
            for fi in files:
                t = datetime.fromisoformat(fi["upload_time"]).strftime("%Y-%m-%d %H:%M")
                with st.expander(f"📄 {fi['filename']} — {t}"):
                    fc1, fc2 = st.columns([3, 1])
                    with fc1:
                        st.write(f"**ID:** `{fi['id'][:12]}...`")
                        st.write(f"**Namespace:** {fi.get('namespace','—')}")
                        st.write(f"**Triples:** {fi.get('triple_count',0):,}")
                        if st.checkbox("Show TTL Preview", key=f"p_{fi['id']}"):
                            st.code(fi.get("ttl_preview", "")[:2000], language="turtle")
                    with fc2:
                        if st.button("🗑️ Remove", key=f"d_{fi['id']}", type="secondary"):
                            FileManager.delete(fi["id"])
                            st.rerun()
        else:
            st.info("No files imported yet.")

    with reasoning_sub:
        st.subheader("🧠 Semantic Reasoning (OWL/RDFS)")
        if not OWLRL_AVAILABLE:
            st.error("Install owlrl: `pip install owlrl`")
        else:
            rc1, rc2 = st.columns([1, 1])
            with rc1:
                st.caption("Define rules in Turtle:")
                default_rules = f"""@prefix ex: <{custom_ns}> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

# Example: define class hierarchy
ex:Oceania rdfs:subClassOf ex:GlobalMarket .
ex:NorthAmerica rdfs:subClassOf ex:GlobalMarket .
"""
                rules_ttl = st.text_area("Ontology Rules", value=default_rules, height=250)
            with rc2:
                st.caption("Apply rules to infer new facts:")
                if st.button("🚀 Run Reasoner", type="primary"):
                    with st.spinner("Reasoning..."):
                        ok, result = reasoner.run(graph, rules_ttl)
                    if ok:
                        if result > 0:
                            st.success(f"✅ Inferred {result} new facts!")
                            st.balloons()
                        else:
                            st.warning("Rules applied — no new facts inferred.")
                    else:
                        st.error(f"Failed: {result}")

# ============================================================
st.divider()
st.caption("🕸️ RDF Navigator v4 · Oxigraph · Streamlit Cloud Ready · https://github.com/Vc0108/rdf-navigator")
