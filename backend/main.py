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

def _guess_molecule(req: PredictRequest) -> str:
    """Try to guess molecule from filename hints in CSV data (best effort)."""
    return "caffeine"  # default fallback
