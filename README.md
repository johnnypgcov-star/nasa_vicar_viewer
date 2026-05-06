# NASA VICAR Viewer

A Docker-based web viewer for NASA Voyager 1 & 2 planetary imagery. Browse live data from the NASA OPUS archive, explore your local `J:\ASTRONOMY` collection, and parse VICAR/PDS3/PDS4 image files directly in the browser.

![Dark space-themed UI](https://img.shields.io/badge/UI-dark%20space%20theme-0a0a1a)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688)
![Docker](https://img.shields.io/badge/Docker-port%2085-2496ED)

---

## Features

- **Browse NASA OPUS** — search Voyager 1 & 2 observations by spacecraft and target body (Jupiter, Saturn, Uranus, Neptune and their moons); paginated image grid with lightbox and raw VICAR loading
- **Local file browser** — three-panel explorer with a user-configurable root path (saved persistently); supports `.IMG`, `.JPG`, `.GIF`, text files, PDS4 `.xml`, and all major archive formats
- **Archive browser** — browse and view files inside `.tar.gz`, `.zip`, and other archives without manual extraction
- **Upload** — drag-and-drop any `.IMG`, `.VIC`, or `.xml` file for instant parsing
- **Format support** — VICAR, PDS3, PDS4; BYTE/HALF/FULL/REAL pixel types; BSQ/BIL/BIP organisations; all byte orders

---

## Quick start

```powershell
docker compose up -d
```

Open **http://localhost:85**

```powershell
# Stop
docker compose down

# Rebuild after code changes
docker compose build && docker compose up -d
```

> Requires Docker Desktop with `J:\` drive shared under Resources → File Sharing.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + uvicorn (Python 3.12) |
| Frontend | Vanilla JS SPA, dark space theme |
| Container | Docker, port 85 |
| Data | NASA OPUS API + local `J:\ASTRONOMY` (read-only mount) |
| Cache | 512 MB tmpfs at `/tmp/vicar_cache` |

---

## Documentation

- [User Manual](USER_MANUAL.md) — full usage guide for all tabs and features
- [Changelog](CHANGELOG.md) — version history and API reference

---

## Data sources

All NASA planetary data is in the public domain.  
OPUS API: https://opus.pds-rings.seti.org  
PDS Imaging Node: https://pds-imaging.jpl.nasa.gov

---

Built by John Gilbert &mdash; 2026
