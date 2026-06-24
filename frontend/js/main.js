// ── State ────────────────────────────────────────────────────────────────────
let parsedRawB64 = null;      // base64 of the original CSV, returned by /api/parse
let grainOverrides = {};      // {material: bool} set by the user in step 2
let currentExportId = null;

// ── DOM refs ─────────────────────────────────────────────────────────────────
const parseForm      = document.getElementById('parse-form');
const parseBtn       = document.getElementById('parse-btn');
const parseBtnText   = document.getElementById('parse-btn-text');
const parseSpinner   = document.getElementById('parse-spinner');
const parseError     = document.getElementById('parse-error');

const grainSection   = document.getElementById('grain-section');
const grainTbody     = document.getElementById('grain-tbody');
const optimizeBtn    = document.getElementById('optimize-btn');
const optimizeBtnText = document.getElementById('optimize-btn-text');
const optimizeSpinner = document.getElementById('optimize-spinner');
const optimizeError  = document.getElementById('optimize-error');

const resultSection  = document.getElementById('result-section');
const advancedToggle = document.getElementById('advanced-toggle');
const advancedPanel  = document.getElementById('advanced-panel');

// ── Advanced toggle ───────────────────────────────────────────────────────────
advancedToggle.addEventListener('click', () => advancedPanel.classList.toggle('open'));

// ── STEP 1 — Parse CSV ───────────────────────────────────────────────────────
parseForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  setParseLoading(true);
  hideError(parseError);
  grainSection.classList.remove('visible');
  resultSection.classList.remove('visible');

  const data = new FormData();
  const fileInput = document.getElementById('file-input');
  const paste = document.getElementById('paste-input').value.trim();

  if (fileInput.files.length > 0) {
    data.append('file', fileInput.files[0]);
  } else if (paste) {
    data.append('paste', paste);
  } else {
    showError(parseError, 'Colle un tableau de débit ou sélectionne un fichier CSV.');
    setParseLoading(false);
    return;
  }

  try {
    const res = await fetch('/api/parse', { method: 'POST', body: data });
    const json = await res.json();
    if (!res.ok) { showError(parseError, json.detail || `Erreur ${res.status}`); return; }

    parsedRawB64 = json.raw_b64;
    grainOverrides = {};
    buildGrainTable(json.materials);
    grainSection.classList.add('visible');
    grainSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch {
    showError(parseError, 'Impossible de joindre le serveur.');
  } finally {
    setParseLoading(false);
  }
});

// ── STEP 2 — Build grain table ────────────────────────────────────────────────
function buildGrainTable(materials) {
  grainTbody.innerHTML = '';
  materials.forEach(mat => {
    // Initialise override with auto-detected value
    grainOverrides[mat.material] = mat.grain_locked;

    const tr = document.createElement('tr');
    const badge = mat.grain_locked
      ? '<span class="badge badge-grain">FIL OBLIGATOIRE</span>'
      : '<span class="badge badge-free">ROTATION LIBRE</span>';

    tr.innerHTML = `
      <td style="font-weight:500">${escHtml(mat.material)}</td>
      <td style="font-family:var(--mono);font-size:12px;color:var(--ink-dim)">
        ${mat.thicknesses.map(t => t + 'mm').join(', ')}
      </td>
      <td style="font-family:var(--mono);font-size:13px">${mat.piece_count}</td>
      <td>
        <div class="toggle-wrap">
          <label class="toggle">
            <input type="checkbox" data-material="${escAttr(mat.material)}"
                   ${mat.grain_locked ? 'checked' : ''}>
            <span class="slider"></span>
          </label>
          <span class="grain-label ${mat.grain_locked ? 'locked' : ''}" id="label-${slugify(mat.material)}">
            ${mat.grain_locked ? 'Sens du fil respecté' : 'Rotation libre'}
          </span>
        </div>
      </td>`;
    grainTbody.appendChild(tr);

    // Toggle listener
    tr.querySelector('input[type=checkbox]').addEventListener('change', function() {
      const mat_name = this.dataset.material;
      grainOverrides[mat_name] = this.checked;
      const labelEl = tr.querySelector('.grain-label');
      labelEl.textContent = this.checked ? 'Sens du fil respecté' : 'Rotation libre';
      labelEl.classList.toggle('locked', this.checked);
    });
  });
}

// ── STEP 3 — Optimise ────────────────────────────────────────────────────────
optimizeBtn.addEventListener('click', async () => {
  setOptimizeLoading(true);
  hideError(optimizeError);
  resultSection.classList.remove('visible');

  const data = new FormData();
  data.append('raw_b64', parsedRawB64);
  data.append('grain_overrides', JSON.stringify(grainOverrides));

  const projectName = document.getElementById('project-name').value.trim();
  if (projectName) data.append('project_name', projectName);

  data.append('panel_width',    document.getElementById('panel-width').value);
  data.append('panel_height',   document.getElementById('panel-height').value);
  data.append('kerf',           document.getElementById('kerf').value);
  data.append('border_margin',  document.getElementById('border-margin').value);

  try {
    const res = await fetch('/api/optimize', { method: 'POST', body: data });
    const json = await res.json();
    if (!res.ok) { showError(optimizeError, json.detail || `Erreur ${res.status}`); return; }

    currentExportId = json.export_id;
    displayResult(json);
  } catch {
    showError(optimizeError, 'Impossible de joindre le serveur.');
  } finally {
    setOptimizeLoading(false);
  }
});

// ── Display result ────────────────────────────────────────────────────────────
function displayResult(json) {
  const label = json.project_name || 'Résultat';
  document.getElementById('result-title').textContent = `Résultat — ${label}`;
  document.getElementById('stat-panels').textContent   = json.total_panels;
  document.getElementById('stat-waste').textContent    = `${json.global_waste_ratio}%`;
  document.getElementById('stat-materials').textContent = json.materials_count;
  document.getElementById('stat-pieces').textContent   = json.total_pieces;
  document.getElementById('stat-area').textContent     = `${json.consumed_area_m2} m²`;

  if (currentExportId) {
    document.getElementById('dl-recap').href   = `/api/history/${currentExportId}/recap`;
    document.getElementById('dl-layout').href  = `/api/history/${currentExportId}/layout`;
  }

  resultSection.classList.add('visible');
  resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function setParseLoading(on) {
  parseBtn.disabled = on;
  parseSpinner.classList.toggle('active', on);
  parseBtnText.textContent = on ? 'Analyse en cours…' : 'Analyser le débit';
}
function setOptimizeLoading(on) {
  optimizeBtn.disabled = on;
  optimizeSpinner.classList.toggle('active', on);
  optimizeBtnText.textContent = on ? 'Calcul en cours…' : 'Optimiser';
}
function showError(el, msg) { el.textContent = msg; el.classList.add('visible'); }
function hideError(el) { el.classList.remove('visible'); }
function escHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function escAttr(s) { return s.replace(/"/g,'&quot;'); }
function slugify(s) { return s.replace(/[^a-z0-9]/gi, '_').toLowerCase(); }
