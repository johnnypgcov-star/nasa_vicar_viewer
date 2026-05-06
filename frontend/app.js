/* NASA VICAR Viewer — frontend logic */
const API = "";  // same origin

let state = {
  spacecraft: "both",
  target: "all",
  page: 1,
  total: 0,
  limit: 24,
  currentObs: null,
};

// ── View switching ────────────────────────────────────────────────────────
function showView(name) {
  document.querySelectorAll(".view").forEach(v => (v.style.display = "none"));
  const el = document.getElementById(`view-${name}`);
  // local view uses grid, others use flex/block
  if (name === "local") {
    el.style.display = "grid";
    initLocalBrowser();
  } else if (name === "browse") {
    el.style.display = "flex";
  } else {
    el.style.display = "block";
  }
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  document.querySelector(`[data-view="${name}"]`).classList.add("active");
}

// ── Spacecraft filter — auto-search on click ──────────────────────────────
document.querySelectorAll("#spacecraft-filter .filter-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#spacecraft-filter .filter-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    state.spacecraft = btn.dataset.val;
    runSearch(1);
  });
});

document.getElementById("target-select").addEventListener("change", e => {
  state.target = e.target.value;
  runSearch(1);
});

// ── Search ────────────────────────────────────────────────────────────────
async function runSearch(page = 1) {
  state.page = page;

  const grid = document.getElementById("image-grid");
  const loading = document.getElementById("loading");
  const errBox = document.getElementById("error-msg");
  const statsBox = document.getElementById("stats-box");
  const pagination = document.getElementById("pagination");

  grid.innerHTML = "";
  errBox.style.display = "none";
  loading.style.display = "flex";
  pagination.style.display = "none";
  statsBox.style.display = "none";

  try {
    const qs = new URLSearchParams({
      spacecraft: state.spacecraft,
      target: state.target,
      page: state.page,
      limit: state.limit,
    });
    const resp = await fetch(`${API}/api/search?${qs}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${await resp.text()}`);
    const data = await resp.json();

    state.total = data.total || 0;
    const pages = Math.max(1, Math.ceil(state.total / state.limit));

    document.getElementById("stat-total").textContent = state.total.toLocaleString();
    document.getElementById("stat-page").textContent = state.page;
    document.getElementById("stat-pages").textContent = pages;
    statsBox.style.display = "flex";

    loading.style.display = "none";

    if (!data.results || data.results.length === 0) {
      grid.innerHTML = `<div class="loading"><p style="color:var(--text3)">No images found for these filters.</p></div>`;
      return;
    }

    data.results.forEach(obs => {
      grid.appendChild(buildCard(obs));
    });

    if (state.total > state.limit) {
      document.getElementById("btn-prev").disabled = state.page <= 1;
      document.getElementById("btn-next").disabled = state.page >= pages;
      document.getElementById("page-label").textContent = `Page ${state.page} of ${pages}`;
      pagination.style.display = "flex";
    }
  } catch (err) {
    loading.style.display = "none";
    errBox.textContent = `Error fetching data: ${err.message}`;
    errBox.style.display = "block";
  }
}

function changePage(delta) {
  runSearch(state.page + delta);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function buildCard(obs) {
  const card = document.createElement("div");
  card.className = "image-card";
  card.title = obs.opusid || "";

  const target = obs.target || obs.intended_target_names || "Unknown";
  const time = (obs.time1 || obs.observation_start_time_ymdhms || "").split("T")[0];
  const opusid = obs.opusid || obs.opus_id || "";
  const isvg1 = opusid.toLowerCase().includes("-1-");
  const thumbUrl = obs.thumb_url || obs.small_url || "";

  const badgeClass = isvg1 ? "" : " v2";
  const badgeLabel = isvg1 ? "Voyager 1" : "Voyager 2";

  let imgHtml;
  if (thumbUrl) {
    imgHtml = `<img class="thumb" src="${API}/api/proxy/image?url=${encodeURIComponent(thumbUrl)}" alt="${target}" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'" />
               <div class="thumb-placeholder" style="display:none">🔭</div>`;
  } else {
    imgHtml = `<div class="thumb-placeholder">🔭</div>`;
  }

  card.innerHTML = `
    ${imgHtml}
    <div class="card-meta">
      <div class="card-target">${escHtml(target)}</div>
      <div class="card-time">${escHtml(time)}</div>
      <div class="card-id">${escHtml(opusid)}</div>
      <span class="card-badge${badgeClass}">${badgeLabel}</span>
    </div>`;

  card.addEventListener("click", () => openLightbox(obs));
  return card;
}

// ── Lightbox ──────────────────────────────────────────────────────────────
function openLightbox(obs) {
  state.currentObs = obs;
  const lb = document.getElementById("lightbox");
  const img = document.getElementById("lb-image");
  const title = document.getElementById("lb-title");
  const info = document.getElementById("lb-info");
  const pdsLink = document.getElementById("lb-pds-link");
  const vicarMeta = document.getElementById("lb-vicar-meta");
  const vicarWrap = document.getElementById("lb-vicar-wrap");
  const lbLoading = document.getElementById("lb-loading");

  vicarMeta.style.display = "none";
  vicarWrap.style.display = "none";
  lbLoading.style.display = "none";
  document.getElementById("lb-vicar-btn").textContent = "Load Raw VICAR";
  document.getElementById("lb-vicar-btn").disabled = false;

  const opusid = obs.opusid || obs.opus_id || "";
  const target = obs.target || obs.intended_target_names || "Unknown";
  const time = obs.time1 || obs.observation_start_time_ymdhms || "";
  const previewUrl = obs.small_url || obs.med_url || obs.thumb_url || "";

  title.textContent = target + (time ? ` — ${time.split("T")[0]}` : "");

  if (previewUrl) {
    img.src = `${API}/api/proxy/image?url=${encodeURIComponent(previewUrl)}`;
  } else {
    img.src = "";
  }

  info.innerHTML = `
    <div><strong>OPUS ID:</strong> ${escHtml(opusid)}</div>
    <div><strong>Target:</strong> ${escHtml(target)}</div>
    <div><strong>Time:</strong> ${escHtml(time)}</div>
    ${obs.instrument ? `<div><strong>Instrument:</strong> ${escHtml(obs.instrument)}</div>` : ""}
    ${obs.wavelength1 ? `<div><strong>Wavelength:</strong> ${escHtml(String(obs.wavelength1))} µm</div>` : ""}
  `;

  pdsLink.href = opusid
    ? `https://opus.pds-rings.seti.org/#/view=detail&detail=${encodeURIComponent(opusid)}`
    : "#";

  lb.style.display = "flex";
  document.body.style.overflow = "hidden";
}

function closeLightbox(e) {
  if (e && e.target !== document.getElementById("lightbox")) return;
  document.getElementById("lightbox").style.display = "none";
  document.body.style.overflow = "";
  state.currentObs = null;
}

async function loadVicarForLightbox() {
  const obs = state.currentObs;
  if (!obs) return;

  const btn = document.getElementById("lb-vicar-btn");
  const lbLoading = document.getElementById("lb-loading");
  const vicarWrap = document.getElementById("lb-vicar-wrap");
  const vicarImg = document.getElementById("lb-vicar-image");
  const vicarMeta = document.getElementById("lb-vicar-meta");

  btn.disabled = true;
  btn.textContent = "Loading…";
  lbLoading.style.display = "flex";
  vicarWrap.style.display = "none";

  try {
    // Get file list for this observation
    const filesResp = await fetch(`${API}/api/observation/${encodeURIComponent(obs.opusid)}`);
    if (!filesResp.ok) throw new Error(`Files API: ${filesResp.status}`);
    const filesData = await filesResp.json();

    // Find a .IMG VICAR file
    const vicarUrl = findVicarUrl(filesData.files || filesData);
    if (!vicarUrl) throw new Error("No VICAR .IMG file found for this observation");

    const vicarResp = await fetch(`${API}/api/vicar/from-url?url=${encodeURIComponent(vicarUrl)}`);
    if (!vicarResp.ok) throw new Error(`VICAR parse: ${vicarResp.status}`);
    const vicarData = await vicarResp.json();

    vicarImg.src = `data:image/png;base64,${vicarData.png_base64}`;
    vicarWrap.style.display = "flex";
    lbLoading.style.display = "none";
    btn.textContent = "VICAR Loaded ✓";

    renderVicarMeta(vicarData.metadata, vicarMeta);
    vicarMeta.style.display = "block";
  } catch (err) {
    lbLoading.style.display = "none";
    btn.disabled = false;
    btn.textContent = "Load Raw VICAR";
    alert(`Failed to load VICAR: ${err.message}`);
  }
}

function findVicarUrl(filesData) {
  // OPUS files structure: {data: {opusId: {versionKey: [url, ...]}}, versions: [...]}
  const files = filesData.data || {};
  for (const obsId of Object.keys(files)) {
    const versions = files[obsId];
    // Prefer calibrated, then cleaned, then raw
    const preferOrder = ["vgiss_calib", "vgiss_cleaned", "vgiss_raw"];
    for (const vkey of preferOrder) {
      const urls = versions[vkey];
      if (Array.isArray(urls)) {
        const imgUrl = urls.find(u => typeof u === "string" && u.toLowerCase().endsWith(".img"));
        if (imgUrl) return imgUrl;
      }
    }
    // Fallback: any version with a .IMG file
    for (const urls of Object.values(versions)) {
      if (Array.isArray(urls)) {
        const imgUrl = urls.find(u => typeof u === "string" && u.toLowerCase().endsWith(".img"));
        if (imgUrl) return imgUrl;
      }
    }
  }
  return null;
}

function renderVicarMeta(meta, container) {
  if (!meta) return;
  const label = meta.raw_label || {};
  const keyFields = ["LBLSIZE","NL","NS","NB","FORMAT","ORG","INTFMT","RECSIZE","NBB","NLB","HOST","DAT_TIM","NOTE"];
  const rows = keyFields
    .filter(k => label[k] !== undefined)
    .map(k => `<div class="vm-row"><span class="vm-key">${k}</span><span class="vm-val">${escHtml(String(label[k]))}</span></div>`)
    .join("");
  container.innerHTML = `<h4>VICAR Label</h4>${rows}
    <div class="vm-row"><span class="vm-key">Dimensions</span><span class="vm-val">${meta.nl}×${meta.ns}×${meta.nb}</span></div>`;
}

// ── Upload VICAR ──────────────────────────────────────────────────────────
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");

dropZone.addEventListener("click", () => fileInput.click());
dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("drag-over"); });
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", e => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) uploadVicar(file);
});
fileInput.addEventListener("change", e => {
  const file = e.target.files[0];
  if (file) uploadVicar(file);
});

async function uploadVicar(file) {
  const resultDiv = document.getElementById("upload-result");
  const img = document.getElementById("upload-image");
  const meta = document.getElementById("upload-meta");

  resultDiv.style.display = "none";
  dropZone.querySelector("p").textContent = "Uploading…";

  try {
    const form = new FormData();
    form.append("file", file);

    const resp = await fetch(`${API}/api/vicar/upload`, { method: "POST", body: form });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || resp.statusText);
    }
    const data = await resp.json();

    img.src = `data:image/png;base64,${data.png_base64}`;
    renderVicarMeta(data.metadata, meta);
    resultDiv.style.display = "block";
    dropZone.querySelector("p").innerHTML = "Drop your VICAR file here<br />or click to browse";
  } catch (err) {
    dropZone.querySelector("p").innerHTML = `<span style="color:#fca5a5">Error: ${escHtml(err.message)}</span>`;
  }
}

// ── Local File Browser ────────────────────────────────────────────────────
let localTreeRoot   = null;
let activeFileBtn   = null;
let _lastFolderPath = null;
let _lastFolderRow  = null;
let _currentArchive = null;

// ── Root path config ──────────────────────────────────────────────────────
async function loadRootConfig() {
  try {
    const resp = await fetch(`${API}/api/config`);
    const data = await resp.json();
    const wp = data.root_path || "";
    document.getElementById("local-root-label").textContent =
      wp ? `📂 ${wp}` : "📂 Not configured — click ✏ to set path";
    document.getElementById("local-root-input").value = wp;
    return wp;
  } catch {
    document.getElementById("local-root-label").textContent = "📂 Not configured";
    return "";
  }
}

function togglePathEdit() {
  const display = document.getElementById("local-root-display");
  const edit    = document.getElementById("local-root-edit");
  const isEdit  = edit.style.display !== "none";
  display.style.display = isEdit ? "flex" : "none";
  edit.style.display    = isEdit ? "none" : "flex";
  if (!isEdit) {
    const inp = document.getElementById("local-root-input");
    inp.focus();
    inp.select();
  }
}

async function saveRootPath() {
  const newPath = document.getElementById("local-root-input").value.trim();
  if (!newPath) return;
  try {
    const resp = await fetch(
      `${API}/api/config?root_path=${encodeURIComponent(newPath)}`,
      { method: "POST" }
    );
    if (!resp.ok) throw new Error(await resp.text());
    document.getElementById("local-root-label").textContent = `📂 ${newPath}`;
    togglePathEdit();
    localTreeRoot   = null;
    activeFileBtn   = null;
    _lastFolderPath = null;
    _lastFolderRow  = null;
    _currentArchive = null;
    document.getElementById("local-tree").innerHTML = "";
    document.getElementById("local-file-list").innerHTML =
      '<div class="local-empty">Select a folder from the tree</div>';
    document.getElementById("local-path-display").textContent = "Select a folder";
    document.getElementById("local-viewer-empty").style.display = "flex";
    document.getElementById("local-viewer-content").style.display = "none";
    await initLocalBrowser();
  } catch (err) {
    alert(`Failed to save path: ${err.message}`);
  }
}

// Called when "Local Files" tab is opened
async function initLocalBrowser() {
  if (localTreeRoot) return;
  const wp = await loadRootConfig();
  const treeEl = document.getElementById("local-tree");
  if (!wp) {
    treeEl.innerHTML = `<div class="local-empty">Enter a path above to begin browsing</div>`;
    togglePathEdit();
    return;
  }
  treeEl.innerHTML = `<div class="local-empty">Loading…</div>`;
  try {
    const resp = await fetch(`${API}/api/local/browse?path=`);
    if (!resp.ok) throw new Error(await resp.text());
    localTreeRoot = await resp.json();
    treeEl.innerHTML = "";
    renderTreeChildren(treeEl, localTreeRoot.dirs, 0);
  } catch (err) {
    treeEl.innerHTML = `<div class="local-empty" style="color:#fca5a5">Failed to load: ${escHtml(err.message)}</div>`;
  }
}

function renderTreeChildren(container, dirs, depth) {
  dirs.forEach(dir => {
    const nodeEl = document.createElement("div");
    nodeEl.className = "tree-node";

    const row = document.createElement("div");
    row.className = "tree-node-row";
    row.style.paddingLeft = `${12 + depth * 14}px`;

    const toggle = document.createElement("span");
    toggle.className = "tree-toggle";
    toggle.textContent = "▶";

    const icon = document.createElement("span");
    icon.className = "tree-icon";
    icon.textContent = "📁";

    const label = document.createElement("span");
    label.className = "tree-label";
    label.textContent = dir.name;
    label.title = dir.name;

    row.append(toggle, icon, label);
    nodeEl.appendChild(row);

    const childrenEl = document.createElement("div");
    childrenEl.className = "tree-children";
    childrenEl.style.display = "none";
    nodeEl.appendChild(childrenEl);

    let expanded = false;
    let loaded = false;

    row.addEventListener("click", async () => {
      // Load files in this folder
      await showLocalFolder(dir.path, row);

      // Toggle expand
      if (!loaded) {
        loaded = true;
        childrenEl.innerHTML = `<div class="local-empty" style="padding:4px 12px;font-size:.75rem">Loading…</div>`;
        childrenEl.style.display = "block";
        try {
          const resp = await fetch(`${API}/api/local/browse?path=${encodeURIComponent(dir.path)}`);
          const data = await resp.json();
          childrenEl.innerHTML = "";
          if (data.dirs.length > 0) {
            renderTreeChildren(childrenEl, data.dirs, depth + 1);
            expanded = true;
            toggle.textContent = "▼";
            icon.textContent = "📂";
          } else {
            toggle.textContent = "";
            expanded = true;
          }
        } catch {
          childrenEl.innerHTML = "";
          childrenEl.style.display = "none";
        }
      } else {
        expanded = !expanded;
        childrenEl.style.display = expanded ? "block" : "none";
        toggle.textContent = expanded ? "▼" : "▶";
        icon.textContent = expanded ? "📂" : "📁";
      }
    });

    container.appendChild(nodeEl);
  });
}

const IMG_TYPE_ORDER = { CALIB: 0, CLEANED: 1, RAW: 2, GEOMED: 3, GEOMA: 4, IMG: 5 };
const CAT_ORDER = { image: 0, pds4: 1, text: 2, data: 3 };

async function showLocalFolder(relPath, rowEl) {
  _lastFolderPath = relPath;
  _lastFolderRow  = rowEl;
  _currentArchive = null;
  document.querySelectorAll(".tree-node-row").forEach(r => r.classList.remove("active"));
  if (rowEl) rowEl.classList.add("active");

  const fileList = document.getElementById("local-file-list");
  const pathDisplay = document.getElementById("local-path-display");
  fileList.innerHTML = `<div class="local-empty">Loading…</div>`;

  try {
    const resp = await fetch(`${API}/api/local/browse?path=${encodeURIComponent(relPath)}`);
    if (!resp.ok) throw new Error(await resp.text());
    const data = await resp.json();

    pathDisplay.textContent = data.display_path || relPath;

    if (data.files.length === 0) {
      fileList.innerHTML = `<div class="local-empty">No viewable files in this folder</div>`;
      return;
    }

    // Group by obs_id, sort groups by ID, sort files within group by category then type
    const groups = {};
    data.files.forEach(f => {
      const key = f.obs_id || f.name;
      if (!groups[key]) groups[key] = [];
      groups[key].push(f);
    });

    fileList.innerHTML = "";
    Object.entries(groups).sort(([a], [b]) => a.localeCompare(b)).forEach(([obsId, files]) => {
      files.sort((a, b) => {
        const catDiff = (CAT_ORDER[a.category] ?? 9) - (CAT_ORDER[b.category] ?? 9);
        if (catDiff !== 0) return catDiff;
        return (IMG_TYPE_ORDER[a.type] ?? 9) - (IMG_TYPE_ORDER[b.type] ?? 9);
      });

      const grp = document.createElement("div");
      grp.className = "obs-group";

      const idRow = document.createElement("div");
      idRow.className = "obs-group-id";
      idRow.textContent = obsId;
      grp.appendChild(idRow);

      const btnsRow = document.createElement("div");
      btnsRow.className = "obs-group-files";

      files.forEach(f => {
        const btn = document.createElement("button");
        btn.className = `file-btn type-${f.type.toLowerCase()} cat-${f.category}`;
        btn.textContent = f.category === "archive" ? `📦 ${f.ext.toUpperCase()}` : f.type;
        btn.title = `${f.name}  (${f.size_mb} MB)`;
        btn.addEventListener("click", () =>
          f.category === "archive" ? openArchiveBrowser(f) : loadLocalFile(f, btn)
        );
        btnsRow.appendChild(btn);
      });

      grp.appendChild(btnsRow);
      fileList.appendChild(grp);
    });
  } catch (err) {
    fileList.innerHTML = `<div class="local-empty" style="color:#fca5a5">Error: ${escHtml(err.message)}</div>`;
  }
}

function _resetViewer() {
  document.getElementById("local-viewer-empty").style.display = "none";
  document.getElementById("local-viewer-content").style.display = "flex";
  document.getElementById("local-img-loading").style.display = "flex";
  document.getElementById("local-img-wrap").style.display = "none";
  document.getElementById("local-text-wrap").style.display = "none";
  document.getElementById("local-binary-wrap").style.display = "none";
  document.getElementById("local-meta-panel").innerHTML = "";
  document.getElementById("local-vicar-img").src = "";
  document.getElementById("local-text-content").textContent = "";
}

function _showViewerResponse(data) {
  document.getElementById("local-img-loading").style.display = "none";

  if (data.type === "image") {
    const imgEl = document.getElementById("local-vicar-img");
    imgEl.src = data.png_base64
      ? `data:image/png;base64,${data.png_base64}`
      : `data:${data.mime_type};base64,${data.data_base64}`;
    document.getElementById("local-img-wrap").style.display = "flex";
    if (data.metadata) renderVicarMeta(data.metadata, document.getElementById("local-meta-panel"));

  } else if (data.type === "text" || data.type === "pds4_label_only") {
    document.getElementById("local-text-content").textContent =
      data.text || JSON.stringify(data.metadata, null, 2);
    document.getElementById("local-text-label").textContent =
      (data.format || "text").toUpperCase().replace(/_/g, " ");
    document.getElementById("local-text-truncated").style.display =
      data.truncated ? "inline" : "none";
    document.getElementById("local-text-wrap").style.display = "flex";

  } else if (data.type === "binary") {
    document.getElementById("local-binary-msg").textContent =
      `${data.filename}  —  ${data.size_mb} MB  —  ${data.message}`;
    document.getElementById("local-binary-wrap").style.display = "flex";

  } else {
    document.getElementById("local-binary-msg").textContent = `Unknown type: ${data.type}`;
    document.getElementById("local-binary-wrap").style.display = "flex";
  }
}

async function loadLocalFile(fileInfo, btnEl) {
  if (activeFileBtn) activeFileBtn.classList.remove("active");
  btnEl.classList.add("active");
  activeFileBtn = btnEl;

  _resetViewer();
  document.getElementById("local-loading-msg").textContent =
    fileInfo.category === "image" ? "Rendering image…" :
    fileInfo.category === "text"  ? "Loading text…" : "Loading…";

  try {
    const resp = await fetch(`${API}/api/local/view?path=${encodeURIComponent(fileInfo.path)}`);
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || resp.statusText);
    }
    _showViewerResponse(await resp.json());
  } catch (err) {
    document.getElementById("local-img-loading").style.display = "none";
    document.getElementById("local-meta-panel").innerHTML =
      `<span style="color:#fca5a5">Error: ${escHtml(err.message)}</span>`;
  }
}

// ── Archive browser ────────────────────────────────────────────────────────

async function openArchiveBrowser(fileInfo) {
  _currentArchive = fileInfo.path;
  const fileList = document.getElementById("local-file-list");
  const pathDisplay = document.getElementById("local-path-display");

  pathDisplay.textContent = `📦 ${fileInfo.name}`;
  fileList.innerHTML = `
    <div class="archive-header">
      <button class="arc-back-btn" onclick="restoreFolder()">← Folder</button>
      <span class="arc-name">${escHtml(fileInfo.name)}</span>
    </div>
    <div class="arc-scanning">
      <div class="spinner"></div>
      <p>Scanning archive… large archives may take a moment</p>
    </div>`;

  try {
    const resp = await fetch(`${API}/api/local/archive/list?path=${encodeURIComponent(fileInfo.path)}`);
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || resp.statusText);
    }
    const data = await resp.json();
    _renderArchiveBrowser(data);
  } catch (err) {
    fileList.innerHTML = `
      <div class="archive-header"><button class="arc-back-btn" onclick="restoreFolder()">← Folder</button></div>
      <div class="local-empty" style="color:#fca5a5">Error: ${escHtml(err.message)}</div>`;
  }
}

let _allArchiveEntries = [];

function _renderArchiveBrowser(data) {
  const fileList = document.getElementById("local-file-list");
  _allArchiveEntries = (data.entries || []).filter(e => e.category !== "other");

  const header = `
    <div class="archive-header">
      <button class="arc-back-btn" onclick="restoreFolder()">← Folder</button>
      <span class="arc-name">${escHtml(data.archive_name)}</span>
      <span class="arc-count">${_allArchiveEntries.length.toLocaleString()} files${data.capped ? " (capped)" : ""}</span>
    </div>
    <div class="arc-search-wrap">
      <input type="text" class="arc-search-input" placeholder="Filter by name or ID…"
             oninput="_filterArchive(this.value)" />
    </div>`;

  const listEl = document.createElement("div");
  listEl.id = "archive-inner-list";
  listEl.style.overflowY = "auto";
  listEl.style.flex = "1";

  fileList.innerHTML = header;
  fileList.appendChild(listEl);
  _renderArchiveList(_allArchiveEntries, "");
}

function _filterArchive(q) {
  const filtered = q
    ? _allArchiveEntries.filter(e =>
        e.name.toLowerCase().includes(q.toLowerCase()) ||
        e.obs_id.toLowerCase().includes(q.toLowerCase()) ||
        e.dir.toLowerCase().includes(q.toLowerCase()))
    : _allArchiveEntries;
  _renderArchiveList(filtered, q);
}

const _ARC_TYPE_ORDER = { CALIB: 0, CLEANED: 1, RAW: 2, GEOMED: 3, GEOMA: 4, IMG: 5 };
const _ARC_CAT_ORDER  = { image: 0, text: 1 };
const MAX_ARC_GROUPS  = 300;

function _renderArchiveList(entries, _q) {
  const listEl = document.getElementById("archive-inner-list");
  if (!listEl) return;

  if (entries.length === 0) {
    listEl.innerHTML = `<div class="local-empty">No matches</div>`;
    return;
  }

  // Group by obs_id
  const groups = {};
  entries.forEach(e => {
    const key = e.obs_id || e.name;
    if (!groups[key]) groups[key] = [];
    groups[key].push(e);
  });

  const sorted = Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
  listEl.innerHTML = "";
  const shown = sorted.slice(0, MAX_ARC_GROUPS);

  shown.forEach(([obsId, files]) => {
    files.sort((a, b) => {
      const cd = (_ARC_CAT_ORDER[a.category] ?? 9) - (_ARC_CAT_ORDER[b.category] ?? 9);
      return cd !== 0 ? cd : (_ARC_TYPE_ORDER[a.type] ?? 9) - (_ARC_TYPE_ORDER[b.type] ?? 9);
    });

    const grp = document.createElement("div");
    grp.className = "obs-group";

    const idRow = document.createElement("div");
    idRow.className = "obs-group-id";
    idRow.textContent = obsId;
    grp.appendChild(idRow);

    const btnsRow = document.createElement("div");
    btnsRow.className = "obs-group-files";

    files.forEach(f => {
      const btn = document.createElement("button");
      btn.className = `file-btn type-${f.type.toLowerCase()} cat-${f.category}`;
      btn.textContent = f.type;
      btn.title = `${f.name} (${f.size_mb} MB)\n${f.dir}`;
      btn.addEventListener("click", () => _loadArchiveFile(f, btn));
      btnsRow.appendChild(btn);
    });

    grp.appendChild(btnsRow);
    listEl.appendChild(grp);
  });

  if (sorted.length > MAX_ARC_GROUPS) {
    const more = document.createElement("div");
    more.className = "local-empty";
    more.style.borderTop = "1px solid var(--border)";
    more.style.paddingTop = "12px";
    more.textContent = `${sorted.length - MAX_ARC_GROUPS} more groups — use search to filter`;
    listEl.appendChild(more);
  }
}

async function _loadArchiveFile(fileInfo, btnEl) {
  if (activeFileBtn) activeFileBtn.classList.remove("active");
  btnEl.classList.add("active");
  activeFileBtn = btnEl;

  _resetViewer();
  document.getElementById("local-loading-msg").textContent =
    fileInfo.category === "image" ? "Extracting & rendering…" : "Extracting…";

  try {
    const url = `${API}/api/local/archive/view` +
      `?path=${encodeURIComponent(_currentArchive)}` +
      `&inner=${encodeURIComponent(fileInfo.inner_path)}`;
    const resp = await fetch(url);
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || resp.statusText);
    }
    _showViewerResponse(await resp.json());
  } catch (err) {
    document.getElementById("local-img-loading").style.display = "none";
    document.getElementById("local-meta-panel").innerHTML =
      `<span style="color:#fca5a5">Error: ${escHtml(err.message)}</span>`;
  }
}

function restoreFolder() {
  if (_lastFolderPath !== null) {
    showLocalFolder(_lastFolderPath, _lastFolderRow);
  }
}

let _textWrapped = false;
function toggleTextWrap() {
  _textWrapped = !_textWrapped;
  document.getElementById("local-text-content").style.whiteSpace =
    _textWrapped ? "pre-wrap" : "pre";
}

// ── Stars ─────────────────────────────────────────────────────────────────
function generateStars() {
  const container = document.getElementById("stars");
  const count = 120;
  for (let i = 0; i < count; i++) {
    const star = document.createElement("div");
    const x = Math.random() * 100;
    const y = Math.random() * 100;
    const size = Math.random() * 2 + 0.5;
    const opacity = Math.random() * 0.7 + 0.2;
    const duration = Math.random() * 3 + 2;
    Object.assign(star.style, {
      position: "absolute",
      left: `${x}%`,
      top: `${y}%`,
      width: `${size}px`,
      height: `${size}px`,
      background: "#fff",
      borderRadius: "50%",
      opacity,
      animation: `twinkle ${duration}s ease-in-out infinite`,
      animationDelay: `${Math.random() * 3}s`,
    });
    container.appendChild(star);
  }

  const style = document.createElement("style");
  style.textContent = `
    @keyframes twinkle {
      0%, 100% { opacity: var(--op, .4); transform: scale(1); }
      50% { opacity: calc(var(--op, .4) * 0.3); transform: scale(0.7); }
    }
  `;
  document.head.appendChild(style);
}

// ── Utilities ─────────────────────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ── Init ──────────────────────────────────────────────────────────────────
document.getElementById("local-root-input").addEventListener("keydown", e => {
  if (e.key === "Enter")  saveRootPath();
  if (e.key === "Escape") togglePathEdit();
});

generateStars();
runSearch(1);
