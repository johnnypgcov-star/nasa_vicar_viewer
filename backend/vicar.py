"""VICAR (Video Image Communication And Retrieval) and PDS3 image parser."""
import re
import numpy as np
from PIL import Image
from io import BytesIO

# ── Shared helpers ────────────────────────────────────────────────────────────

def _normalize_array(arr: np.ndarray) -> np.ndarray:
    """Stretch to 0-255 uint8 using 1st–99th percentile."""
    a = arr.astype(np.float32)
    lo, hi = float(np.percentile(a, 1)), float(np.percentile(a, 99))
    if hi > lo:
        a = np.clip((a - lo) / (hi - lo) * 255.0, 0, 255.0)
    else:
        a = np.zeros_like(a)
    return a.astype(np.uint8)


def _to_png(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


# ── Format detection ──────────────────────────────────────────────────────────

def detect_format(data: bytes) -> str:
    """Return 'vicar', 'pds3', 'pds4', or 'unknown'."""
    head = data[:512].decode("ascii", errors="replace")
    if re.search(r"LBLSIZE\s*=", head):
        return "vicar"
    if re.search(r"PDS_VERSION_ID\s*=\s*PDS3", head):
        return "pds3"
    if data[:5] in (b"<?xml", b"<Prod") or b"PDS4" in data[:256]:
        return "pds4"
    return "unknown"


def parse_any_image(data: bytes) -> tuple[bytes, dict]:
    """Auto-detect VICAR/PDS3 format and return (PNG bytes, metadata)."""
    fmt = detect_format(data)
    if fmt == "vicar":
        return vicar_to_png_bytes(data)
    if fmt == "pds3":
        return pds3_to_png_bytes(data)
    raise ValueError(f"Cannot parse image: unrecognised format ({fmt})")


# ── VICAR ─────────────────────────────────────────────────────────────────────

VICAR_DTYPE_MAP = {
    "BYTE": np.uint8,
    "HALF": np.int16,
    "FULL": np.int32,
    "REAL": np.float32,
    "DOUB": np.float64,
}
VICAR_SIZE_MAP = {"BYTE": 1, "HALF": 2, "FULL": 4, "REAL": 4, "DOUB": 8}


def parse_vicar_label(data: bytes) -> tuple[dict, int]:
    header = data[:100].decode("ascii", errors="replace")
    m = re.search(r"LBLSIZE\s*=\s*(\d+)", header)
    if not m:
        raise ValueError("Not a valid VICAR file: LBLSIZE not found")
    lblsize = int(m.group(1))
    label_text = data[:lblsize].decode("ascii", errors="replace").replace("\x00", " ")
    params: dict = {}
    for match in re.finditer(
        r"(\w+)\s*=\s*(?:'([^']*)'|(-?\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?))",
        label_text,
    ):
        key = match.group(1)
        if match.group(2) is not None:
            params[key] = match.group(2).strip()
        else:
            val = match.group(3)
            try:
                params[key] = int(val)
            except ValueError:
                params[key] = float(val)
    return params, lblsize


def vicar_to_png_bytes(data: bytes) -> tuple[bytes, dict]:
    params, lblsize = parse_vicar_label(data)

    nl = int(params.get("NL", params.get("N2", 0)))
    ns = int(params.get("NS", params.get("N1", 0)))
    nb = int(params.get("NB", params.get("N3", 1)))
    fmt = str(params.get("FORMAT", "BYTE")).upper()
    org = str(params.get("ORG", "BSQ")).upper()
    nbb = int(params.get("NBB", 0))
    nlb = int(params.get("NLB", 0))
    recsize = int(params.get("RECSIZE", ns))
    intfmt = str(params.get("INTFMT", "LOW")).upper()

    if nl == 0 or ns == 0:
        raise ValueError(f"Invalid VICAR dimensions: NL={nl}, NS={ns}")

    dtype = VICAR_DTYPE_MAP.get(fmt, np.uint8)
    pixel_size = VICAR_SIZE_MAP.get(fmt, 1)
    offset = lblsize + nlb * recsize

    byteorder = "|" if fmt == "BYTE" else ("<" if intfmt == "LOW" else ">")
    pixel_dtype = np.dtype(dtype).newbyteorder(byteorder)
    img_bytes = data[offset:]

    if org == "BSQ":
        if nbb > 0:
            line_bytes = nbb + ns * pixel_size
            band_arrays = []
            for b in range(nb):
                lines = []
                band_offset = b * nl * line_bytes
                for ln in range(nl):
                    s = band_offset + ln * line_bytes + nbb
                    lines.append(np.frombuffer(img_bytes[s: s + ns * pixel_size], dtype=pixel_dtype))
                band_arrays.append(np.vstack(lines))
        else:
            total = nl * ns * nb
            flat = np.frombuffer(img_bytes[: total * pixel_size], dtype=pixel_dtype)
            band_arrays = [flat[b * nl * ns: (b + 1) * nl * ns].reshape(nl, ns) for b in range(nb)]
    elif org == "BIL":
        line_bytes = ns * pixel_size * nb + nbb
        band_arrays = [np.zeros((nl, ns), dtype=pixel_dtype) for _ in range(nb)]
        for ln in range(nl):
            for b in range(nb):
                s = ln * line_bytes + nbb + b * ns * pixel_size
                band_arrays[b][ln] = np.frombuffer(img_bytes[s: s + ns * pixel_size], dtype=pixel_dtype)
    else:  # BIP
        pixel_bytes = nb * pixel_size + nbb
        band_arrays = [np.zeros((nl, ns), dtype=pixel_dtype) for _ in range(nb)]
        for ln in range(nl):
            for smp in range(ns):
                s = (ln * ns + smp) * pixel_bytes + nbb
                for b in range(nb):
                    raw = img_bytes[s + b * pixel_size: s + (b + 1) * pixel_size]
                    band_arrays[b][ln, smp] = np.frombuffer(raw, dtype=pixel_dtype)[0]

    if nb == 1:
        img = Image.fromarray(_normalize_array(band_arrays[0]), "L")
    elif nb == 3:
        rgb = np.stack([_normalize_array(band_arrays[i]) for i in range(3)], axis=-1)
        img = Image.fromarray(rgb, "RGB")
    else:
        img = Image.fromarray(_normalize_array(band_arrays[0]), "L")

    return _to_png(img), {
        "nl": nl, "ns": ns, "nb": nb,
        "format": fmt, "org": org,
        "lblsize": lblsize, "intfmt": intfmt,
        "image_format": "vicar",
        "raw_label": dict(params),
    }


# ── PDS3 ──────────────────────────────────────────────────────────────────────

def _odl_scalar(s: str):
    s = s.strip().strip('"')
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _parse_odl_value(raw: str):
    s = raw.strip()
    # Strip trailing inline comments
    if "/*" in s:
        s = s[:s.index("/*")].strip()
    # Quoted string
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    # Value with <UNIT>: e.g.  800 <BYTES>  — keep just the number
    m = re.match(r"^(-?\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?)\s*<[^>]+>$", s)
    if m:
        return _odl_scalar(m.group(1))
    # Sequence: (a, b, c)
    if s.startswith("(") and s.endswith(")"):
        inner = s[1:-1]
        return [_odl_scalar(p.strip().strip('"')) for p in inner.split(",")]
    return _odl_scalar(s)


def _parse_pds3_odl(text: str) -> tuple[dict, dict]:
    """Return (top_level_params, image_object_params)."""
    top: dict = {}
    image: dict = {}
    current_obj = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("/*"):
            continue
        if line.upper() == "END":
            break
        # Object markers
        if re.match(r"^OBJECT\s*=\s*IMAGE\b", line, re.I):
            current_obj = "IMAGE"
            continue
        if re.match(r"^END_OBJECT", line, re.I):
            current_obj = None
            continue
        if re.match(r"^OBJECT\s*=", line, re.I):
            current_obj = "OTHER"
            continue
        if current_obj == "OTHER":
            continue
        # key = value
        m = re.match(r"^(\^?\w+)\s*=\s*(.+)$", line)
        if not m:
            continue
        key = m.group(1).upper()
        val = _parse_odl_value(m.group(2))
        if current_obj == "IMAGE":
            image[key] = val
        else:
            top[key] = val

    return top, image


def _pds3_image_offset(top: dict, label_text_len: int) -> int:
    record_bytes = int(top.get("RECORD_BYTES", 512) or 512)
    ptr = top.get("^IMAGE")
    if ptr is None:
        # Pad label to next record boundary
        return ((label_text_len + record_bytes - 1) // record_bytes) * record_bytes if record_bytes else label_text_len
    val = int(ptr) if isinstance(ptr, (int, float)) else 1
    return (val - 1) * record_bytes


# PDS3 sample-type → (byteorder, numpy base dtype string)
_PDS3_DTYPES: dict[str, tuple[str, str]] = {
    "UNSIGNED_INTEGER":       (">", "u"),
    "INTEGER":                (">", "i"),
    "MSB_UNSIGNED_INTEGER":   (">", "u"),
    "MSB_INTEGER":            (">", "i"),
    "LSB_UNSIGNED_INTEGER":   ("<", "u"),
    "LSB_INTEGER":            ("<", "i"),
    "PC_UNSIGNED_INTEGER":    ("<", "u"),
    "PC_INTEGER":             ("<", "i"),
    "SUN_UNSIGNED_INTEGER":   (">", "u"),
    "SUN_INTEGER":            (">", "i"),
    "MAC_UNSIGNED_INTEGER":   (">", "u"),
    "MAC_INTEGER":            (">", "i"),
    "VAX_UNSIGNED_INTEGER":   ("<", "u"),
    "VAX_INTEGER":            ("<", "i"),
    "IEEE_REAL":              (">", "f"),
    "SUN_REAL":               (">", "f"),
    "MAC_REAL":               (">", "f"),
    "PC_REAL":                ("<", "f"),
    "VAX_REAL":               ("<", "f"),
}


def pds3_to_png_bytes(data: bytes) -> tuple[bytes, dict]:
    """Parse a PDS3 embedded-label .IMG file → (PNG bytes, metadata)."""
    label_bytes = min(131072, len(data))
    text = data[:label_bytes].decode("ascii", errors="replace")

    end_m = re.search(r"^\s*END\s*$", text, re.MULTILINE)
    if not end_m:
        raise ValueError("PDS3 END marker not found")

    label_text = text[:end_m.end()]
    top, image_params = _parse_pds3_odl(label_text)

    nl = int(image_params.get("LINES", image_params.get("LINE", 0)))
    ns = int(image_params.get("LINE_SAMPLES", image_params.get("SAMPLES", 0)))
    nb = int(image_params.get("BANDS", 1))
    bits = int(image_params.get("SAMPLE_BITS", 8))
    sample_type = str(image_params.get("SAMPLE_TYPE", "UNSIGNED_INTEGER")).upper()
    band_storage = str(image_params.get("BAND_STORAGE_TYPE", "BAND_SEQUENTIAL")).upper()

    if nl == 0 or ns == 0:
        raise ValueError(f"PDS3 invalid dimensions: LINES={nl}, LINE_SAMPLES={ns}")

    byteorder, base_kind = _PDS3_DTYPES.get(sample_type, (">", "u"))
    nbytes = bits // 8
    dtype_str = f"{byteorder}{base_kind}{nbytes}"
    try:
        pixel_dtype = np.dtype(dtype_str)
    except TypeError:
        pixel_dtype = np.dtype(f">{base_kind}{nbytes}")

    data_offset = _pds3_image_offset(top, end_m.end())
    img_data = data[data_offset:]
    total = nl * ns * nb
    flat = np.frombuffer(img_data[: total * nbytes], dtype=pixel_dtype).astype(np.float32)

    if nb == 1:
        arr = flat.reshape(nl, ns)
        img = Image.fromarray(_normalize_array(arr), "L")
    elif nb == 3:
        if "LINE_INTERLEAVED" in band_storage or "BIL" in band_storage:
            arr = flat.reshape(nl, nb, ns)
            rgb = np.stack([_normalize_array(arr[:, i, :]) for i in range(3)], axis=-1)
        elif "SAMPLE_INTERLEAVED" in band_storage or "BIP" in band_storage:
            arr = flat.reshape(nl, ns, nb)
            rgb = np.stack([_normalize_array(arr[:, :, i]) for i in range(3)], axis=-1)
        else:  # BSQ / BAND_SEQUENTIAL
            arr = flat.reshape(nb, nl, ns)
            rgb = np.stack([_normalize_array(arr[i]) for i in range(3)], axis=-1)
        img = Image.fromarray(rgb, "RGB")
    else:
        arr = flat[: nl * ns].reshape(nl, ns)
        img = Image.fromarray(_normalize_array(arr), "L")

    all_params = {**top, **{f"IMAGE.{k}": v for k, v in image_params.items()}}
    return _to_png(img), {
        "nl": nl, "ns": ns, "nb": nb,
        "format": f"PDS3/{sample_type}",
        "sample_bits": bits,
        "band_storage": band_storage,
        "data_offset": data_offset,
        "image_format": "pds3",
        "raw_label": all_params,
    }
