"""disclosure.tools web server — UAP Eigenforensics
Full-featured server with PDF ingestion, reference graphs, gap reports,
meme factory, leaderboard, and AI Search integration.
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import time
import os
import sys
import tempfile
import numpy as np
from typing import Optional

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gap_detector.spectral_engine import SpectralEngine
from gap_detector.ingestion import ingest_bytes, ingest_text, ingest_file, ingest_pdf
from gap_detector.graph import build_document_graph, build_corpus_graph
from gap_detector.report import generate_report, GapReport as GapReportObj
from meme_factory import generate_meme, auto_generate_memes, get_all_templates, MEME_TEMPLATES
from leaderboard import Leaderboard
from integration import evez_integration
from monitor import foia_monitor

app = FastAPI(
    title="disclosure.tools",
    version="2.0.0",
    description="UAP/FOIA eigenforensics gap detection. Negative eigenvalues = missing records.",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Initialize leaderboard
leaderboard = Leaderboard(
    data_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaderboard_data")
)

# Ensure meme output directory exists
MEME_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_memes")
os.makedirs(MEME_DIR, exist_ok=True)


# ─── Health & Status ───────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "disclosure.tools", "version": "2.0.0", "ts": int(time.time())}


@app.get("/")
def index():
    return FileResponse("static_index.html")


# ─── Core Analysis ─────────────────────────────────────────

@app.post("/api/v1/analyze")
async def analyze_documents(file: UploadFile = File(...)):
    """Upload a file (JSON, PDF, TXT) and get eigenforensics analysis."""
    content = await file.read()
    filename = file.filename or "upload.json"

    try:
        docs = ingest_bytes(content, filename)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Ingestion failed: {str(e)}")

    if not docs:
        raise HTTPException(status_code=422, detail="No documents extracted from file")

    # Run spectral engine
    corpus = [d.to_corpus_entry() for d in docs]
    engine = SpectralEngine(operator="evez666")
    engine.load_corpus(corpus)
    spectral_result = engine.analyze()

    # Build reference graph (for structural analysis)
    graph = build_corpus_graph(corpus)
    graph_info = graph.to_dict()

    # Generate full gap report using spectral engine eigenvalues
    # (SpectralEngine's similarity-based adjacency produces meaningful negative eigenvalues)
    eigenvalues = np.array(spectral_result.get("eigenvalues", []))
    section_titles = [d.title for d in docs]
    report = generate_report(
        eigenvalues=eigenvalues,
        n_documents=len(docs),
        n_sections=sum(len(d.sections) for d in docs),
        operator="evez666",
        section_titles=section_titles,
        context_text=" ".join(d.text[:200] for d in docs),
    )

    # Auto-generate memes for high/critical findings
    findings_dicts = [f.to_dict() for f in report.findings]
    memes = auto_generate_memes(findings_dicts)
    meme_results = []
    for meme in memes:
        meme_path = os.path.join(MEME_DIR, f"{meme.meme_id}.svg")
        with open(meme_path, "w") as f:
            f.write(meme.svg_content)
        meme_results.append({"meme_id": meme.meme_id, "caption": meme.caption,
                              "template": meme.template_id, "svg_path": meme_path})

    return {
        "spectral": spectral_result,
        "graph": graph_info,
        "report": report.to_dict(),
        "report_text": report.to_text(),
        "memes": meme_results,
    }


@app.get("/api/v1/demo")
def demo_analysis():
    """Run eigenforensics on the built-in AARO sample corpus."""
    sample_docs = [
        {"id": "AARO-2024-001", "text": "Unidentified anomalous phenomena assessment office report", "date": "2024-03"},
        {"id": "AARO-2024-002", "text": "UAP incident report redacted Naval aviation encounter", "date": "2024-03"},
        {"id": "AARO-2024-003", "text": "FOIA release AARO historical records review", "date": "2024-06"},
        {"id": "AARO-2024-004", "text": "Department of Defense statement on UAP classification", "date": "2024-06"},
        {"id": "AARO-2024-005", "text": "National Archives UAP document release partial", "date": "2024-09"},
        {"id": "AARO-2024-006", "text": "Pentagon UAP task force historical analysis volumes 1-9", "date": "2024-09"},
    ]
    engine = SpectralEngine(operator="evez666")
    engine.load_corpus(sample_docs)
    return engine.analyze()


# ─── Text Analysis (no file upload) ────────────────────────

@app.post("/api/v1/analyze/text")
async def analyze_text(
    text: str = Form(...),
    title: str = Form("Untitled"),
    date: str = Form(""),
):
    """Submit text directly for analysis (no file upload needed).
    Splits single text into sections for section-level spectral analysis."""
    doc = ingest_text(text, title=title, date=date)
    
    # Build corpus from sections of the document itself
    # This enables eigenforensic detection of internal gaps/redactions
    sections = text.split('\n\n')
    sections = [s.strip() for s in sections if len(s.strip()) > 20]
    
    if len(sections) >= 2:
        # Section-level spectral analysis
        corpus_entries = []
        for i, sec in enumerate(sections):
            corpus_entries.append({
                "id": f"{title}_sec{i}",
                "text": sec,
                "title": f"Section {i+1}"
            })
        engine = SpectralEngine(operator="evez666")
        engine.load_corpus(corpus_entries)
    else:
        engine = SpectralEngine(operator="evez666")
        engine.load_corpus([doc.to_corpus_entry()])
    
    spectral_result = engine.analyze()

    # Generate report
    eigenvalues = np.array(spectral_result.get("eigenvalues", []))
    report = generate_report(
        eigenvalues=eigenvalues,
        n_documents=1,
        n_sections=len(doc.sections),
        operator="evez666",
        section_titles=doc.sections[:5],
        context_text=text[:500],
    )

    findings = [f.to_dict() for f in report.findings]
    memes = auto_generate_memes(findings)

    return {
        "spectral": spectral_result,
        "report": report.to_dict(),
        "report_text": report.to_text(),
        "memes": [{"meme_id": m.meme_id, "caption": m.caption} for m in memes],
    }


# ─── Reference Graph ───────────────────────────────────────

@app.post("/api/v1/graph")
async def build_graph(file: UploadFile = File(...)):
    """Build and return reference graph from uploaded documents."""
    content = await file.read()
    filename = file.filename or "upload.json"

    docs = ingest_bytes(content, filename)
    corpus = [d.to_corpus_entry() for d in docs]

    # Document-level graph
    doc_graph = build_corpus_graph(corpus)
    doc_info = doc_graph.to_dict()
    adjacency = doc_graph.build_adjacency()

    # Section-level graph
    sec_graph = build_document_graph(corpus)
    sec_info = sec_graph.to_dict()
    sec_adjacency = sec_graph.build_adjacency()

    result = {
        "document_graph": doc_info,
        "section_graph": sec_info,
        "orphan_nodes": doc_graph.find_orphan_nodes(),
        "dangling_refs": doc_graph.find_dangling_refs(),
        "n_documents": len(docs),
        "n_sections_total": sum(len(d.sections) for d in docs),
    }

    if adjacency.size > 0:
        eigenvalues = np.linalg.eigvalsh(adjacency)
        result["eigenvalues"] = [round(float(v), 4) for v in eigenvalues]

    return result


# ─── Gap Report ─────────────────────────────────────────────

@app.post("/api/v1/report")
async def generate_gap_report(file: UploadFile = File(...)):
    """Generate a detailed gap report with findings and meme triggers."""
    content = await file.read()
    filename = file.filename or "upload.json"

    docs = ingest_bytes(content, filename)
    corpus = [d.to_corpus_entry() for d in docs]

    graph = build_corpus_graph(corpus)
    adjacency = graph.build_adjacency()

    if adjacency.size > 0:
        eigenvalues = np.linalg.eigvalsh(adjacency)
    else:
        eigenvalues = np.array([0.0])

    section_titles = [d.title for d in docs]
    report = generate_report(
        eigenvalues=eigenvalues,
        n_documents=len(docs),
        n_sections=sum(len(d.sections) for d in docs),
        operator="evez666",
        section_titles=section_titles,
        context_text=" ".join(d.text[:200] for d in docs),
    )

    return {
        "report": report.to_dict(),
        "text": report.to_text(),
        "summary": report.summary,
    }


# ─── Meme Factory ──────────────────────────────────────────

@app.get("/api/v1/memes/templates")
def list_meme_templates():
    """List all available meme templates."""
    return {"templates": get_all_templates()}


@app.post("/api/v1/memes/generate")
async def generate_meme_endpoint(
    caption: str = Form(...),
    template_id: str = Form("gap_detected"),
    top_override: str = Form(""),
    bottom_override: str = Form(""),
):
    """Generate a meme with custom text."""
    meme = generate_meme(
        caption=caption,
        template_id=template_id,
        top_override=top_override,
        bottom_override=bottom_override,
    )

    # Save SVG
    svg_path = os.path.join(MEME_DIR, f"{meme.meme_id}.svg")
    with open(svg_path, "w") as f:
        f.write(meme.svg_content)

    # Save HTML
    html_path = os.path.join(MEME_DIR, f"{meme.meme_id}.html")
    with open(html_path, "w") as f:
        f.write(meme.html_content)

    return {
        "meme_id": meme.meme_id,
        "caption": meme.caption,
        "template_id": meme.template_id,
        "svg_path": svg_path,
        "html_path": html_path,
    }


@app.get("/api/v1/memes/{meme_id}")
def get_meme(meme_id: str):
    """Retrieve a generated meme."""
    svg_path = os.path.join(MEME_DIR, f"{meme_id}.svg")
    html_path = os.path.join(MEME_DIR, f"{meme_id}.html")

    if os.path.exists(svg_path):
        return FileResponse(svg_path, media_type="image/svg+xml")
    elif os.path.exists(html_path):
        return FileResponse(html_path, media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail=f"Meme {meme_id} not found")


# ─── Leaderboard ───────────────────────────────────────────

@app.post("/api/v1/leaderboard/register")
def register_researcher(name: str = Query(...)):
    """Register a new researcher on the leaderboard."""
    researcher = leaderboard.register_researcher(name)
    return researcher.to_dict()


@app.get("/api/v1/leaderboard")
def get_leaderboard(limit: int = Query(50, ge=1, le=200)):
    """Get the FOIA researcher leaderboard."""
    return {
        "leaderboard": leaderboard.get_leaderboard(limit),
        "stats": leaderboard.get_stats(),
    }


@app.get("/api/v1/leaderboard/{researcher_id}")
def get_researcher(researcher_id: str):
    """Get researcher details."""
    result = leaderboard.get_researcher(researcher_id)
    if not result:
        raise HTTPException(status_code=404, detail="Researcher not found")
    return result


@app.post("/api/v1/leaderboard/{researcher_id}/foia")
def submit_foia_request(
    researcher_id: str,
    agency: str = Query(...),
    description: str = Query(...),
    date_filed: str = Query(""),
):
    """Record a FOIA request submission for a researcher."""
    req = leaderboard.record_foia_request(researcher_id, agency, description, date_filed)
    return req.to_dict()


@app.post("/api/v1/leaderboard/{researcher_id}/gap-closure")
def record_gap_closure(researcher_id: str, count: int = Query(1, ge=1)):
    """Record gap closures attributed to a researcher."""
    leaderboard.record_gap_closure(researcher_id, count)
    result = leaderboard.get_researcher(researcher_id)
    return result or {"error": "Researcher not found"}


# ─── Batch Analysis ────────────────────────────────────────

@app.post("/api/v1/analyze/batch")
async def batch_analyze(files: list[UploadFile] = File(...)):
    """Analyze multiple files at once."""
    results = []
    for file in files:
        content = await file.read()
        try:
            docs = ingest_bytes(content, file.filename or "upload")
            corpus = [d.to_corpus_entry() for d in docs]
            engine = SpectralEngine(operator="evez666")
            engine.load_corpus(corpus)
            result = engine.analyze()
            results.append({"filename": file.filename, "result": result})
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})

    return {"results": results, "total_files": len(files)}


# ─── EVEZ-OS Integration ───────────────────────────────────

@app.get("/api/v1/integration/services")
async def get_service_status():
    """Health-check all EVEZ-OS services."""
    results = await evez_integration.check_all_services()
    online = sum(1 for s in results.values() if s["status"] == "online")
    return {"services": results, "online": online, "total": len(results)}


@app.post("/api/v1/integration/cross-analyze")
async def cross_service_analysis(file: UploadFile = File(...)):
    """Analyze document + generate cross-service insights from EVEZ-OS."""
    content = await file.read()
    filename = file.filename or "upload.json"

    docs = ingest_bytes(content, filename)
    corpus = [d.to_corpus_entry() for d in docs]

    # Run spectral analysis
    engine = SpectralEngine(operator="evez666")
    engine.load_corpus(corpus)
    spectral_result = engine.analyze()

    # Generate gap report
    eigenvalues = np.array(spectral_result.get("eigenvalues", []))
    report = generate_report(
        eigenvalues=eigenvalues,
        n_documents=len(docs),
        n_sections=sum(len(d.sections) for d in docs),
        operator="evez666",
        section_titles=[d.title for d in docs],
        context_text=" ".join(d.text[:200] for d in docs),
    )

    # Cross-service insights
    insights = await evez_integration.generate_cross_insights(report.to_dict())

    # Check service health
    services = await evez_integration.check_all_services()

    return {
        "spectral": spectral_result,
        "report": report.to_dict(),
        "cross_insights": [i.to_dict() for i in insights],
        "services": services,
    }


@app.get("/api/v1/integration/search-gaps")
async def search_for_gaps(query: str = Query("aaro_reports")):
    """Use AI Search to find documents that fill detected gaps."""
    results = await evez_integration.search_for_gaps(query)
    return {"query": query, "results": results, "count": len(results)}


# ─── FOIA Monitor ─────────────────────────────────────────────

@app.get("/api/v1/monitor/sources")
def get_monitor_sources():
    """Get all configured FOIA monitoring sources."""
    return {"sources": foia_monitor.get_sources()}


@app.post("/api/v1/monitor/check")
async def check_all_sources():
    """Check all enabled FOIA sources for new content."""
    results = await foia_monitor.check_all()
    changes = sum(1 for r in results if r.changes)
    return {
        "results": [r.to_dict() for r in results],
        "sources_checked": len(results),
        "changes_detected": changes,
    }


@app.post("/api/v1/monitor/check/{source_id}")
async def check_single_source(source_id: str):
    """Check a single FOIA source for new content."""
    result = await foia_monitor.check_source(source_id)
    if not result:
        raise HTTPException(status_code=404, detail="Source not found")
    return result.to_dict()


@app.post("/api/v1/monitor/add-source")
def add_monitor_source(name: str = Query(...), url: str = Query(...)):
    """Add a new FOIA monitoring source."""
    source = foia_monitor.add_source(name, url)
    return source.to_dict()


@app.get("/api/v1/monitor/history")
def get_monitor_history(limit: int = Query(50, ge=1, le=200)):
    """Get FOIA monitoring check history."""
    return {"history": foia_monitor.get_history(limit)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8087)
