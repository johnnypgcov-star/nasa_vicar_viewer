# NASA VICAR Viewer — User Manual

A Docker-based web viewer for NASA Voyager 1 & 2 VICAR / PDS3 / PDS4 planetary imagery. Browse live data from the NASA OPUS archive or a local planetary data collection — all from your browser.

---

## Contents

1. [Requirements](#requirements)
2. [Starting and stopping](#starting-and-stopping)
3. [First-time setup — local path](#first-time-setup--local-path)
4. [Browse NASA tab](#browse-nasa-tab)
5. [Local Files tab](#local-files-tab)
6. [Upload VICAR tab](#upload-vicar-tab)
7. [About tab](#about-tab)
8. [Supported file formats](#supported-file-formats)
9. [Caching](#caching)
10. [Troubleshooting](#troubleshooting)

---

## Requirements

- **Docker Desktop** (Windows) with the container engine running
- A local planetary data collection, such as VGISS volumes from the PDS archive (optional — only needed for the Local Files tab)
- The drive containing your data must be shared in Docker Desktop under Settings → Resources → File Sharing

---

## Starting and stopping

From the project directory:

```powershell
# Start in background
docker compose up -d

# Stop
docker compose down

# Rebuild after code changes
docker compose build
docker compose up -d
```

Once running, open **http://localhost:85** in your browser.

---

## First-time setup — local path

Before you can use the Local Files tab, you need to tell the viewer where your data lives.

1. Open the **Local Files** tab — the path editor opens automatically on first use.
2. Type the Windows path to your data root, for example `J:\ASTRONOMY`.
3. Click **Save** or press **Enter**.

The path is saved to a persistent Docker named volume (`vicar_config`) and restored every time the container starts — you only need to do this once.

To change the path later, click the **✏** pencil icon at the top of the folder tree panel.

### Adding drives

The default `docker-compose.yml` mounts the `J:` drive. To browse a different drive, add it to the `volumes:` section and rebuild:

```yaml
volumes:
  - "D:/:/data/D:ro"
  - "J:/:/data/J:ro"
```

Then run `docker compose build && docker compose up -d`.

---

## Browse NASA tab

Searches the NASA OPUS (Outer Planets Unified Search) system live.

### Filters

**Spacecraft** — three buttons in the left sidebar:

| Button | Shows |
|--------|-------|
| Both | All Voyager observations |
| Voyager 1 | V1 only |
| Voyager 2 | V2 only |

Clicking a spacecraft button triggers a new search immediately.

**Target** — dropdown below the spacecraft buttons:

| Group | Bodies |
|-------|--------|
| Gas giants | Jupiter, Saturn, Uranus, Neptune |
| Jupiter moons | Io, Europa, Ganymede, Callisto |
| Saturn moons | Titan |
| Uranus / Neptune moons | Miranda, Ariel, Umbriel, Titania, Oberon, Triton |

Changing the target dropdown triggers a new search immediately.

**Search button** — manually re-runs the current filters; useful after returning to the tab.

### Image grid

Results appear as thumbnail cards showing the observation ID, target, observation date, and spacecraft badge. The stats box shows the total match count and current page.

### Lightbox

Click any card to open the lightbox:

- **Preview image** — browse-quality JPEG from the PDS archive
- **Load Raw VICAR** — fetches the full calibrated `.IMG` file, parses it, and displays the raw greyscale science image alongside its VICAR label fields (dimensions, pixel format, byte order)
- **View on OPUS ↗** — opens the observation on the NASA OPUS website in a new tab

### Pagination

Use **← Prev** and **Next →** to page through results.

---

## Local Files tab

Browse your local planetary data collection directly from the viewer.

### Layout

Three panels, side by side:

| Panel | Purpose |
|-------|---------|
| Folder tree (left) | Expandable directory tree rooted at your configured path |
| File list (centre) | All viewable files in the selected folder, grouped by observation ID |
| Viewer (right) | Displays the selected file |

Click any folder in the tree to load its contents in the file list. Click any file button to view it.

### Viewing images

`.IMG` files are parsed as VICAR or PDS3 and rendered as a greyscale PNG. A metadata panel beneath the image shows key header fields: dimensions (NL × NS × NB), pixel format, data organisation, byte order, and label size.

`.JPG` and `.GIF` browse previews are displayed directly without parsing.

File buttons are colour-coded by image type:

| Colour | Type |
|--------|------|
| Blue | CALIB — radiometrically calibrated |
| Green | CLEANED — geometric distortion removed |
| Grey | RAW — unprocessed |
| Gold | GEOMED / GEOMA — geometrically corrected |

### Viewing text files

`.LBL`, `.TAB`, `.CAT`, `.ASC`, `.TXT`, `.HTM`, `.HTML` files open in a monospace text viewer. A format badge in the toolbar labels the file type. Use the **Wrap** button to toggle word wrap. Files larger than 200 KB are truncated with a warning banner.

### Viewing archives

Click any archive file button (shown with a 📦 icon) to open the archive browser. The viewer lists all images and text files inside the archive without requiring manual extraction.

- Use the **filter bar** at the top to search by filename, observation ID, or subdirectory
- Click any listed file to extract and view it in the viewer panel
- Use **← Folder** to return to the regular file list

> **Large archives:** The first time you open a VGISS `.tar.gz` volume (typically 700 MB – 1.5 GB) the container must decompress the entire archive. This takes one to two minutes. Subsequent opens use the disk cache and are instant.

Supported archive formats: `.zip` · `.tar` · `.tar.gz` · `.tgz` · `.tar.bz2` · `.tar.xz` · `.gz` · `.bz2`

### PDS4 files

`.xml` PDS4 labels are rendered to a PNG image if the corresponding data file is in the same directory. If the data file is missing, the label XML is shown as text with a note.

---

## Upload VICAR tab

Upload a file from your computer to parse and view it — no need for it to be in your mounted data folder.

1. Drag and drop a file onto the drop zone, or click the zone to open a file picker.
2. Accepted types: `.img` · `.IMG` · `.vic` · `.VIC` · `.vicar` · `.xml` · `.XML` · `.lbl` · `.LBL`
3. The file is parsed and the image (or label metadata for `.xml`) is displayed immediately.

> PDS4 `.xml` files uploaded without their co-located data file will return label metadata only — no image is rendered.

---

## About tab

Provides background on:

- The Voyager 1 & 2 programme and the images it captured
- The VICAR image format and its key header fields
- The NASA OPUS and PDS data sources used by this viewer

---

## Supported file formats

| Extension | Rendering |
|-----------|-----------|
| `.IMG` | VICAR or PDS3 auto-detected → greyscale PNG |
| `.VIC` / `.VICAR` | VICAR → PNG |
| `.JPG` / `.JPEG` | Pass-through JPEG |
| `.GIF` | Pass-through GIF |
| `.XML` | PDS4 label + data file → PNG; or label text if data absent |
| `.LBL` | PDS3 detached label — monospace text viewer |
| `.TAB` | ASCII table — monospace text viewer |
| `.CAT` | PDS3 catalogue file — monospace text viewer |
| `.ASC` | ASCII data — monospace text viewer |
| `.TXT` / `.HTM` / `.HTML` | Plain text viewer |
| `.DAT` | Text viewer if ASCII; binary notice if non-printable content detected |
| `.zip` | Archive browser |
| `.tar` / `.tar.gz` / `.tgz` | Archive browser |
| `.tar.bz2` / `.tar.xz` | Archive browser |
| `.gz` / `.bz2` | Archive browser (or raw single-file extraction if not a tar wrapper) |

---

## Caching

The container uses a 512 MB RAM disk (`/tmp/vicar_cache`) to cache:

- Parsed PNG images and their metadata (keyed by file path or URL)
- Archive listings (keyed by path + modification time)
- Full extracted-file responses (avoids re-extraction on revisit)

The cache is cleared when the container restarts (`docker compose down` then `docker compose up -d`). Your configured root path is **not** stored in the cache — it lives on the persistent `vicar_config` named volume and is unaffected by restarts.

---

## Troubleshooting

**"No data path configured"**
Open the Local Files tab and click the ✏ pencil button. Enter your data path (e.g. `J:\ASTRONOMY`) and click Save.

**"Configured path not accessible"**
The saved path cannot be reached inside the container. Check two things:
1. The drive is listed in `docker-compose.yml` under `volumes:` (e.g. `J:/:/data/J:ro`)
2. Docker Desktop has file-sharing permission for that drive: Settings → Resources → File Sharing → add the drive → Apply & Restart

**Archive scan is slow on first open**
Large VGISS `.tar.gz` volumes must be fully decompressed before they can be listed. This is expected behaviour and only happens once per container session. The result is cached for all subsequent opens.

**Blank image or parse error on a `.IMG` file**
A small number of early Voyager files use VICAR variants that may trigger a parse error. The error detail is shown in the metadata panel. If the file has a companion `.LBL` label, try opening that instead to inspect the header.

**OPUS search returns no results**
The NASA OPUS API is a live internet service and occasionally has brief outages. Wait a minute and try again. You can verify the service is up at https://opus.pds-rings.seti.org

---

Built by John Gilbert &mdash; 2026
