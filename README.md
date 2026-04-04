# DiamondHacks — Multimodal Spectra → Structure

> Paste in NMR, MS, and/or IR spectra. Get ranked candidate molecules with 3D conformers.

## Stack
| Layer | Tech |
|---|---|
| Frontend | Next.js + Tailwind CSS |
| Backend | FastAPI + Uvicorn |
| MS inference | MIST (pretrained, MIT) |
| Chemistry | RDKit, SELFIES |

## Quickstart

```bash
# 1. Install Python deps
pip install -e ".[dev]"

# 2. Fetch real spectra for 20 demo molecules
python scripts/fetch_demo_data.py

# 3. Build fixture JSONs + conformers
python scripts/build_fixtures.py

# 4. Start API (demo mode — no ML needed)
DEMO_MODE=true uvicorn backend.main:app --reload --port 8000

# 5. Start frontend
cd frontend && npm install && npm run dev
```

## Project structure
```
diamondhacks/
  configs/          — model, data, train YAML configs
  data/
    fixtures/       — precomputed JSON + spectra CSVs for 20 molecules
    raw/            — downloaded database files
  scripts/
    fetch_demo_data.py  — downloads spectra from MassBank + NMRShiftDB2
    build_fixtures.py   — generates fixture JSONs + RDKit conformers
  src/
    data/           — binning, datasets, schema
    models/         — encoder, fusion, decoder, heads
    chemistry/      — rdkit_utils, selfies_utils
    training/       — losses, metrics, loops
  backend/
    main.py         — FastAPI app
  frontend/         — Next.js app (npm create next-app)
  tests/            — pytest tests
```

## Demo molecules (20)
caffeine, aspirin, ibuprofen, acetaminophen, dopamine, serotonin,
nicotine, glucose, cholesterol, vanillin, menthol, capsaicin,
citric_acid, lidocaine, quinine, penicillin_g, ethanol, benzene,
acetone, toluene

## API
`POST /predict` — accepts base64-encoded CSV spectra, returns top-5 candidates
`GET  /fixtures` — lists available demo molecules
`GET  /health`   — health check

## Demo flow (rehearse twice!)
1. Open site → clean landing page
2. Upload caffeine NMR CSV
3. Show top-5 candidates (correct molecule in top-3)
4. Add MS input → correct molecule moves to #1
5. Click top-1 → show 3D conformer in viewer
6. Ablation: NMR alone vs NMR+MS vs all three
