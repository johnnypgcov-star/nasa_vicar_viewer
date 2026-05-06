"""PDS4 XML label parser and image extractor."""
import re
import numpy as np
from pathlib import Path
from PIL import Image
from io import BytesIO
from xml.etree import ElementTree as ET

from vicar import _normalize_array, _to_png

# PDS4 element data-type → (byteorder, numpy dtype)
_PDS4_DTYPES: dict[str, tuple[str, type]] = {
    "IEEE754MSBSingle":   (">", np.float32),
    "IEEE754MSBDouble":   (">", np.float64),
    "IEEE754LSBSingle":   ("<", np.float32),
    "IEEE754LSBDouble":   ("<", np.float64),
    "SignedByte":         ("|", np.int8),
    "UnsignedByte":       ("|", np.uint8),
    "SignedMSB2":         (">", np.int16),
    "UnsignedMSB2":       (">", np.uint16),
    "SignedLSB2":         ("<", np.int16),
    "UnsignedLSB2":       ("<", np.uint16),
    "SignedMSB4":         (">", np.int32),
    "UnsignedMSB4":       (">", np.uint32),
    "SignedLSB4":         ("<", np.int32),
    "UnsignedLSB4":       ("<", np.uint32),
    "SignedMSB8":         (">", np.int64),
    "UnsignedMSB8":       (">", np.uint64),
    "SignedLSB8":         ("<", np.int64),
    "UnsignedLSB8":       ("<", np.uint64),
    # Aliases used in older PDS4 labels
    "IEEE754MSBSingle_4": (">", np.float32),
    "IEEE754LSBSingle_4": ("<", np.float32),
}

# Strip namespace from tag: {uri}tag → tag
_NS_RE = re.compile(r"\{[^}]+\}")


def _tag(el: ET.Element) -> str:
    return _NS_RE.sub("", el.tag)


def _find(el: ET.Element, *tags: str) -> ET.Element | None:
    """Recursively find first element matching any of the given local names."""
    for child in el:
        if _tag(child) in tags:
            return child
        found = _find(child, *tags)
        if found is not None:
            return found
    return None


def _findall(el: ET.Element, *tags: str) -> list[ET.Element]:
    results = []
    for child in el:
        if _tag(child) in tags:
            results.append(child)
        results.extend(_findall(child, *tags))
    return results


def _text(el: ET.Element | None, default: str = "") -> str:
    return (el.text or default).strip() if el is not None else default


def parse_pds4_label(xml_bytes: bytes) -> dict:
    """Parse a PDS4 XML label and extract key metadata."""
    root = ET.fromstring(xml_bytes)

    # Identification
    id_area = _find(root, "Identification_Area")
    lid = _text(_find(id_area, "logical_identifier")) if id_area is not None else ""
    version = _text(_find(id_area, "version_id")) if id_area is not None else ""
    title = _text(_find(id_area, "title")) if id_area is not None else ""

    # File references
    file_areas = _findall(root, "File_Area_Observational",
                          "File_Area_Observational_Supplemental",
                          "File_Area_Browse")
    files = []
    arrays = []

    for fa in file_areas:
        file_el = _find(fa, "File")
        fname = _text(_find(file_el, "file_name")) if file_el is not None else ""
        files.append(fname)

        # Look for Array_2D_Image, Array_3D_Image, Array_2D, Array_3D
        for arr_el in _findall(fa, "Array_2D_Image", "Array_3D_Image",
                               "Array_2D", "Array_3D", "Array"):
            offset_el = _find(arr_el, "offset")
            offset = int(_text(offset_el, "0"))
            axes_els = _findall(arr_el, "Axis_Array")
            axes = []
            for ax in sorted(axes_els, key=lambda e: int(_text(_find(e, "sequence_number"), "1"))):
                axes.append({
                    "name": _text(_find(ax, "axis_name")),
                    "elements": int(_text(_find(ax, "elements"), "0")),
                })
            elem_el = _find(arr_el, "Element_Array")
            data_type = _text(_find(elem_el, "data_type")) if elem_el is not None else ""
            scaling = float(_text(_find(elem_el, "scaling_factor"), "1.0"))
            offset_val = float(_text(_find(elem_el, "value_offset"), "0.0"))
            arrays.append({
                "file": fname,
                "byte_offset": offset,
                "axes": axes,
                "data_type": data_type,
                "scaling_factor": scaling,
                "value_offset": offset_val,
                "tag": _tag(arr_el),
            })

    return {
        "lid": lid,
        "version": version,
        "title": title,
        "files": files,
        "arrays": arrays,
    }


def pds4_to_png_bytes(label_bytes: bytes, data_bytes: bytes) -> tuple[bytes, dict]:
    """
    Parse a PDS4 label + binary data blob and return (PNG bytes, metadata).
    Handles 2D and 3D arrays; first 2D slice used for 3D.
    """
    meta = parse_pds4_label(label_bytes)
    arrays = meta["arrays"]

    if not arrays:
        raise ValueError("No image arrays found in PDS4 label")

    # Prefer Array_2D_Image, then any Array
    img_arr = next((a for a in arrays if "Image" in a["tag"]), arrays[0])

    axes = img_arr["axes"]
    if len(axes) < 2:
        raise ValueError(f"Not enough axes in PDS4 array: {axes}")

    # Last two axes = (lines, samples); if 3D first axis is band/frame
    if len(axes) == 2:
        nl = axes[0]["elements"]
        ns = axes[1]["elements"]
        nb = 1
    else:
        nb = axes[0]["elements"]
        nl = axes[1]["elements"]
        ns = axes[2]["elements"]

    data_type = img_arr["data_type"]
    byteorder, base_dtype = _PDS4_DTYPES.get(data_type, (">", np.uint8))
    pixel_dtype = np.dtype(base_dtype).newbyteorder(byteorder)
    pixel_size = pixel_dtype.itemsize

    byte_offset = img_arr["byte_offset"]
    scaling = img_arr["scaling_factor"]
    val_offset = img_arr["value_offset"]

    total = nl * ns * nb
    raw_slice = data_bytes[byte_offset: byte_offset + total * pixel_size]
    flat = np.frombuffer(raw_slice, dtype=pixel_dtype).astype(np.float64)
    flat = flat * scaling + val_offset

    if nb == 1:
        arr = flat.reshape(nl, ns)
        img = Image.fromarray(_normalize_array(arr), "L")
    elif nb == 3:
        arr = flat.reshape(nb, nl, ns)
        rgb = np.stack([_normalize_array(arr[i]) for i in range(3)], axis=-1)
        img = Image.fromarray(rgb, "RGB")
    else:
        # Show first band
        arr = flat[:nl * ns].reshape(nl, ns)
        img = Image.fromarray(_normalize_array(arr), "L")

    return _to_png(img), {
        "nl": nl, "ns": ns, "nb": nb,
        "format": f"PDS4/{data_type}",
        "data_type": data_type,
        "byte_offset": byte_offset,
        "scaling_factor": scaling,
        "value_offset": val_offset,
        "image_format": "pds4",
        "raw_label": meta,
    }


def pds4_from_local(label_path: Path) -> tuple[bytes, dict]:
    """Load a PDS4 label + its referenced data file from the local filesystem."""
    label_bytes = label_path.read_bytes()
    meta = parse_pds4_label(label_bytes)

    # Find data file
    data_file = None
    for fname in meta["files"]:
        candidate = label_path.parent / fname
        if candidate.exists():
            data_file = candidate
            break

    if data_file is None:
        raise FileNotFoundError(
            f"PDS4 data file not found. Label references: {meta['files']}"
        )

    data_bytes = data_file.read_bytes()
    return pds4_to_png_bytes(label_bytes, data_bytes)
