# DiamondHacks Frontend

## Setup
```bash
npx create-next-app@latest . --typescript --tailwind --app
npm install 3dmol axios
npm run dev
```

## Key pages
- `/` — Landing + file upload
- `/results` — Ranked candidates + 3D viewer

## API integration
All calls go to `http://localhost:8000`
See `backend/main.py` for the full API contract.
