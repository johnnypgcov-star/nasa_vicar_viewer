# Changelog

All notable changes to NASA VICAR Viewer are documented here.

---

## [1.1.0] — 2026-05-06

### Changed
- **Local file browser root path is now user-configurable** — no path is hardcoded in the application. The root directory is saved server-side in `/config/settings.json` on a persistent Docker named volume (`vicar_config`) and survives container restarts.
- Docker volume mount changed from `J:/ASTRONOMY:/data/astronomy` to `J:/:/data/J` so any subdirectory of the J: drive can be set as the root without rebuilding.
- Removed all hardcoded references to `J:\ASTRONOMY` from application code.

### Added
- `GET /api/config` — returns the currently saved root path
- `POST /api/config?root_path=` — saves a new root path; persisted to `/config/settings.json`
- Path edit UI in the Local Files panel header: pencil button opens an inline text input; Enter saves, Escape cancels; path auto-loads on tab open
- If no path is configured, the edit UI opens automatically with a prompt
- Credit: Built by John Gilbert — 2026

### Fixed
- Backend path mapper `_win_to_container()` handles any drive letter (not just J:), UNC-style paths, and bare drive roots

---

## [1.0.0] — 2026-05-06

### Added

**Core image parsing**
- VICAR format parser supporting BYTE, HALF, FULL, and REAL pixel types
- PDS3 detached-label `.IMG` auto-detection (falls back to VICAR if no PDS3 label found)
- PDS4 XML label parser with array renderer
- Support for all byte orders (LOW/HIGH) and all data organisations (BSQ, BIL, BIP)
- All parsed images returned as PNG via base64

**NASA OPUS integration**
- Live search against NASA OPUS API (`opus.pds-rings.seti.org/opus/api`)
- Filter by spacecraft (Voyager 1, Voyager 2, or both) and target body
- Targets: Jupiter, Saturn, Uranus, Neptune and their major moons (Io, Europa, Ganymede, Callisto, Titan, Miranda, Ariel, Umbriel, Titania, Oberon, Triton)
- Paginated image grid (24 per page, configurable up to 100)
- Observation detail panel with calibrated file links
- Lightbox viewer with VICAR raw-image loading and OPUS deep-link
- Spacecraft filter buttons auto-trigger search on click (no separate Search button needed)
- Image proxy endpoint with disk cache to avoid repeated PDS fetches

**Local file browser**
- Browse `J:\ASTRONOMY` collection mounted read-only into the container
- Three-panel layout: folder tree / file list / viewer
- Displays `.IMG`, `.JPG`, `.GIF`, `.LBL`, `.TAB`, `.CAT`, `.ASC`, `.TXT`, `.HTM`, `.HTML`, `.DAT`, `.XML` files
- IMG sub-type badges: CALIB, CLEANED, RAW, GEOMED, GEOMA
- Text viewer with format badge, 200 KB cap warning, and word-wrap toggle
- Binary `.DAT` detection (skips non-printable content)

**Archive browser**
- Browse and view files inside `.zip`, `.tar`, `.tar.gz`, `.tgz`, `.tar.bz2`, `.tar.xz`, `.gz`, `.bz2` archives
- Archive listing runs in a thread pool (non-blocking)
- Listing cache keyed on path + mtime; full response disk cache avoids re-extraction
- Up to 5,000 viewable entries per archive

**Upload**
- Drag-and-drop or click-to-browse upload of `.IMG`, `.VIC`, `.VICAR` files
- PDS4 `.xml` upload returns parsed label metadata (image requires co-located data file)

**Infrastructure**
- FastAPI + uvicorn backend on port 85 (`python:3.12-slim` Docker image)
- Dark space-themed single-page frontend (vanilla JS, no framework)
- CORS middleware enabled for local development
- `/tmp/vicar_cache` tmpfs (512 MB) for parsed PNG and metadata cache
- `/api/health` endpoint
- `J:\ASTRONOMY` mounted read-only at `/data/astronomy`

---

## API endpoints (v1.0.0)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/search` | OPUS search (spacecraft, target, page, limit) |
| GET | `/api/targets` | List available target bodies and spacecraft |
| GET | `/api/observation/{opus_id}` | Files + metadata for one observation |
| GET | `/api/proxy/image?url=` | Proxy + cache a PDS image URL |
| GET | `/api/vicar/from-url?url=` | Fetch + parse remote VICAR/PDS3 as PNG |
| GET | `/api/pds4/from-url?label_url=` | Fetch PDS4 label + data file → PNG |
| POST | `/api/vicar/upload` | Upload VICAR/PDS3/.xml → PNG or label metadata |
| GET | `/api/local/browse?path=` | List dirs + files under J:\ASTRONOMY |
| GET | `/api/local/view?path=` | Render any supported local file |
| GET | `/api/local/archive/list?path=` | List viewable files inside an archive |
| GET | `/api/local/archive/view?path=&inner=` | Extract + render one file from an archive |
| GET | `/api/health` | Service health check |
