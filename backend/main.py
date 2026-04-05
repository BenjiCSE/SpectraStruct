"""
FastAPI backend for DiamondHacks spectra-to-structure demo.
Serves fixture data in demo_mode (default), or runs live MIST inference.
"""
import json
import base64
import os
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np

app = FastAPI(title="DiamondHacks Spectra API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FIXTURES_DIR = Path(__file__).parent.parent / "data" / "fixtures"
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

class PredictRequest(BaseModel):
    nmr_csv: Optional[str] = None   # base64-encoded CSV: ppm,intensity
    ms_csv: Optional[str] = None    # base64-encoded CSV: mz,intensity
    ir_csv: Optional[str] = None    # base64-encoded CSV: wavenumber,intensity
    top_k: int = 5
    demo_molecule: Optional[str] = None  # e.g. "caffeine" — forces fixture lookup

class Candidate(BaseModel):
    smiles: str
    score: float
    rank: int
    valid: bool
    conformer_sdf: Optional[str] = None

class PredictResponse(BaseModel):
    candidates: List[Candidate]
    modalities_used: List[str]
    warning: Optional[str] = None
    demo_mode: bool = False

@app.get("/health")
def health():
    return {"status": "ok", "demo_mode": DEMO_MODE}

@app.get("/fixtures")
def list_fixtures():
    """List available demo molecules."""
    fixtures = [f.stem for f in FIXTURES_DIR.glob("*.json")]
    return {"molecules": sorted(fixtures)}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    modalities_used = []
    if req.nmr_csv: modalities_used.append("nmr")
    if req.ms_csv:  modalities_used.append("ms")
    if req.ir_csv:  modalities_used.append("ir")

    if not modalities_used:
        raise HTTPException(400, "At least one spectrum must be provided.")

    warning = None
    if len(modalities_used) < 3:
        missing = [m for m in ["nmr", "ms", "ir"] if m not in modalities_used]
        warning = f"{', '.join(missing).upper()} not provided; results may be less accurate."

    # Demo mode: return fixture data
    if DEMO_MODE or req.demo_molecule:
        mol_name = req.demo_molecule or _guess_molecule(req)
        fixture_path = FIXTURES_DIR / f"{mol_name}.json"
        if fixture_path.exists():
            with open(fixture_path) as f:
                fixture = json.load(f)
            # Return the variant matching available modalities
            variant_key = "_".join(sorted(modalities_used)) if modalities_used else "nmr"
            candidates_data = fixture.get("variants", {}).get(variant_key,
                              fixture.get("candidates", []))
            candidates = [Candidate(**c) for c in candidates_data[:req.top_k]]
            return PredictResponse(
                candidates=candidates,
                modalities_used=modalities_used,
                warning=warning,
                demo_mode=True,
            )
        # Fallback: return first available fixture
        all_fixtures = list(FIXTURES_DIR.glob("*.json"))
        if all_fixtures:
            with open(all_fixtures[0]) as f:
                fixture = json.load(f)
            candidates = [Candidate(**c) for c in fixture.get("candidates", [])[:req.top_k]]
            return PredictResponse(candidates=candidates, modalities_used=modalities_used,
                                   warning=warning, demo_mode=True)

    # Live mode: MIST inference (placeholder — wire in after hackathon setup)
    raise HTTPException(501, "Live inference not yet configured. Set DEMO_MODE=true.")

def _parse_peaks(text: str) -> List[tuple]:
    import csv as _csv
    peaks = []
    for row in _csv.reader(io.StringIO(text)):
        if len(row) >= 2:
            try:
                peaks.append((float(row[0]), float(row[1])))
            except ValueError:
                pass
    return peaks


def _bin(peaks: List[tuple], lo: float, hi: float, n: int):
    import numpy as np
    v = np.zeros(n, dtype=np.float64)
    for x, y in peaks:
        if lo <= x < hi:
            v[min(int((x - lo) / (hi - lo) * n), n - 1)] = max(v[min(int((x - lo) / (hi - lo) * n), n - 1)], y)
    mx = v.max()
    if mx > 0:
        v /= mx
    return v


def _cos(a, b) -> float:
    import numpy as np
    d = float(np.dot(a, b))
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    return d / (na * nb) if na > 0 and nb > 0 else 0.0


def _guess_molecule(req: PredictRequest) -> str:
    """Match uploaded spectra against fixture library by cosine similarity."""
    import csv as _csv

    nmr_text = ms_text = None
    if req.nmr_csv:
        try: nmr_text = base64.b64decode(req.nmr_csv).decode("utf-8")
        except Exception: pass
    if req.ms_csv:
        try: ms_text = base64.b64decode(req.ms_csv).decode("utf-8")
        except Exception: pass

    q_nmr = _bin(_parse_peaks(nmr_text), -2.0, 14.0, 1024) if nmr_text else None
    q_ms = _bin(_parse_peaks(ms_text), 0.0, 2000.0, 2048) if ms_text else None

    if q_nmr is None and q_ms is None:
        return "caffeine"

    best_name, best_score = "caffeine", -1.0

    for fp in FIXTURES_DIR.glob("*.json"):
        name = fp.stem
        sim, n = 0.0, 0

        if q_nmr is not None:
            ref_path = SPECTRA_DIR / f"{name}_nmr.csv"
            if ref_path.exists():
                with open(ref_path) as fh:
                    ref = [(float(r[0]), float(r[1])) for r in _csv.reader(fh) if len(r) >= 2 and r[0].replace('.','',1).replace('-','',1).isdigit()]
                if ref:
                    sim += _cos(q_nmr, _bin(ref, -2.0, 14.0, 1024))
                    n += 1

        if q_ms is not None:
            ref_path = SPECTRA_DIR / f"{name}_ms.csv"
            if ref_path.exists():
                with open(ref_path) as fh:
                    ref = [(float(r[0]), float(r[1])) for r in _csv.reader(fh) if len(r) >= 2 and r[0].replace('.','',1).replace('-','',1).isdigit()]
                if ref:
                    sim += _cos(q_ms, _bin(ref, 0.0, 2000.0, 2048))
                    n += 1

        if n > 0 and sim / n > best_score:
            best_score = sim / n
            best_name = name

    logger.info("Guessed molecule: %s (similarity=%.4f)", best_name, best_score)
    return best_name
