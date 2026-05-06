# Changelog

All notable changes to NASA VICAR Viewer are documented here.

---

## [1.1.0] — 2026-05-06

Initial public release.

### Core image parsing

- VICAR format parser — BYTE, HALF, FULL, REAL pixel types; BSQ, BIL, BIP data organisations; LOW/HIGH byte order
- PDS3 detached-label `.IMG` auto-detection; falls back to VICAR header detection if no PDS3 label present
- PDS4 XML label parser with array renderer
- All parsed images returned as PNG via base64

### NASA OPUS integration

- Live search against the NASA OPUS API (`opus.pds-rings.seti.org/opus/api`)
- Filter by spacecraft (Voyager 1, Voyager 2, or both) and target body
- Supported targets: Jupiter, Saturn, Uranus, Neptune and their major moons — Io, Europa, Ganymede, Callisto, Titan, Miranda, Ariel, Umbriel, Titania, Oberon, Triton
- Paginated image grid (24 per page, up to 100)
- Lightbox viewer with full VICAR raw-image loading and OPUS deep-link
- Spacecraft and target filters trigger search immediately on change — no separate Search button required
- Image proxy endpoint with disk cache to avoid repeated PDS round-trips

### Local file browser

- User-configurable root path — no hardcoded paths in the application
- Root path saved persistently in `/config/settings.json` on a Docker named volume (`vicar_config`); survives container restarts
- Inline path editor in the panel header: pencil button opens a text input; Enter saves, Escape cancels; edit UI opens automatically if no path is configured
- Backend path mapper `_win_to_container()` supports any Windows drive letter and bare drive roots
- Three-panel layout: expandable folder tree / file list grouped by observation ID / viewer
- Displays `.IMG`, `.JPG`, `.GIF`, `.LBL`, `.TAB`, `.CAT`, `.ASC`, `.TXT`, `.HTM`, `.HTML`, `.DAT`, `.XML`
- IMG sub-type colour badges: CALIB, CLEANED, RAW, GEOMED, GEOMA
- Text viewer with format badge, 200 KB truncation warning, and word-wrap toggle
- Binary `.DAT` auto-detection (non-printable ratio check)

### Archive browser

- Browse and view files inside `.zip`, `.tar`, `.tar.gz`, `.tgz`, `.tar.bz2`, `.tar.xz`, `.gz`, `.bz2` archives
- Archive listing and extraction run in a `ThreadPoolExecutor` (non-blocking)
- Listing cache keyed on path + mtime; full-response disk cache avoids re-extraction on revisit
- Filter bar inside open archives (by filename, observation ID, or subdirectory)
- Up to 5,000 viewable entries per archive; overflow indicated with a count

### Upload

- Drag-and-drop or click-to-browse upload of `.IMG`, `.VIC`, `.VICAR`, `.xml`, `.LBL` files
- PDS4 `.xml` without a co-located data file returns parsed label metadata

### Infrastructure

- FastAPI + uvicorn backend on port 85 (`python:3.12-slim`)
- Dark space-themed single-page frontend — vanilla JS, no framework
- CORS middleware enabled
- 512 MB tmpfs at `/tmp/vicar_cache` for parsed PNG and metadata
- `vicar_config` named Docker volume for persistent settings
- `/api/health` endpoint

---

## API reference (v1.1.0)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/search` | OPUS search — `spacecraft`, `target`, `page`, `limit` |
| GET | `/api/targets` | List available target bodies and spacecraft values |
| GET | `/api/observation/{opus_id}` | Files + metadata for one observation |
| GET | `/api/proxy/image?url=` | Proxy and cache a remote PDS image URL |
| GET | `/api/vicar/from-url?url=` | Fetch and parse a remote VICAR / PDS3 file → PNG |
| GET | `/api/pds4/from-url?label_url=` | Fetch PDS4 label + data file → PNG |
| POST | `/api/vicar/upload` | Upload VICAR / PDS3 / `.xml` → PNG or label metadata |
| GET | `/api/config` | Return the currently saved local root path |
| POST | `/api/config?root_path=` | Save a new local root path |
| GET | `/api/local/browse?path=` | List directories and viewable files at a path |
| GET | `/api/local/view?path=` | Render any supported local file |
| GET | `/api/local/archive/list?path=` | List viewable files inside an archive |
| GET | `/api/local/archive/view?path=&inner=` | Extract and render one file from an archive |
| GET | `/api/health` | Service health check |

---

Built by John Gilbert &mdash; 2026
