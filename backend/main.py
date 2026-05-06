"""NASA VICAR Viewer — FastAPI backend for Voyager 1 & 2 data."""
import asyncio
import base64
import bz2 as _bz2
import gzip
import hashlib
import json as _json
import tarfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

import pds
import vicar
import pds4 as pds4_mod

_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="archive")

app = FastAPI(title="NASA VICAR Viewer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CACHE_DIR = Path("/tmp/vicar_cache")
CACHE_DIR.mkdir(exist_ok=True)


def _cache(key: str) -> Path:
    h = hashlib.sha256(key.encode()).hexdigest()[:16]
    return CACHE_DIR / h


# ── File-type catalogue ───────────────────────────────────────────────────────
# ext (uppercase) → category used by the frontend
# ── Archive support ───────────────────────────────────────────────────────────

INNER_IMAGE_EXTS   = {".IMG", ".JPG", ".JPEG", ".GIF", ".PNG"}
INNER_TEXT_EXTS    = {".LBL", ".CAT", ".TAB", ".ASC", ".TXT", ".HTM", ".HTML"}
INNER_VIEWABLE_EXTS = INNER_IMAGE_EXTS | INNER_TEXT_EXTS

MAX_ARCHIVE_ENTRIES = 5000


def _effective_ext(item: Path) -> str:
    """Return the full effective extension, handling .tar.gz / .tar.bz2."""
    sfx = [s.lower() for s in item.suffixes]
    if len(sfx) >= 2 and sfx[-2:] == [".tar", ".gz"]:  return ".TAR.GZ"
    if len(sfx) >= 2 and sfx[-2:] == [".tar", ".bz2"]: return ".TAR.BZ2"
    if len(sfx) >= 2 and sfx[-2:] == [".tar", ".xz"]:  return ".TAR.XZ"
    return item.suffix.upper()


def _archive_mode(path: Path) -> tuple[str, str]:
    """Return (kind, mode): kind in {zip,tar,gz,bz2}, mode is tarfile open mode."""
    ext = _effective_ext(path)
    if ext == ".ZIP":     return "zip", ""
    if ext == ".TGZ":     return "tar", "r:gz"
    if ext == ".TAR.GZ":  return "tar", "r:gz"
    if ext == ".TAR.BZ2": return "tar", "r:bz2"
    if ext == ".TAR.XZ":  return "tar", "r:xz"
    if ext == ".TAR":     return "tar", "r:"
    if ext == ".GZ":
        # Probe: is it actually a tar.gz?
        try:
            with tarfile.open(path, "r:gz") as tf:
                if tf.next() is not None:
                    return "tar", "r:gz"
        except Exception:
            pass
        return "gz", ""
    if ext == ".BZ2":
        try:
            with tarfile.open(path, "r:bz2") as tf:
                if tf.next() is not None:
                    return "tar", "r:bz2"
        except Exception:
            pass
        return "bz2", ""
    raise ValueError(f"Not a recognised archive: {path.name}")


def _inner_entry(name: str, size: int) -> dict | None:
    """Build a file-entry dict for an archive member; returns None if not viewable."""
    p = Path(name)
    ext = p.suffix.upper()
    if ext not in INNER_VIEWABLE_EXTS:
        return None
    basename = p.name
    if ext in INNER_IMAGE_EXTS:
        cat = "image"
        ftype = _img_subtype(basename)
    else:
        cat = "text"
        ftype = ext.lstrip(".")
    return {
        "inner_path": name,
        "name": basename,
        "dir": str(p.parent) if str(p.parent) != "." else "",
        "obs_id": basename.split("_")[0],
        "type": ftype,
        "category": cat,
        "ext": ext.lstrip("."),
        "size_mb": round(size / 1_048_576, 2),
    }


def _list_archive_sync(path: Path) -> dict:
    """Blocking: list viewable entries in an archive. Run in thread pool."""
    kind, mode = _archive_mode(path)
    entries = []
    capped = False

    if kind == "zip":
        with zipfile.ZipFile(path, "r") as zf:
            for info in zf.infolist():
                if info.filename.endswith("/"):
                    continue
                e = _inner_entry(info.filename, info.file_size)
                if e:
                    entries.append(e)
                if len(entries) >= MAX_ARCHIVE_ENTRIES:
                    capped = True
                    break

    elif kind == "tar":
        with tarfile.open(path, mode) as tf:
            for member in tf:
                if not member.isfile():
                    continue
                e = _inner_entry(member.name, member.size)
                if e:
                    entries.append(e)
                if len(entries) >= MAX_ARCHIVE_ENTRIES:
                    capped = True
                    break

    elif kind == "gz":
        with gzip.open(path, "rb") as gz:
            raw = gz.read()
        inner_name = path.stem  # strip .gz
        e = _inner_entry(inner_name, len(raw))
        if e:
            entries.append(e)

    elif kind == "bz2":
        with _bz2.open(path, "rb") as bz:
            raw = bz.read()
        inner_name = path.stem
        e = _inner_entry(inner_name, len(raw))
        if e:
            entries.append(e)

    return {
        "archive_name": path.name,
        "archive_type": kind,
        "entries": entries,
        "total_viewable": len(entries),
        "capped": capped,
    }


def _read_archive_member_sync(path: Path, inner: str) -> bytes:
    """Blocking: extract one member from an archive. Run in thread pool."""
    kind, mode = _archive_mode(path)

    if kind == "zip":
        with zipfile.ZipFile(path, "r") as zf:
            return zf.read(inner)

    elif kind == "tar":
        with tarfile.open(path, mode) as tf:
            m = tf.getmember(inner)
            f = tf.extractfile(m)
            if f is None:
                raise FileNotFoundError(f"{inner} is not a regular file")
            return f.read()

    elif kind == "gz":
        with gzip.open(path, "rb") as gz:
            return gz.read()

    elif kind == "bz2":
        with _bz2.open(path, "rb") as bz:
            return bz.read()

    raise ValueError(f"Cannot extract from {kind} archive")


def _raw_to_response(raw: bytes, filename: str, cp: Path) -> dict:
    """Convert raw bytes to a typed viewer response, using cache path cp."""
    png_p   = Path(str(cp) + ".png")
    meta_p  = Path(str(cp) + ".json")

    # Check cache
    if png_p.exists() and meta_p.exists():
        return {
            "type": "image",
            "format": _json.loads(meta_p.read_text()).get("image_format", "vicar"),
            "png_base64": base64.b64encode(png_p.read_bytes()).decode(),
            "metadata": _json.loads(meta_p.read_text()),
            "filename": filename,
        }

    ext = Path(filename).suffix.upper()

    # VICAR / PDS3 image
    if ext in (".IMG", ".VIC", ""):
        png_bytes, metadata = vicar.parse_any_image(raw)
        png_p.write_bytes(png_bytes)
        meta_p.write_text(_json.dumps(metadata))
        return {
            "type": "image",
            "format": metadata.get("image_format", "vicar"),
            "png_base64": base64.b64encode(png_bytes).decode(),
            "metadata": metadata,
            "filename": filename,
        }

    # Pass-through image
    if ext in IMAGE_PASSTHROUGH:
        return {
            "type": "image",
            "format": ext.lstrip(".").lower(),
            "data_base64": base64.b64encode(raw).decode(),
            "mime_type": _mime(ext),
            "filename": filename,
            "size_mb": round(len(raw) / 1_048_576, 2),
        }

    # Text files
    if ext in TEXT_EXTENSIONS:
        text = raw.decode("ascii", errors="replace")
        return {
            "type": "text",
            "format": "pds3_label" if ext == ".LBL" else "pds3_table" if ext == ".TAB" else "text",
            "text": text[:200_000],
            "truncated": len(raw) > 200_000,
            "filename": filename,
        }

    # Auto-detect: try image then text
    try:
        png_bytes, metadata = vicar.parse_any_image(raw)
        png_p.write_bytes(png_bytes)
        meta_p.write_text(_json.dumps(metadata))
        return {
            "type": "image",
            "format": metadata.get("image_format", "vicar"),
            "png_base64": base64.b64encode(png_bytes).decode(),
            "metadata": metadata,
            "filename": filename,
        }
    except Exception:
        pass

    non_print = sum(1 for c in raw[:2000] if c < 9 or (13 < c < 32))
    if non_print / max(min(len(raw), 2000), 1) < 0.10:
        return {
            "type": "text",
            "format": "text",
            "text": raw.decode("ascii", errors="replace")[:200_000],
            "filename": filename,
        }

    return {
        "type": "binary",
        "filename": filename,
        "size_mb": round(len(raw) / 1_048_576, 2),
        "message": "Binary data — cannot display as text.",
    }


# ── File-type catalogue ───────────────────────────────────────────────────────

VIEWABLE_EXTS: dict[str, str] = {
    ".IMG":   "image",    # VICAR or PDS3 — rendered as PNG
    ".JPG":   "image",    # JPEG browse preview
    ".JPEG":  "image",
    ".GIF":   "image",    # GIF browse preview
    ".XML":    "pds4",     # PDS4 label + data
    ".ZIP":    "archive",  # ZIP archive
    ".TAR":    "archive",  # TAR archive
    ".TGZ":    "archive",  # tar.gz alias
    ".GZ":     "archive",  # standalone gz OR tar.gz
    ".BZ2":    "archive",  # standalone bz2 OR tar.bz2
    ".TAR.GZ": "archive",
    ".TAR.BZ2":"archive",
    ".TAR.XZ": "archive",
    ".LBL":   "text",     # PDS3 detached label
    ".CAT":   "text",     # PDS3 catalog
    ".TAB":   "text",     # ASCII table
    ".ASC":   "text",     # ASCII data
    ".TXT":   "text",
    ".HTM":   "text",
    ".HTML":  "text",
    ".DAT":   "data",     # binary or ASCII auxiliary data
}

# IMG sub-type badge names
_IMG_TYPE_SUFFIXES = {
    "_CALIB":   "CALIB",
    "_CLEANED": "CLEANED",
    "_RAW":     "RAW",
    "_GEOMED":  "GEOMED",
    "_GEOMA":   "GEOMA",
}

TEXT_EXTENSIONS = {".LBL", ".CAT", ".TAB", ".ASC", ".TXT", ".HTM", ".HTML"}
IMAGE_PASSTHROUGH = {".JPG", ".JPEG", ".GIF"}


def _img_subtype(name: str) -> str:
    upper = name.upper()
    for sfx, label in _IMG_TYPE_SUFFIXES.items():
        if sfx in upper:
            return label
    return "IMG"


def _mime(ext: str) -> str:
    return {"JPG": "image/jpeg", "JPEG": "image/jpeg", "GIF": "image/gif",
            "PNG": "image/png"}.get(ext.lstrip(".").upper(), "application/octet-stream")


# ── Search ────────────────────────────────────────────────────────────────────

@app.get("/api/search")
async def search(
    spacecraft: str = Query("both"),
    target: str = Query("all"),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
):
    try:
        return await pds.search_voyager(spacecraft=spacecraft, target=target,
                                        page=page, limit=limit)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"OPUS API error: {e}")


@app.get("/api/targets")
async def targets():
    return {"targets": list(pds.VOYAGER_TARGETS.keys()),
            "spacecraft": ["both", "Voyager 1", "Voyager 2"]}


# ── Observation detail ────────────────────────────────────────────────────────

@app.get("/api/observation/{opus_id}")
async def observation(opus_id: str):
    try:
        import asyncio
        files, meta = await asyncio.gather(
            pds.get_observation_files(opus_id),
            pds.get_observation_metadata(opus_id),
        )
        return {"opus_id": opus_id, "files": files, "metadata": meta}
    except httpx.HTTPError as e:
        raise HTTPException(502, f"OPUS API error: {e}")


# ── Image proxy ───────────────────────────────────────────────────────────────

@app.get("/api/proxy/image")
async def proxy_image(url: str = Query(...)):
    cp = _cache(url)
    if cp.exists():
        return Response(content=cp.read_bytes(), media_type=_guess_ct(url))
    try:
        resp = await pds.get_client().get(url)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Fetch failed: {e}")
    data = resp.content
    cp.write_bytes(data)
    return Response(content=data, media_type=resp.headers.get("content-type", _guess_ct(url)))


def _guess_ct(url: str) -> str:
    ul = url.lower()
    if ul.endswith((".jpg", ".jpeg")): return "image/jpeg"
    if ul.endswith(".png"): return "image/png"
    if ul.endswith(".gif"): return "image/gif"
    return "application/octet-stream"


# ── VICAR / PDS3 from URL ─────────────────────────────────────────────────────

@app.get("/api/vicar/from-url")
async def vicar_from_url(url: str = Query(...)):
    """Download and parse a VICAR or PDS3 .IMG from a remote URL."""
    cp = _cache(f"img:{url}")
    png_p = Path(str(cp) + ".png")
    meta_p = Path(str(cp) + ".json")

    if png_p.exists() and meta_p.exists():
        return {"png_base64": base64.b64encode(png_p.read_bytes()).decode(),
                "metadata": _json.loads(meta_p.read_text())}

    try:
        raw = await pds.fetch_vicar_file(url)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Fetch failed: {e}")

    try:
        png_bytes, metadata = vicar.parse_any_image(raw)
    except Exception as e:
        raise HTTPException(422, f"Parse error: {e}")

    png_p.write_bytes(png_bytes)
    meta_p.write_text(_json.dumps(metadata))
    return {"png_base64": base64.b64encode(png_bytes).decode(), "metadata": metadata}


# ── PDS4 from URL ─────────────────────────────────────────────────────────────

@app.get("/api/pds4/from-url")
async def pds4_from_url(
    label_url: str = Query(..., description="URL of the PDS4 XML label"),
):
    """Fetch a PDS4 XML label, resolve and fetch the data file, return PNG."""
    client = pds.get_client()

    try:
        label_resp = await client.get(label_url)
        label_resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Failed to fetch PDS4 label: {e}")

    label_bytes = label_resp.content
    try:
        meta = pds4_mod.parse_pds4_label(label_bytes)
    except Exception as e:
        raise HTTPException(422, f"PDS4 label parse error: {e}")

    if not meta["files"]:
        raise HTTPException(422, "PDS4 label contains no file references")

    # Construct data file URL relative to label URL
    base_url = label_url.rsplit("/", 1)[0] + "/"
    data_url = base_url + meta["files"][0]

    cp = _cache(f"pds4:{label_url}")
    png_p = Path(str(cp) + ".png")
    meta_p = Path(str(cp) + ".json")

    if png_p.exists() and meta_p.exists():
        return {"png_base64": base64.b64encode(png_p.read_bytes()).decode(),
                "metadata": _json.loads(meta_p.read_text())}

    try:
        data_resp = await client.get(data_url)
        data_resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Failed to fetch PDS4 data file ({data_url}): {e}")

    try:
        png_bytes, metadata = pds4_mod.pds4_to_png_bytes(label_bytes, data_resp.content)
    except Exception as e:
        raise HTTPException(422, f"PDS4 render error: {e}")

    png_p.write_bytes(png_bytes)
    meta_p.write_text(_json.dumps(metadata))
    return {"png_base64": base64.b64encode(png_bytes).decode(), "metadata": metadata}


# ── Upload (VICAR / PDS3 / PDS4) ─────────────────────────────────────────────

@app.post("/api/vicar/upload")
async def vicar_upload(file: UploadFile = File(...)):
    """Upload a VICAR, PDS3 .IMG, or PDS4 .xml file and get PNG + metadata."""
    raw = await file.read()
    ext = Path(file.filename or "").suffix.upper()

    if ext == ".XML":
        # PDS4 label upload — can only show metadata without data file
        try:
            meta = pds4_mod.parse_pds4_label(raw)
        except Exception as e:
            raise HTTPException(422, f"PDS4 label parse error: {e}")
        return {
            "type": "pds4_label_only",
            "metadata": meta,
            "filename": file.filename,
            "message": "PDS4 label parsed. Upload the data file separately or provide a URL.",
        }

    try:
        png_bytes, metadata = vicar.parse_any_image(raw)
    except Exception as e:
        raise HTTPException(422, f"Image parse error: {e}")

    return {
        "type": "image",
        "png_base64": base64.b64encode(png_bytes).decode(),
        "metadata": metadata,
        "filename": file.filename,
    }


# ── Config — user-configurable data root ─────────────────────────────────────

CONFIG_DIR  = Path("/config")
CONFIG_FILE = CONFIG_DIR / "settings.json"


def _win_to_container(win_path: str) -> Path:
    """Map a Windows path (e.g. J:\\ASTRONOMY) to its container mount (/data/J/ASTRONOMY)."""
    p = win_path.strip().replace("\\", "/")
    if len(p) >= 2 and p[1] == ":":
        drive = p[0].upper()
        rest  = p[2:].lstrip("/")
        return Path(f"/data/{drive}") / rest if rest else Path(f"/data/{drive}")
    return Path("/data") / p.lstrip("/")


def _get_root() -> tuple[Path, str]:
    """Return (container_path, windows_display_path) from saved config."""
    if CONFIG_FILE.exists():
        try:
            cfg = _json.loads(CONFIG_FILE.read_text())
            wp  = cfg.get("root_path", "").strip()
            if wp:
                return _win_to_container(wp), wp
        except Exception:
            pass
    return Path("/data"), ""


def _save_root(win_path: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(_json.dumps({"root_path": win_path}))


@app.get("/api/config")
async def get_config():
    _, wp = _get_root()
    return {"root_path": wp}


@app.post("/api/config")
async def set_config(root_path: str = Query(...)):
    _save_root(root_path.strip())
    return {"root_path": root_path.strip(), "status": "saved"}


# ── Local file browser ────────────────────────────────────────────────────────


def _safe(rel: str) -> Path:
    local_root, win_root = _get_root()
    if not win_root:
        raise HTTPException(503, "No data path configured. Use the settings panel to set a path.")
    if not local_root.exists():
        raise HTTPException(503, f"Configured path not accessible: {win_root}")
    rel = rel.lstrip("/").replace("\\", "/")
    resolved = (local_root / rel).resolve()
    try:
        resolved.relative_to(local_root.resolve())
    except ValueError:
        raise HTTPException(400, "Invalid path")
    return resolved


@app.get("/api/local/browse")
async def local_browse(path: str = Query("")):
    local_root, win_root = _get_root()
    if not win_root:
        raise HTTPException(503, "No data path configured. Use the settings panel to set a path.")
    if not local_root.exists():
        raise HTTPException(503, f"Configured path not accessible: {win_root}")
    target = _safe(path)
    if not target.is_dir():
        raise HTTPException(404, f"Not a directory: {path}")

    dirs, files = [], []
    for item in sorted(target.iterdir(), key=lambda p: p.name.upper()):
        rel = str(item.relative_to(local_root)).replace("\\", "/")
        ext = _effective_ext(item)
        if item.is_dir():
            dirs.append({"name": item.name, "path": rel})
        elif ext in VIEWABLE_EXTS:
            category = VIEWABLE_EXTS[ext]
            entry: dict = {
                "name": item.name,
                "path": rel,
                "ext": ext.lstrip("."),
                "category": category,
                "size_mb": round(item.stat().st_size / 1_048_576, 2),
            }
            # IMG: add sub-type badge and observation ID
            if ext == ".IMG":
                entry["type"] = _img_subtype(item.name)
                entry["obs_id"] = item.stem.split("_")[0]
            else:
                entry["type"] = ext.lstrip(".")
                entry["obs_id"] = item.stem.split("_")[0]
            files.append(entry)

    rel_str = str(target.relative_to(local_root))
    display = win_root if rel_str in (".", "") else win_root.rstrip("\\") + "\\" + rel_str.replace("/", "\\")
    return {"path": rel_str.replace("\\", "/"), "display_path": display,
            "dirs": dirs, "files": files}


@app.get("/api/local/view")
async def local_view(path: str = Query(...)):
    """View any supported local file. Returns type-tagged response."""
    target = _safe(path)
    if not target.is_file():
        raise HTTPException(404, "File not found")

    ext = target.suffix.upper()
    if ext not in VIEWABLE_EXTS:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    # ── PDS4 XML label ─────────────────────────────────────────────────
    if ext == ".XML":
        label_bytes = target.read_bytes()
        try:
            png_bytes, metadata = pds4_mod.pds4_from_local(target)
            return {
                "type": "image",
                "format": "pds4",
                "png_base64": base64.b64encode(png_bytes).decode(),
                "metadata": metadata,
                "filename": target.name,
            }
        except FileNotFoundError as e:
            # Data file missing — return label as text
            return {
                "type": "text",
                "format": "pds4_label",
                "text": label_bytes.decode("utf-8", errors="replace"),
                "filename": target.name,
                "note": str(e),
            }
        except Exception as e:
            raise HTTPException(422, f"PDS4 error: {e}")

    # ── VICAR / PDS3 image ─────────────────────────────────────────────
    if ext == ".IMG":
        cp = _cache(f"local:{path}")
        png_p = Path(str(cp) + ".png")
        meta_p = Path(str(cp) + ".json")
        if png_p.exists() and meta_p.exists():
            return {
                "type": "image",
                "format": _json.loads(meta_p.read_text()).get("image_format", "vicar"),
                "png_base64": base64.b64encode(png_p.read_bytes()).decode(),
                "metadata": _json.loads(meta_p.read_text()),
                "filename": target.name,
            }
        raw = target.read_bytes()
        try:
            png_bytes, metadata = vicar.parse_any_image(raw)
        except Exception as e:
            raise HTTPException(422, f"Image parse error ({target.name}): {e}")
        png_p.write_bytes(png_bytes)
        meta_p.write_text(_json.dumps(metadata))
        return {
            "type": "image",
            "format": metadata.get("image_format", "vicar"),
            "png_base64": base64.b64encode(png_bytes).decode(),
            "metadata": metadata,
            "filename": target.name,
        }

    # ── JPEG / GIF pass-through ────────────────────────────────────────
    if ext in IMAGE_PASSTHROUGH:
        raw = target.read_bytes()
        return {
            "type": "image",
            "format": ext.lstrip(".").lower(),
            "data_base64": base64.b64encode(raw).decode(),
            "mime_type": _mime(ext),
            "filename": target.name,
            "size_mb": round(len(raw) / 1_048_576, 2),
        }

    # ── Text / metadata files ──────────────────────────────────────────
    if ext in TEXT_EXTENSIONS or ext == ".DAT":
        raw = target.read_bytes()
        # Detect if truly binary
        try:
            text = raw.decode("ascii", errors="strict")
            is_binary = False
        except UnicodeDecodeError:
            try:
                text = raw.decode("latin-1", errors="replace")
                # Check ratio of non-printable chars
                non_print = sum(1 for c in raw if c < 9 or (13 < c < 32))
                is_binary = (non_print / max(len(raw), 1)) > 0.10
            except Exception:
                is_binary = True

        if is_binary:
            return {
                "type": "binary",
                "filename": target.name,
                "size_mb": round(len(raw) / 1_048_576, 2),
                "message": "Binary data file — cannot display as text.",
            }

        fmt = "pds3_label" if ext == ".LBL" else \
              "pds3_table" if ext == ".TAB" else \
              "pds3_catalog" if ext == ".CAT" else "text"
        return {
            "type": "text",
            "format": fmt,
            "text": text[:200_000],  # cap at 200 KB
            "filename": target.name,
            "truncated": len(raw) > 200_000,
        }

    raise HTTPException(400, f"Unhandled extension: {ext}")


# ── Archive browser ──────────────────────────────────────────────────────────

@app.get("/api/local/archive/list")
async def archive_list(path: str = Query(...)):
    """List all viewable files inside a zip/tar/gz archive."""
    target = _safe(path)
    if not target.is_file():
        raise HTTPException(404, "Archive not found")

    # Serve from disk cache if available
    cp = _cache(f"arclist:{path}:{target.stat().st_mtime_ns}")
    meta_p = Path(str(cp) + ".json")
    if meta_p.exists():
        return _json.loads(meta_p.read_text())

    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(_pool, _list_archive_sync, target)
    except Exception as e:
        raise HTTPException(422, f"Archive read error: {e}")

    result["archive_path"] = path
    meta_p.write_text(_json.dumps(result))
    return result


@app.get("/api/local/archive/view")
async def archive_view(
    path: str = Query(...),
    inner: str = Query(...),
):
    """Extract and render one file from inside an archive."""
    target = _safe(path)
    if not target.is_file():
        raise HTTPException(404, "Archive not found")

    cp = _cache(f"arcview:{path}:{inner}")
    full_cache = Path(str(cp) + ".full.json")

    # Fast path: full response cached — avoid expensive re-extraction
    if full_cache.exists():
        return _json.loads(full_cache.read_text())

    # Also check if a previous local_view run already cached png+meta
    png_p = Path(str(cp) + ".png")
    meta_p = Path(str(cp) + ".json")
    if png_p.exists() and meta_p.exists():
        meta = _json.loads(meta_p.read_text())
        result = {
            "type": "image",
            "format": meta.get("image_format", "vicar"),
            "png_base64": base64.b64encode(png_p.read_bytes()).decode(),
            "metadata": meta,
            "filename": Path(inner).name,
        }
        full_cache.write_text(_json.dumps(result))
        return result

    loop = asyncio.get_running_loop()
    try:
        raw = await loop.run_in_executor(
            _pool, _read_archive_member_sync, target, inner
        )
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(422, f"Extract error: {e}")

    try:
        result = _raw_to_response(raw, Path(inner).name, cp)
    except Exception as e:
        raise HTTPException(422, f"Render error: {e}")

    full_cache.write_text(_json.dumps(result))
    return result


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "NASA VICAR Viewer"}


# ── Static frontend ───────────────────────────────────────────────────────────

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
