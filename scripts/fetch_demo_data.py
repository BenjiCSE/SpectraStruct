#!/usr/bin/env python3
"""
fetch_demo_data.py
==================
Downloads real experimental spectra for 20 demo molecules from:
  - MassBank Europe (MS spectra) via GitHub flat files
  - NMRShiftDB2 (NMR spectra) via SourceForge SDF dump

Outputs:
  data/raw/massbank/   — raw MassBank .txt files for each molecule
  data/raw/nmrshiftdb/ — extracted NMR peak CSVs
  data/fixtures/spectra/<name>_ms.csv
  data/fixtures/spectra/<name>_nmr.csv
"""
import os
import re
import csv
import json
import time
import requests
from pathlib import Path

ROOT = Path(__file__).parent.parent
RAW_MB   = ROOT / "data" / "raw" / "massbank"
RAW_NMR  = ROOT / "data" / "raw" / "nmrshiftdb"
SPEC_OUT = ROOT / "data" / "fixtures" / "spectra"

for d in [RAW_MB, RAW_NMR, SPEC_OUT]:
    d.mkdir(parents=True, exist_ok=True)

# ── 20 demo molecules ──────────────────────────────────────────────────────────
DEMO_MOLECULES = [
    {"name": "caffeine",       "smiles": "Cn1cnc2c1c(=O)n(c(=O)n2C)C",             "inchikey": "RYYVLZVUVIJVGH-UHFFFAOYSA-N"},
    {"name": "aspirin",        "smiles": "CC(=O)Oc1ccccc1C(=O)O",                   "inchikey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"},
    {"name": "ibuprofen",      "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",              "inchikey": "HEFNNWSXXWATRW-UHFFFAOYSA-N"},
    {"name": "acetaminophen",  "smiles": "CC(=O)Nc1ccc(O)cc1",                       "inchikey": "RZVAJINKPMORJF-UHFFFAOYSA-N"},
    {"name": "dopamine",       "smiles": "NCCc1ccc(O)c(O)c1",                        "inchikey": "VYFYYTLLBUKUHU-UHFFFAOYSA-N"},
    {"name": "serotonin",      "smiles": "NCCc1c[nH]c2ccc(O)cc12",                   "inchikey": "QZAYGJVTTNCVMB-UHFFFAOYSA-N"},
    {"name": "nicotine",       "smiles": "CN1CCC[C@@H]1c1cccnc1",                    "inchikey": "SNICXCGAKADSCV-JTQLQIEISA-N"},
    {"name": "glucose",        "smiles": "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O", "inchikey": "WQZGKKKJIJFFOK-GASJEMHNSA-N"},
    {"name": "cholesterol",    "smiles": "C[C@@H](CCCC(C)C)[C@H]1CC[C@@H]2[C@@H]1CC=C3C[C@@H](O)CC[C@]23C", "inchikey": "HVYWMOMLDIMFJA-DPAQBDIFSA-N"},
    {"name": "vanillin",       "smiles": "COc1cc(C=O)ccc1O",                         "inchikey": "MWOOGOJBHIARFG-UHFFFAOYSA-N"},
    {"name": "menthol",        "smiles": "CC(C)[C@@H]1CC[C@@H](C)C[C@H]1O",         "inchikey": "NOOLISFMXDJSKH-UTLUCORTSA-N"},
    {"name": "capsaicin",      "smiles": "COc1cc(CNC(=O)CCCC/C=C/C(C)C)ccc1O",      "inchikey": "YKPUWZUDDOIDPM-SOFGYWHQSA-N"},
    {"name": "citric_acid",    "smiles": "OC(=O)CC(O)(CC(=O)O)C(=O)O",              "inchikey": "KRKNYBCHXYNGOX-UHFFFAOYSA-N"},
    {"name": "lidocaine",      "smiles": "CCN(CC)CC(=O)Nc1c(C)cccc1C",              "inchikey": "NNJVILVZKWQKPM-UHFFFAOYSA-N"},
    {"name": "quinine",        "smiles": "COc1ccc2nccc(c2c1)[C@@H](O)[C@H]3CC[N@@]4CC[C@@H](C=C)[C@H](C3)[C@@H]4", "inchikey": "LOUPRKONTZGTKE-LHHVKLHASA-N"},
    {"name": "penicillin_g",   "smiles": "CC1(C)S[C@@H]2[C@H](NC(=O)Cc3ccccc3)C(=O)N2[C@H]1C(=O)O", "inchikey": "JGSARLDLIJGVTE-MBNYWOFBSA-N"},
    {"name": "ethanol",        "smiles": "CCO",                                       "inchikey": "LFQSCWFLJHTTHZ-UHFFFAOYSA-N"},
    {"name": "benzene",        "smiles": "c1ccccc1",                                  "inchikey": "UHOVQNZJYSORNB-UHFFFAOYSA-N"},
    {"name": "acetone",        "smiles": "CC(C)=O",                                   "inchikey": "CSCPPACGZOOCGX-UHFFFAOYSA-N"},
    {"name": "toluene",        "smiles": "Cc1ccccc1",                                 "inchikey": "YXFVVABEGXRONW-UHFFFAOYSA-N"},
]

# ── MassBank fetching ──────────────────────────────────────────────────────────
MB_API = "https://massbank.eu/MassBank/api/v1"

def search_massbank(inchikey: str, name: str):
    """Search MassBank API for a molecule by InChIKey, return best MS spectrum."""
    try:
        url = f"{MB_API}/records/search?inchikey={inchikey}&type=MS2"
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            # Try by name
            url = f"{MB_API}/records/search?compound_name={name}&type=MS2"
            r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return None
        results = r.json()
        if not results:
            return None
        # Pick first result with actual peaks
        for rec in results[:5]:
            accession = rec.get("accession") or rec.get("id")
            if accession:
                detail_url = f"{MB_API}/records/{accession}"
                dr = requests.get(detail_url, timeout=15)
                if dr.status_code == 200:
                    return dr.json()
        return None
    except Exception as e:
        print(f"  MassBank API error for {name}: {e}")
        return None

def parse_massbank_record(record: dict) -> list:
    """Extract (mz, intensity) pairs from a MassBank API record."""
    peaks = []
    try:
        peak_data = record.get("peaks", record.get("peak", {}).get("peak", []))
        if isinstance(peak_data, list):
            for p in peak_data:
                if isinstance(p, dict):
                    peaks.append((float(p.get("mz", 0)), float(p.get("intensity", 0))))
                elif isinstance(p, (list, tuple)) and len(p) >= 2:
                    peaks.append((float(p[0]), float(p[1])))
    except Exception:
        pass
    return peaks

def fetch_massbank_txt(inchikey: str, name: str):
    """Fallback: search GitHub MassBank-data for txt files matching InChIKey."""
    try:
        # Use GitHub search API
        url = f"https://api.github.com/search/code?q={inchikey}+repo:MassBank/MassBank-data"
        headers = {"Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            items = r.json().get("items", [])
            if items:
                raw_url = items[0].get("html_url", "").replace(
                    "github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                if raw_url:
                    tr = requests.get(raw_url, timeout=15)
                    if tr.status_code == 200:
                        return parse_massbank_txt(tr.text)
    except Exception as e:
        print(f"  GitHub fallback error for {name}: {e}")
    return []

def parse_massbank_txt(text: str) -> list:
    """Parse a MassBank flat .txt record into (mz, intensity) pairs."""
    peaks = []
    in_peaks = False
    for line in text.splitlines():
        if line.startswith("PK$PEAK:"):
            in_peaks = True
            continue
        if in_peaks:
            if line.startswith("//") or line.startswith("PK$") or not line.strip():
                break
            parts = line.strip().split()
            if len(parts) >= 2:
                try:
                    peaks.append((float(parts[0]), float(parts[1])))
                except ValueError:
                    pass
    return peaks

def save_ms_csv(peaks: list, path: Path):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["mz", "intensity"])
        for mz, intensity in sorted(peaks):
            writer.writerow([f"{mz:.4f}", f"{intensity:.2f}"])

# ── NMRShiftDB fetching ────────────────────────────────────────────────────────
def search_nmrshiftdb(name: str, inchikey: str):
    """Search NMRShiftDB2 REST API for 1H NMR spectrum."""
    try:
        # NMRShiftDB has a simple search endpoint
        url = f"https://nmrshiftdb.nmr.uni-koeln.de/NmrshiftdbServlet/nmrshiftdbaction/search/searchresultsonly?name={name}&nucleus=1H&mol=&molsearchtype=exact&searchradius=0"
        r = requests.get(url, timeout=20)
        if r.status_code == 200 and r.text.strip():
            return parse_nmrshiftdb_html(r.text)
    except Exception as e:
        print(f"  NMRShiftDB error for {name}: {e}")

    # Fallback: try by InChIKey prefix
    try:
        url2 = f"https://nmrshiftdb.nmr.uni-koeln.de/NmrshiftdbServlet/nmrshiftdbaction/search/searchresultsonly?inchikey={inchikey[:14]}&nucleus=1H"
        r2 = requests.get(url2, timeout=20)
        if r2.status_code == 200:
            return parse_nmrshiftdb_html(r2.text)
    except Exception:
        pass

    return []

def parse_nmrshiftdb_html(html: str) -> list:
    """Extract chemical shifts from NMRShiftDB HTML response (peak list format)."""
    peaks = []
    # Look for patterns like: 7.26 (1H) or shift values in table cells
    # NMRShiftDB returns shift;intensity pairs separated by | or in table format
    pattern = re.compile(r'(\d+\.?\d*)\s*[;,]\s*(\d+\.?\d*)')
    for match in pattern.finditer(html):
        try:
            shift = float(match.group(1))
            intensity = float(match.group(2))
            if -2 <= shift <= 15:  # valid 1H NMR range
                peaks.append((shift, intensity))
        except ValueError:
            pass

    # Also try simple float extraction for shift lists
    if not peaks:
        shift_pattern = re.compile(r'\b(\d+\.\d{1,3})\b')
        shifts = []
        for m in shift_pattern.finditer(html):
            val = float(m.group(1))
            if -2 <= val <= 14:
                shifts.append(val)
        # Deduplicate and assign unit intensity
        seen = set()
        for s in shifts:
            rounded = round(s, 2)
            if rounded not in seen:
                seen.add(rounded)
                peaks.append((rounded, 1.0))

    return peaks[:50]  # cap at 50 peaks

def save_nmr_csv(peaks: list, path: Path):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ppm", "intensity"])
        for ppm, intensity in sorted(peaks):
            writer.writerow([f"{ppm:.4f}", f"{intensity:.4f}"])

# ── Synthetic fallback spectra ─────────────────────────────────────────────────
SYNTHETIC_NMR = {
    "caffeine":      [(3.35,100),(3.54,100),(3.93,100),(7.69,100)],
    "aspirin":       [(2.28,100),(6.92,10),(7.06,10),(7.37,10),(7.64,10),(8.05,10),(11.1,5)],
    "ibuprofen":     [(0.89,150),(1.46,50),(1.82,50),(2.44,50),(3.68,50),(7.07,100),(7.18,100)],
    "acetaminophen": [(2.16,100),(6.72,100),(7.34,100),(9.18,50),(9.65,20)],
    "dopamine":      [(2.60,100),(2.96,100),(3.10,50),(6.51,100),(6.63,100),(6.68,100)],
    "ethanol":       [(1.18,300),(3.69,200),(4.65,50)],
    "benzene":       [(7.34,500)],
    "acetone":       [(2.15,600)],
    "toluene":       [(2.33,300),(7.17,200),(7.25,200),(7.33,200)],
    "vanillin":      [(3.88,100),(6.95,100),(7.43,100),(7.54,100),(9.75,100)],
    "serotonin":     [(2.71,100),(3.00,100),(6.73,50),(6.97,50),(7.07,50),(7.22,50),(10.56,20)],
    "nicotine":      [(1.70,50),(1.90,50),(2.25,100),(2.35,100),(3.12,50),(7.29,50),(7.70,50),(8.47,50),(8.52,50)],
    "glucose":       [(3.20,100),(3.38,100),(3.45,100),(3.50,100),(3.72,100),(4.58,50),(5.18,50)],
    "cholesterol":   [(0.68,300),(0.86,200),(0.92,100),(1.01,200),(1.10,200),(1.45,300),(1.84,100),(3.52,50),(5.35,50)],
    "menthol":       [(0.78,200),(0.91,200),(0.95,100),(1.00,200),(1.45,100),(1.63,100),(2.17,50),(3.41,50)],
    "capsaicin":     [(0.94,100),(1.37,50),(1.62,50),(2.22,50),(3.85,100),(4.37,50),(5.91,30),(6.39,30),(6.75,80),(6.82,80),(9.36,20)],
    "citric_acid":   [(2.54,200),(2.78,200)],
    "lidocaine":     [(1.04,200),(2.14,100),(2.47,100),(3.22,100),(4.11,50),(6.97,100),(7.00,100),(7.02,100)],
    "quinine":       [(1.62,50),(1.85,50),(2.70,50),(3.11,50),(3.93,50),(4.98,30),(5.07,30),(5.76,30),(7.34,50),(7.42,50),(7.52,50),(7.98,50),(8.72,50)],
    "penicillin_g":  [(1.48,200),(1.53,200),(3.60,100),(4.20,50),(5.43,50),(5.51,50),(7.28,150),(7.34,150),(7.40,150)],
}

SYNTHETIC_MS = {
    "caffeine":      [(55,40),(69,50),(82,70),(109,100),(138,80),(194,200)],
    "aspirin":       [(39,30),(50,40),(64,60),(77,100),(92,80),(120,90),(138,70),(180,150)],
    "ibuprofen":     [(41,60),(43,100),(57,80),(69,50),(91,70),(105,60),(161,40),(206,180)],
    "acetaminophen": [(28,40),(43,100),(65,30),(80,50),(109,80),(151,200)],
    "dopamine":      [(30,20),(41,30),(77,50),(107,100),(123,80),(153,200)],
    "ethanol":       [(27,40),(29,100),(31,80),(45,200),(46,50)],
    "benzene":       [(50,50),(51,80),(52,40),(77,100),(78,200)],
    "acetone":       [(15,40),(27,30),(43,100),(58,200)],
    "toluene":       [(38,20),(50,30),(51,50),(63,40),(65,60),(91,100),(92,200)],
    "vanillin":      [(51,30),(65,40),(77,80),(93,60),(109,100),(137,70),(152,200)],
    "serotonin":     [(77,40),(115,60),(132,80),(146,100),(159,70),(176,200)],
    "nicotine":      [(42,30),(65,40),(80,60),(84,80),(117,50),(130,100),(133,70),(162,200)],
    "glucose":       [(60,50),(73,80),(85,60),(103,100),(145,70),(180,200)],
    "cholesterol":   [(95,40),(145,50),(159,60),(213,80),(247,100),(275,70),(301,60),(353,50),(368,80),(386,200)],
    "menthol":       [(41,50),(55,60),(69,80),(71,100),(81,70),(95,80),(123,60),(138,50),(156,200)],
    "capsaicin":     [(94,40),(122,60),(137,100),(168,50),(195,40),(261,30),(305,200)],
    "citric_acid":   [(43,30),(59,50),(75,60),(87,80),(111,100),(129,70),(174,50),(192,200)],
    "lidocaine":     [(58,50),(72,60),(86,100),(105,50),(120,80),(162,40),(191,30),(206,60),(234,200)],
    "quinine":       [(81,30),(108,50),(136,80),(160,60),(189,100),(226,50),(253,40),(281,60),(307,50),(324,200)],
    "penicillin_g":  [(91,40),(114,50),(160,80),(176,100),(217,60),(246,50),(290,80),(334,200)],
}

# ── Main fetch loop ────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("DiamondHacks — Fetching demo spectra")
    print("=" * 60)

    results = {}

    for mol in DEMO_MOLECULES:
        name = mol["name"]
        smiles = mol["smiles"]
        inchikey = mol["inchikey"]
        print(f"\n[{name}]")

        ms_path  = SPEC_OUT / f"{name}_ms.csv"
        nmr_path = SPEC_OUT / f"{name}_nmr.csv"

        # ── MS spectrum ──
        ms_peaks = []
        if not ms_path.exists():
            print(f"  Fetching MS from MassBank...")
            record = search_massbank(inchikey, name)
            if record:
                ms_peaks = parse_massbank_record(record)
                if ms_peaks:
                    print(f"  ✓ Got {len(ms_peaks)} MS peaks from API")
            if not ms_peaks:
                print(f"  Trying GitHub fallback...")
                ms_peaks = fetch_massbank_txt(inchikey, name)
                if ms_peaks:
                    print(f"  ✓ Got {len(ms_peaks)} MS peaks from GitHub")
            if not ms_peaks and name in SYNTHETIC_MS:
                ms_peaks = SYNTHETIC_MS[name]
                print(f"  ⚠ Using synthetic MS ({len(ms_peaks)} peaks)")
            if ms_peaks:
                save_ms_csv(ms_peaks, ms_path)
                time.sleep(0.3)  # be polite
        else:
            print(f"  ✓ MS already exists")
            ms_peaks = [(1,1)]  # marker

        # ── NMR spectrum ──
        nmr_peaks = []
        if not nmr_path.exists():
            print(f"  Fetching NMR from NMRShiftDB2...")
            nmr_peaks = search_nmrshiftdb(name, inchikey)
            if nmr_peaks:
                print(f"  ✓ Got {len(nmr_peaks)} NMR peaks")
            if not nmr_peaks and name in SYNTHETIC_NMR:
                nmr_peaks = SYNTHETIC_NMR[name]
                print(f"  ⚠ Using synthetic NMR ({len(nmr_peaks)} peaks)")
            if nmr_peaks:
                save_nmr_csv(nmr_peaks, nmr_path)
                time.sleep(0.3)
        else:
            print(f"  ✓ NMR already exists")
            nmr_peaks = [(1,1)]

        results[name] = {
            "smiles": smiles,
            "has_ms": bool(ms_peaks),
            "has_nmr": bool(nmr_peaks),
            "ms_path": str(ms_path.relative_to(ROOT)) if ms_path.exists() else None,
            "nmr_path": str(nmr_path.relative_to(ROOT)) if nmr_path.exists() else None,
        }

    # Save manifest
    manifest_path = ROOT / "data" / "raw" / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print(f"✓ Done. Manifest saved to {manifest_path}")
    ms_ok  = sum(1 for v in results.values() if v["has_ms"])
    nmr_ok = sum(1 for v in results.values() if v["has_nmr"])
    print(f"  MS spectra:  {ms_ok}/{len(DEMO_MOLECULES)}")
    print(f"  NMR spectra: {nmr_ok}/{len(DEMO_MOLECULES)}")
    print(f"\nNext step: run  python scripts/build_fixtures.py")

if __name__ == "__main__":
    main()
