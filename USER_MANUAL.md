# NASA VICAR Viewer — User Manual

A Docker-based viewer for NASA Voyager 1 & 2 VICAR/PDS3/PDS4 planetary imagery. Browse live data from the NASA OPUS archive or your local `J:\ASTRONOMY` collection.

---

## Requirements

- Docker Desktop (Windows) with the container engine running
- Local astronomy collection at `J:\ASTRONOMY` (optional — only needed for the Local Files tab)

---

## Starting and stopping

From the project directory (`D:\code\nasa_vicar_viewer`):

```powershell
# Start (runs in background)
docker compose up -d

# Stop
docker compose down

# Rebuild after code changes
docker compose build
docker compose up -d
```

Once running, open your browser at **http://localhost:85**

---

## Interface overview

The app has four tabs in the top navigation bar:

| Tab | Purpose |
|-----|---------|
| Browse NASA | Search and view images from the live NASA OPUS archive |
| Local Files | Browse your `J:\ASTRONOMY` collection |
| Upload VICAR | Upload a local `.IMG` or `.VIC` file to parse and view |
| About | Background on the Voyager programme and VICAR format |

---

## Browse NASA tab

Searches the NASA OPUS (Outer Planets Unified Search) system in real time.

### Filtering

**Spacecraft** — click one of the three buttons in the sidebar:
- `Both` — all Voyager observations
- `Voyager 1` — V1 only
- `Voyager 2` — V2 only

Clicking a spacecraft button immediately triggers a new search.

**Target** — choose a body from the dropdown:
- Gas giants: Jupiter, Saturn, Uranus, Neptune
- Jupiter moons: Io, Europa, Ganymede, Callisto
- Saturn moons: Titan
- Uranus/Neptune moons: Miranda, Ariel, Umbriel, Titania, Oberon, Triton

Changing the target dropdown immediately triggers a new search.

**Search button** — manually re-run the current filter combination (useful after navigating away and returning).

### Image grid

Results appear as thumbnail cards. Each card shows:
- Observation ID
- Target body
- Spacecraft

### Lightbox

Click any thumbnail to open the lightbox:
- Shows the browse-quality preview image
- **Load Raw VICAR** button — fetches and parses the full calibrated VICAR `.IMG` from PDS; displays the raw science image alongside VICAR metadata (dimensions, format, byte order, label fields)
- **View on OPUS ↗** — opens the observation's page on the NASA OPUS website in a new tab

### Pagination

Use `← Prev` / `Next →` buttons at the bottom to page through results. The stats box shows the total number of matching images and current page.

---

## Local Files tab

Browse any local directory mounted into the container, directly from the viewer.

### Setting the root path

The first time you open the Local Files tab (or if no path has been saved yet), the path editor opens automatically. Type the Windows path to your data folder — for example `J:\ASTRONOMY` — and click **Save** (or press **Enter**).

The path is saved persistently on the server and survives container restarts. To change it later, click the **✏** pencil icon next to the path label at the top of the folder tree. Press **Escape** to cancel without saving.

> The Docker container mounts `J:\` at `/data/J` internally. You can browse any subdirectory under `J:\` by entering its full Windows path (e.g. `J:\ASTRONOMY\VGISS_5101`). To add other drives, add them to the `volumes:` section of `docker-compose.yml` and rebuild.

### Layout

Three panels side by side:

1. **Folder tree** (left) — expandable directory tree rooted at your configured path. Click any folder to load its contents.
2. **File list** (centre) — lists all viewable files in the selected folder. Files are colour-coded by type. Click a file to view it.
3. **Viewer** (right) — displays the selected file.

### Viewing images

`.IMG` files are parsed as VICAR or PDS3 and displayed as a greyscale PNG. A metadata panel below the image shows key VICAR header fields (dimensions, format, byte order, label size).

`.JPG` and `.GIF` files are displayed directly.

### Viewing text files

`.LBL`, `.TAB`, `.CAT`, `.ASC`, `.TXT`, `.HTM`, `.HTML` files open in a monospace text viewer. A format badge in the toolbar indicates the file type (e.g. `PDS3 Label`, `ASCII Table`). Use the **Wrap** button to toggle word wrap. Files larger than 200 KB are truncated with a warning.

### Viewing archives (`.tar.gz`, `.zip`, etc.)

Click any archive file to open the archive browser. This lists all viewable files inside the archive. Click a file inside the archive to extract and view it.

> **Note:** The first time you open a large `.tar.gz` archive (700 MB – 1.5 GB) it must be fully decompressed, which takes a minute or two. Subsequent opens are instant thanks to the disk cache.

Supported archive formats: `.zip`, `.tar`, `.tar.gz`, `.tgz`, `.tar.bz2`, `.tar.xz`, `.gz`, `.bz2`

### PDS4 files

`.xml` PDS4 labels are rendered to PNG if the corresponding data file is in the same directory. If the data file is missing, the label text is shown instead.

---

## Upload VICAR tab

Upload a local file directly from your computer without it needing to be in `J:\ASTRONOMY`.

1. Drag and drop a file onto the drop zone, or click the zone to open a file picker.
2. Accepted types: `.img`, `.IMG`, `.vic`, `.VIC`, `.vicar`, `.xml`, `.XML`, `.lbl`, `.LBL`
3. The file is parsed server-side and the image (or label metadata for `.xml`) is displayed immediately.

> PDS4 `.xml` uploads without a co-located data file will return label metadata only — no image.

---

## Supported file formats

| Extension | How it is rendered |
|-----------|-------------------|
| `.IMG` | VICAR or PDS3 auto-detected → PNG |
| `.VIC` / `.VICAR` | VICAR → PNG |
| `.JPG` / `.JPEG` | Pass-through JPEG |
| `.GIF` | Pass-through GIF |
| `.XML` | PDS4 label + data → PNG; or label text if data file absent |
| `.LBL` | PDS3 detached label — text viewer |
| `.TAB` | ASCII table — text viewer |
| `.CAT` | PDS3 catalogue file — text viewer |
| `.ASC` | ASCII data — text viewer |
| `.TXT` | Plain text |
| `.HTM` / `.HTML` | HTML source as plain text |
| `.DAT` | Text if ASCII, otherwise reported as binary |
| `.zip` | Archive browser |
| `.tar` / `.tar.gz` / `.tgz` | Archive browser |
| `.tar.bz2` / `.tar.xz` | Archive browser |
| `.gz` / `.bz2` | Archive browser (or raw file if not a tar wrapper) |

---

## Caching

Parsed images and archive listings are cached in a 512 MB RAM disk (`/tmp/vicar_cache`) inside the container. The cache is cleared each time the container restarts. This means:

- Re-opening the same `.IMG` or archive file is instant after the first load.
- Restarting the container (`docker compose down && docker compose up -d`) clears all caches.

---

## Troubleshooting

**"No data path configured"** — Open the Local Files tab and click the ✏ button to enter your data path (e.g. `J:\ASTRONOMY`), then click Save.

**"Configured path not accessible"** — The path you saved is not reachable inside the container. Check that the drive is mounted in `docker-compose.yml` under `volumes:`. Docker Desktop must also have access to that drive: go to Settings → Resources → File Sharing and add the drive, then restart Docker.

**Archive takes a long time to open** — Large `.tar.gz` VGISS volumes must be fully decompressed on first access. This is expected and only happens once per container session.

**Blank image / parse error** — Some early Voyager files use uncommon VICAR variants. Check the error message in the metadata panel for details.

**OPUS search returns no results** — The NASA OPUS API is a live service and occasionally has outages. Try again after a minute, or check https://opus.pds-rings.seti.org directly.
