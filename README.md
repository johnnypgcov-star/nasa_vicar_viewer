# NASA VICAR Viewer

A Docker-based web viewer for NASA Voyager 1 & 2 planetary imagery. Browse live data from the NASA OPUS archive, explore your local planetary data collection, and parse VICAR / PDS3 / PDS4 image files directly in the browser.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688)
![Docker](https://img.shields.io/badge/Docker-port%2085-2496ED)
![License](https://img.shields.io/badge/data-public%20domain-green)

---

## Features

- **Browse NASA OPUS** — search Voyager 1 & 2 observations live; filter by spacecraft and target body; paginated image grid with lightbox and raw VICAR loading
- **Local file browser** — three-panel explorer with a user-configurable root path saved persistently across restarts; supports VICAR images, PDS4, text files, and archives
- **Archive browser** — browse and view files inside `.tar.gz`, `.zip`, and other archives without manual extraction; cached after first open
- **Upload** — drag-and-drop any `.IMG`, `.VIC`, or `.xml` file for instant parsing and display
- **Full format support** — VICAR, PDS3, PDS4; BYTE / HALF / FULL / REAL pixel types; BSQ / BIL / BIP organisations; all byte orders

---

## Quick start

```powershell
# Start
docker compose up -d

# Stop
docker compose down

# Rebuild after code changes
docker compose build && docker compose up -d
```

Open **http://localhost:85** once running.

> **Docker Desktop requirement:** the drive containing your local data must be shared under Settings → Resources → File Sharing. The default mount in `docker-compose.yml` is `J:/` — edit this to match your setup.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + uvicorn, Python 3.12 |
| Frontend | Vanilla JS SPA — dark space theme, no framework |
| Container | Docker, port 85 |
| Data | NASA OPUS API + user-configured local mount (read-only) |
| Config | Persistent Docker named volume (`vicar_config`) |
| Cache | 512 MB tmpfs at `/tmp/vicar_cache` |

---

## Configuration

The local file browser root path is set through the UI — no hardcoded paths in the application. On first launch, open the **Local Files** tab and enter your data path (e.g. `J:\ASTRONOMY`). The path is saved to `/config/settings.json` on the `vicar_config` named volume and restored on every subsequent start.

To browse a different drive, add it to `docker-compose.yml`:

```yaml
volumes:
  - "D:/:/data/D:ro"
  - "J:/:/data/J:ro"
```

---

## Documentation

- [User Manual](USER_MANUAL.md) — complete usage guide covering all tabs, file formats, archive browsing, caching, and troubleshooting
- [Changelog](CHANGELOG.md) — version history and full API reference

---

## Data sources

All NASA Voyager planetary data is in the public domain.

- OPUS (Outer Planets Unified Search): https://opus.pds-rings.seti.org
- PDS Imaging Node: https://pds-imaging.jpl.nasa.gov

---

&copy; 2026 John Gilbert. NASA data is public domain.
