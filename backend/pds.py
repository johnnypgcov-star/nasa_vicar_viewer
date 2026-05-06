"""NASA PDS / OPUS API client for Voyager 1 & 2 data."""
import httpx
import asyncio
from typing import Optional

OPUS_BASE = "https://opus.pds-rings.seti.org/opus/api"

VOYAGER_TARGETS = {
    "all": None,
    "jupiter": "Jupiter",
    "saturn": "Saturn",
    "uranus": "Uranus",
    "neptune": "Neptune",
    "titan": "Titan",
    "io": "Io",
    "europa": "Europa",
    "ganymede": "Ganymede",
    "callisto": "Callisto",
    "triton": "Triton",
    "miranda": "Miranda",
    "ariel": "Ariel",
    "umbriel": "Umbriel",
    "titania": "Titania",
    "oberon": "Oberon",
}

_http_client: Optional[httpx.AsyncClient] = None


def get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
    return _http_client


async def search_voyager(
    spacecraft: str = "both",
    target: Optional[str] = None,
    page: int = 1,
    limit: int = 24,
) -> dict:
    """
    Search Voyager images via OPUS API.
    Returns {total, page, limit, results: [{opusid, target, time, thumb_url, small_url,...}]}
    """
    start_obs = (page - 1) * limit + 1

    params: dict = {
        "mission": "Voyager",
        "limit": limit,
        "startobs": start_obs,
        "order": "time1,opusid",
    }

    if spacecraft.lower() == "voyager 1":
        params["insthost"] = "Voyager 1"
    elif spacecraft.lower() == "voyager 2":
        params["insthost"] = "Voyager 2"

    if target and target.lower() != "all":
        params["target"] = VOYAGER_TARGETS.get(target.lower(), target)

    client = get_client()

    data_params = {**params, "cols": "opusid,target,time1,instrument"}
    images_params = {**params}

    data_task = client.get(f"{OPUS_BASE}/data.json", params=data_params)
    images_task = client.get(f"{OPUS_BASE}/images/small.json", params=images_params)

    data_resp, images_resp = await asyncio.gather(data_task, images_task)
    data_resp.raise_for_status()
    images_resp.raise_for_status()

    data_json = data_resp.json()
    images_json = images_resp.json()

    # images data: list of dicts with opus_id, url (small), alt_text etc.
    img_map: dict = {}
    for item in images_json.get("data", []):
        oid = item.get("opus_id", "")
        img_map[oid] = {
            "thumb_url": item.get("url", "").replace("_small.jpg", "_thumb.jpg"),
            "small_url": item.get("url", ""),
        }

    # data rows: array of arrays, columns from data_json["columns"]
    col_names = [c.lower().replace(" ", "_").replace("(", "").replace(")", "").replace(",","") for c in data_json.get("columns", [])]
    results = []
    for row in data_json.get("page", []):
        obs: dict = {}
        for i, col in enumerate(col_names):
            obs[col] = row[i] if i < len(row) else None
        # Normalize key name
        oid = obs.get("opus_id", "")
        obs["opusid"] = oid
        obs.update(img_map.get(oid, {}))
        results.append(obs)

    return {
        "total": data_json.get("available", 0),
        "page": page,
        "limit": limit,
        "results": results,
    }


async def get_observation_files(opus_id: str) -> dict:
    """
    Get all file URLs for an observation.
    Returns {data: {obs_id: {version_key: [url, ...]}}, versions: [...]}
    """
    client = get_client()
    resp = await client.get(f"{OPUS_BASE}/files/{opus_id}.json")
    resp.raise_for_status()
    return resp.json()


async def get_full_preview(opus_id: str) -> dict:
    """Get full-size preview image for an observation."""
    client = get_client()
    resp = await client.get(
        f"{OPUS_BASE}/images/full.json",
        params={"opusid": opus_id},
    )
    resp.raise_for_status()
    data = resp.json()
    items = data.get("data", [])
    return items[0] if items else {}


async def fetch_vicar_file(url: str) -> bytes:
    """Download a VICAR (.IMG) file from PDS."""
    client = get_client()
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.content


async def get_observation_metadata(opus_id: str) -> dict:
    """Get all metadata categories for an observation."""
    client = get_client()
    resp = await client.get(f"{OPUS_BASE}/metadata/{opus_id}.json")
    resp.raise_for_status()
    return resp.json()
