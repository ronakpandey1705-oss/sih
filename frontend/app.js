const API = "";
const DEMO_BARCODES = [
  ["8908877665501", "Heritage Double Bedsheet"],
  ["8902233445501", "Aura X12 5G Smartphone"],
  ["8906038530187", "Envie Rechargeable Charger"],
  ["8903344556601", "Kohinoor Basmati Rice"],
  ["8905566778801", "Herbal Essence Shampoo"],
  ["8907788991101", "Surf Excel Top Load"],
  ["8906677882201", "Huggies Diapers M"],
  ["8904455667701", "Dettol Antiseptic Liquid"],
  ["8901122330001", "Havells LED Bulb 9W"],
  ["8904455667704", "ClassMate Ruled Notebook"],
  ["8902233445506", "Prestige Electric Kettle"],
  ["8908877665504", "HydroSoft Bath Towel"],
];

const FIELD_LABELS = {
  product_name: "Product Designation",
  net_quantity: "Net Quantity",
  mrp: "Maximum Retail Price (MRP)",
  unit_sale_price: "Unit Sale Price (USP)",
  manufacturer_name_and_address: "Manufacturer / Packer Details",
  consumer_care: "Consumer Care Coordinates",
  manufacture_or_import_date: "Date of Manufacture / Import",
  dimensions: "Package Dimensions",
};

const PANEL_LABELS = ["Front PDP", "Back Declarations", "Side / MRP Panel", "Barcode / Batch Panel", "Supplementary Panel"];

const PAGE_TITLES = {
  dashboard: "Compliance Dashboard",
  inspect: "Packaging Inspector",
  results: "Inspection Results & Discrepancies",
  catalog: "Standard Reference Catalog",
  rules: "Legal Metrology Ruleset (2011)",
  assistant: "Regulatory Query Terminal",
  terms: "Terms & Conditions",
  privacy: "Privacy Policy",
  about: "System Documentation",
  login: "Officer Authentication Portal",
  complaints: "Citizen Complaints",
};

const state = {
  scanId: null,
  product: null,
  analysis: null,
  fields: [],
  products: [],
  evidenceFiles: [],
  history: JSON.parse(localStorage.getItem("packsure_history") || "[]"),
  officer: JSON.parse(localStorage.getItem("packsure_officer") || "null"),
  token: localStorage.getItem("packsure_token") || null,
};

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.style.display = "block";
  setTimeout(() => { el.style.display = "none"; }, 4200);
}

async function api(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const res = await fetch(API + path, { ...opts, headers });
  if (res.status === 401 && state.token) {
    // Session expired or revoked: send the user back to the sign-in gate
    endSession("Your session has expired. Please sign in again.");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch (_) {
      try { detail = await res.text(); } catch (__) {}
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res;
}

function showPage(id) {
  if (id === "inspect" && !state.officer) {
    openOfficerModal();
  }
  if (id === "complaints") {
    loadComplaints();
  }
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  const target = document.getElementById(id);
  if (target) {
    target.classList.add("active");
  }
  document.querySelectorAll(".gov-nav-item, nav button").forEach((b) => {
    b.classList.toggle("active", b.dataset.page === id);
  });
  if (PAGE_TITLES[id]) {
    document.title = `PRAMAAN | ${PAGE_TITLES[id]}`;
    const crumb = document.getElementById("pageCrumb");
    if (crumb) {
      crumb.innerHTML = `<span>National Portal</span> <strong>${escapeHtml(PAGE_TITLES[id])}</strong>`;
    }
  }
  const mainNav = document.getElementById("mainNav");
  if (mainNav) {
    mainNav.classList.remove("nav-open");
  }
  const toggleBtn = document.getElementById("navToggle");
  if (toggleBtn) {
    toggleBtn.setAttribute("aria-expanded", "false");
  }
  window.scrollTo({ top: 0, behavior: "instant" });
}

// Global delegated click handler for page navigation links and buttons
document.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-page]");
  if (btn && btn.dataset.page) {
    e.preventDefault();
    showPage(btn.dataset.page);
  }
});

function saveHistory() {
  localStorage.setItem("packsure_history", JSON.stringify(state.history.slice(0, 20)));
  renderDashboard();
}

function pill(status) {
  const map = {
    PASS: ["pass", "PASS"],
    POTENTIAL_NON_COMPLIANCE: ["fail", "FLAGGED"],
    POTENTIAL_DISCREPANCY: ["fail", "FLAGGED"],
    NEEDS_REVIEW: ["review", "REVIEW"],
    NOT_APPLICABLE: ["na", "N/A"],
    INFO: ["na", "INFO"],
  };
  const [cls, label] = map[status] || ["na", status || "N/A"];
  return `<span class="status-tag ${cls}">${label}</span>`;
}

function renderDashboard() {
  document.getElementById("statScans").textContent = String(state.history.length);
  const last = state.history[0];
  document.getElementById("statLast").textContent = last && last.score != null ? `${Math.round(last.score)}%` : "N/A";
  const list = document.getElementById("recentList");
  if (!state.history.length) {
    list.innerHTML = `<p class="muted">No inspections recorded in this browser session.</p>`;
    return;
  }
  list.innerHTML = state.history.slice(0, 6).map((h) => `
    <div class="list-item">
      <div>
        <div style="font-weight:600">${h.name || h.barcode || "Unlisted Pack"}</div>
        <div class="muted">ID: ${h.id.slice(0, 8)} | ${h.status || "COMPLETED"}</div>
      </div>
      <div><strong>${h.score != null ? Math.round(h.score) + "%" : "N/A"}</strong></div>
    </div>
  `).join("");
}

function renderDemoChips() {
  document.getElementById("demoChips").innerHTML = DEMO_BARCODES.map(
    ([code, name]) => `<button class="chip" data-code="${code}" type="button">${name}</button>`
  ).join("");
  document.querySelectorAll("#demoChips .chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.getElementById("barcode").value = btn.dataset.code;
      lookup();
    });
  });
}

async function ping() {
  const dot = document.getElementById("healthDot");
  try {
    const h = await api("/api/health");
    dot.className = "health-dot ok";
    dot.querySelector("span").textContent = h.status === "ok" ? "System Online" : "Service Active";
  } catch {
    dot.className = "health-dot bad";
    dot.querySelector("span").textContent = "Service Offline";
  }
}

function renderCatalog() {
  const grid = document.getElementById("catalogGrid");
  if (!grid) return;
  const categoryFilter = (document.getElementById("catalogCategoryFilter")?.value || "ALL").trim();
  const searchQuery = (document.getElementById("catalogSearch")?.value || "").trim().toLowerCase();

  const filtered = (state.products || []).filter((p) => {
    if (categoryFilter !== "ALL" && p.category !== categoryFilter) {
      return false;
    }
    if (searchQuery) {
      const matchText = [
        p.name,
        p.brand,
        p.barcode,
        p.category,
        p.expected_net_quantity,
        p.expected_mrp,
        p.manufacturer,
        p.packer,
      ].filter(Boolean).join(" ").toLowerCase();
      if (!matchText.includes(searchQuery)) return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:48px 16px;background:var(--card-bg);border:1px dashed var(--border);border-radius:6px">
        <div style="font-weight:600;font-size:15px">No commodities found</div>
        <div class="muted" style="margin-top:6px">No products matched the selected category and search query. Try clearing filters or searching for another term.</div>
      </div>`;
    return;
  }

  grid.innerHTML = filtered.map((p) => `
    <div class="product-item">
      <div class="row" style="justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:6px">
        <h3 style="margin:0">${escapeHtml(p.name)}</h3>
        <span class="status-tag na" style="font-size:10.5px;white-space:nowrap">${escapeHtml(p.category || "General")}</span>
      </div>
      <p class="muted" style="margin-bottom:8px">${escapeHtml(p.brand || "Standard Brand")}</p>
      <div class="list-item"><span>Barcode</span><b>${escapeHtml(p.barcode)}</b></div>
      <div class="list-item"><span>Net Quantity</span><b>${escapeHtml(p.expected_net_quantity || "N/A")}</b></div>
      <div class="list-item"><span>Standard MRP</span><b>${escapeHtml(p.expected_mrp || "N/A")}</b></div>
      ${p.manufacturer ? `<div class="list-item" style="font-size:11.5px;color:var(--text-muted)"><span>Mfr/Packer</span><span style="max-width:60%;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${escapeHtml(p.manufacturer)}">${escapeHtml(p.manufacturer)}</span></div>` : ""}
      <button class="btn btn-ghost" style="margin-top:12px;width:100%" data-use="${escapeHtml(p.barcode)}">
        Select for Inspection
      </button>
    </div>
  `).join("");

  grid.querySelectorAll("[data-use]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.getElementById("barcode").value = btn.dataset.use;
      showPage("inspect");
      lookup();
    });
  });
}

function renderRules(rulesList) {
  const container = document.getElementById("rulesCards");
  if (!container || !rulesList) return;
  container.innerHTML = rulesList.map((r) => `
    <div class="product-item">
      <h3>Rule ${escapeHtml(r.rule_number)}: ${escapeHtml(r.name)}</h3>
      <div class="row" style="margin:4px 0">
        <span class="status-tag ${r.mandatory ? 'fail' : 'na'}">${r.mandatory ? "Mandatory" : "Advisory"}</span>
        <span class="status-tag na">${escapeHtml(r.severity)} Severity</span>
      </div>
      <p class="muted" style="margin-top:6px">${escapeHtml(r.description)}</p>
      <p class="muted" style="margin-top:6px;font-size:11px;color:var(--text-dim)">Reference: ${escapeHtml(r.legal_reference || "Legal Metrology (Packaged Commodities) Rules, 2011")}</p>
    </div>
  `).join("");
}

async function loadBootstrap() {
  try {
    const [products, rules] = await Promise.all([
      api("/api/products/?limit=200"),
      api("/api/compliance/rules"),
    ]);
    state.products = products || [];
    document.getElementById("statProducts").textContent = String(state.products.length);
    document.getElementById("statRules").textContent = String(rules.total_rules || 0);
    renderCatalog();
    renderRules(rules.rules || []);
  } catch (err) {
    toast(err.message);
  }
}

async function lookup() {
  const barcode = document.getElementById("barcode").value.trim();
  const box = document.getElementById("lookupBox");
  if (!barcode) {
    box.textContent = "Enter a barcode to query standard catalog.";
    return;
  }
  try {
    const data = await api("/api/products/lookup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ barcode }),
    });
    state.product = data.product;
    if (data.found && data.product) {
      const p = data.product;
      box.innerHTML = `<strong>Registered SKU:</strong> ${p.name} (${p.brand})<br>Standard Net Qty: ${p.expected_net_quantity} | Standard MRP: ${p.expected_mrp}`;
    } else {
      box.textContent = "Barcode not found in standard reference catalog. Proceeding with standard unlisted package inspection.";
    }
  } catch (err) {
    box.textContent = err.message;
  }
}

function sessionPayload() {
  const customOfficer = document.getElementById("officerId") ? document.getElementById("officerId").value.trim() : "";
  const officerId = customOfficer || (state.officer ? state.officer.officer_badge : null);
  return {
    barcode: document.getElementById("barcode").value.trim() || null,
    officer_id: officerId,
    establishment_name: document.getElementById("establishment").value.trim() || null,
    inspection_location: document.getElementById("location").value.trim() || null,
    notes: document.getElementById("notes").value.trim() || null,
  };
}

function setSession(created) {
  state.scanId = created.scan_id || created.inspection_id;
  document.getElementById("sessionMeta").textContent = `Session ID: ${state.scanId} | Status: ${created.status}`;
}

async function createSession() {
  try {
    const created = await api("/api/scans/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sessionPayload()),
    });
    setSession(created);
    toast("Inspection session initialized");
  } catch (err) {
    toast(err.message);
  }
}

function addEvidenceFiles(files) {
  if (!files || !files.length) return;
  let added = 0;
  for (const file of Array.from(files)) {
    const okType = /^image\/(jpeg|jpg|png|webp)$/i.test(file.type) || /\.(jpe?g|png|webp)$/i.test(file.name);
    if (!okType) {
      toast(`Skipped ${file.name}: invalid format (use JPG, PNG, or WebP).`);
      continue;
    }
    if (file.size > 25 * 1024 * 1024) {
      toast(`Skipped ${file.name}: file exceeds 25 MB maximum limit.`);
      continue;
    }
    const exists = state.evidenceFiles.some((f) => f.name === file.name && f.size === file.size);
    if (!exists) {
      state.evidenceFiles.push(file);
      added++;
    }
  }
  renderEvidenceGallery();
  if (added > 0) {
    toast(`${added} photo${added > 1 ? "s" : ""} added to packaging evidence (${state.evidenceFiles.length} total)`);
  }
}

function removeEvidenceFile(index) {
  if (index >= 0 && index < state.evidenceFiles.length) {
    const removed = state.evidenceFiles.splice(index, 1)[0];
    renderEvidenceGallery();
    toast(`Removed ${removed.name}`);
  }
}

function renderEvidenceGallery() {
  const gallery = document.getElementById("evidenceGallery");
  const preview = document.getElementById("preview");
  if (!gallery) return;

  if (!state.evidenceFiles.length) {
    gallery.style.display = "none";
    gallery.innerHTML = "";
    if (preview) preview.style.display = "none";
    return;
  }

  if (preview) preview.style.display = "none";
  gallery.style.display = "grid";

  const panelLabels = PANEL_LABELS;

  gallery.innerHTML = state.evidenceFiles.map((file, idx) => {
    const url = URL.createObjectURL(file);
    const label = panelLabels[idx] || `Panel ${idx + 1}`;
    const kb = Math.round(file.size / 1024);
    return `
      <div class="evidence-item">
        <div class="evidence-thumb-wrap">
          <img class="evidence-thumb" src="${url}" alt="${escapeHtml(file.name)}" />
          <span class="evidence-tag">${label}</span>
          <button class="evidence-del" type="button" data-del-index="${idx}" title="Remove this panel photo">&times;</button>
        </div>
        <div class="evidence-info" title="${escapeHtml(file.name)}">${escapeHtml(file.name)} (${kb} KB)</div>
      </div>
    `;
  }).join("");

  gallery.querySelectorAll("[data-del-index]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const idx = parseInt(btn.dataset.delIndex, 10);
      removeEvidenceFile(idx);
    });
  });
}

function setChosenFile(file) {
  if (file) addEvidenceFiles([file]);
}

const fileInput = document.getElementById("fileInput");
fileInput.addEventListener("change", (e) => {
  if (e.target.files && e.target.files.length) {
    addEvidenceFiles(e.target.files);
    e.target.value = "";
  }
});
document.getElementById("chooseBtn").addEventListener("click", () => fileInput.click());

const dropZone = document.getElementById("dropZone");
["dragenter", "dragover"].forEach((name) => {
  dropZone.addEventListener(name, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.add("hover");
  });
});
["dragleave", "drop"].forEach((name) => {
  dropZone.addEventListener(name, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove("hover");
  });
});
dropZone.addEventListener("drop", (e) => {
  if (e.dataTransfer.files && e.dataTransfer.files.length) {
    addEvidenceFiles(e.dataTransfer.files);
  }
});

async function analyze() {
  if (!state.evidenceFiles.length) {
    toast("Please attach or capture at least one packaging photograph before running screening.");
    return;
  }
  const busy = document.getElementById("busy");
  const btn = document.getElementById("analyzeBtn");
  busy.style.display = "block";
  btn.disabled = true;
  try {
    const created = await api("/api/scans/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sessionPayload()),
    });
    setSession(created);
    const scanId = state.scanId;

    // Upload all attached packaging photos sequentially
    for (let i = 0; i < state.evidenceFiles.length; i++) {
      const file = state.evidenceFiles[i];
      const form = new FormData();
      form.append("file", file);
      const loc = document.getElementById("location").value.trim();
      if (loc) form.append("user_location", loc);
      const uploadRes = await api(`/api/scans/${scanId}/images`, { method: "POST", body: form });
      if (uploadRes && uploadRes.detected_barcode) {
        const currentBarcode = document.getElementById("barcode").value.trim();
        if (!currentBarcode) {
          document.getElementById("barcode").value = uploadRes.detected_barcode;
          lookup();
          toast(`Barcode ${uploadRes.detected_barcode} automatically detected from panel ${i + 1}`);
        }
      }
    }

    const analysis = await api(`/api/scans/${scanId}/analyze`, { method: "POST" });
    state.analysis = analysis;
    try {
      const fields = await api(`/api/scans/${state.scanId}/extract-fields`, { method: "POST" });
      state.fields = fields.fields || [];
    } catch {
      state.fields = [];
    }
    const name = state.product?.name || document.getElementById("barcode").value.trim() || "Unlisted Pack";
    state.history.unshift({
      id: state.scanId,
      barcode: document.getElementById("barcode").value.trim(),
      name,
      score: analysis.overall_score,
      status: analysis.status,
    });
    saveHistory();
    renderResults();
    loadEvidence();
    showPage("results");
    toast(`Screening pipeline completed across ${state.evidenceFiles.length} packaging panel${state.evidenceFiles.length > 1 ? "s" : ""}`);
  } catch (err) {
    toast(err.message || "Failed to execute compliance screening.");
  } finally {
    busy.style.display = "none";
    btn.disabled = false;
  }
}

function renderResults() {
  const a = state.analysis;
  if (!a) return;
  document.getElementById("resultLede").textContent = `Inspection Session: ${a.inspection_id || a.scan_id}`;
  const score = Math.round(a.overall_score ?? 0);
  document.getElementById("scoreValue").textContent = `${score}%`;
  document.getElementById("riskTitle").textContent = `${a.risk_level || "EVALUATED"} Risk Category`;
  document.getElementById("summaryText").textContent = a.summary || "Statutory rule verification completed.";
  document.getElementById("reportBtn").disabled = false;
  document.getElementById("reviewBtn").disabled = false;
  document.getElementById("pdfLink").style.display = "none";

  const decCard = document.getElementById("declarationsStatusCard");
  const missingSec = document.getElementById("missingDeclarationsSection");
  const missingList = document.getElementById("missingDeclarationsList");
  const detectedSec = document.getElementById("detectedDeclarationsSection");
  const detectedList = document.getElementById("detectedDeclarationsList");

  const detected = a.detected_declarations || [];
  const missing = a.missing_declarations || [];

  if (decCard) {
    if (detected.length || missing.length) {
      decCard.style.display = "block";
      if (missing.length) {
        missingSec.style.display = "block";
        missingList.innerHTML = missing.map((m) => `
          <div class="audit-missing-card">
            <div class="audit-missing-card-head">
              <span class="audit-missing-card-title">${escapeHtml(m.label)}</span>
              <span class="status-tag fail" style="font-size:10px">${escapeHtml(m.rule_number)}</span>
            </div>
            <p class="audit-missing-card-desc">${escapeHtml(m.description)}</p>
            <div class="audit-missing-card-tip">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0;margin-top:2px"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
              <span><strong>Guidance:</strong> ${escapeHtml(m.recommendation)}</span>
            </div>
          </div>
        `).join("");
      } else {
        missingSec.style.display = "none";
      }

      if (detected.length) {
        detectedSec.style.display = "block";
        detectedList.innerHTML = detected.map((d) => {
          let valHtml = escapeHtml(d.value);
          if (d.field === "consumer_care") {
            valHtml = valHtml
              .replace(/(\b\d{3,4}[-\s]?\d{3,4}[-\s]?\d{3,4}\b|\b1800[-\s]?\d{3,4}[-\s]?\d{3,4}\b)/g, '<a href="tel:$1">$1</a>')
              .replace(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g, '<a href="mailto:$1">$1</a>');
          }
          return `
            <div class="audit-detected-card">
              <div class="audit-detected-card-head">
                <span class="audit-detected-card-label">${escapeHtml(d.label)}</span>
                <span class="status-tag pass" style="font-size:10px">${escapeHtml(d.rule_number)}</span>
              </div>
              <div class="audit-detected-card-val">${valHtml}</div>
              <div class="audit-detected-card-meta">
                <span>${d.method === 'AI_LLM_ASSISTED' ? 'AI Vision Extraction' : 'Direct OCR Verification'}</span>
                <span>${Math.round((d.confidence || 0.95) * 100)}% Conf.</span>
              </div>
            </div>
          `;
        }).join("");
      } else {
        detectedSec.style.display = "none";
      }
    } else {
      decCard.style.display = "none";
    }
  }

  const rules = a.rules_summary || [];
  document.getElementById("rulesTable").innerHTML = rules.length
    ? `<div class="table-responsive"><table><thead><tr><th>Statutory Rule</th><th>Finding</th><th>Observation</th></tr></thead><tbody>${
        rules.map((r) => `<tr><td><strong>${escapeHtml(r.rule_id)}</strong><br><span class="muted">${escapeHtml(r.name || "")}</span></td><td>${pill(r.status)}</td><td>${escapeHtml(r.reason || "Verified")}</td></tr>`).join("")
      }</tbody></table></div>`
    : "<p class=\"muted\" style=\"padding:10px 0\">No statutory violations flagged for this session.</p>";

  const discs = a.discrepancies || [];
  document.getElementById("discList").innerHTML = discs.length
    ? discs.map((d) => `
        <div class="list-item">
          <div>
            <div style="font-weight:600">${escapeHtml(d.field)}</div>
            <div class="muted">${escapeHtml(d.difference_summary || "")}</div>
            <div class="muted">Catalog Value: ${escapeHtml(d.catalog_value || "None")} | Detected Value: ${escapeHtml(d.detected_value || "None")}</div>
          </div>
          ${pill(d.status)}
        </div>`).join("")
    : "<p class=\"muted\" style=\"padding:10px 0\">No catalog discrepancies flagged for this item.</p>";

  const labels = FIELD_LABELS;
  document.getElementById("fieldsGrid").innerHTML = (state.fields || []).map((f) => {
    let valHtml = escapeHtml(f.value);
    if (f.field_name === "consumer_care") {
      valHtml = valHtml
        .replace(/(\b\d{3,4}[-\s]?\d{3,4}[-\s]?\d{3,4}\b|\b1800[-\s]?\d{3,4}[-\s]?\d{3,4}\b)/g, '<a href="tel:$1">$1</a>')
        .replace(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g, '<a href="mailto:$1">$1</a>');
    }
    return `
      <div class="product-item">
        <div class="muted" style="font-size:11.5px;font-weight:600;text-transform:uppercase">${labels[f.field_name] || escapeHtml(f.field_name)}</div>
        <div style="margin-top:6px;font-weight:700;font-size:14px">${valHtml}</div>
        <div class="muted" style="font-size:12px;margin-top:4px">${Math.round((f.confidence || 0) * 100)}% Extraction Confidence</div>
        <button type="button" class="ev-link" data-ev-field="${escapeHtml(f.field_name)}">View source on label</button>
      </div>
    `;
  }).join("") || `<p class="muted">No declarations extracted. Ensure the label photograph is sharp and well lit.</p>`;
}

/* =====================================================
   LABEL EVIDENCE VIEWER
   Photo + OCR bounding boxes, linked to extracted declarations
===================================================== */
const evidence = { data: null, imageId: null, activeKey: null };

function evBox(item) {
  const b = item && item.bbox;
  if (!Array.isArray(b) || b.length !== 4) return null;
  const [x1, y1, x2, y2] = b.map(Number);
  if (![x1, y1, x2, y2].every(Number.isFinite) || x2 <= x1 || y2 <= y1) return null;
  return [x1, y1, x2, y2];
}

function evSameBox(a, b) {
  const ba = evBox(a), bb = evBox(b);
  return !!ba && !!bb && ba.every((v, i) => v === bb[i]);
}

function evImages() {
  const imgs = [...(evidence.data?.images || [])];
  return imgs.sort((a, b) => String(a.created_at).localeCompare(String(b.created_at)));
}

function evPanelLabel(idx) {
  return PANEL_LABELS[idx] || `Panel ${idx + 1}`;
}

// Field -> the OCR line it was read from (same image and same box), if any
function evFieldSource(field) {
  if (!field.image_id || !evBox(field)) return null;
  return (evidence.data.ocr_items || []).find((o) => o.image_id === field.image_id && evSameBox(o, field)) || null;
}

function evFieldKey(field) {
  const src = evFieldSource(field);
  return src ? `ocr:${src.id}` : `field:${field.id}`;
}

function evMethodLabel(method) {
  if (method === "AI_LLM_ASSISTED") return "AI-assisted";
  if (String(method || "").includes("CATALOG")) return "Catalog";
  return "OCR";
}

async function loadEvidence() {
  const card = document.getElementById("evidenceCard");
  if (!state.scanId) {
    card.style.display = "none";
    return;
  }
  try {
    evidence.data = await api(`/api/scans/${state.scanId}/evidence`);
    evidence.activeKey = null;
    const images = evImages();
    if (!images.length) {
      card.style.display = "none";
      return;
    }
    card.style.display = "block";
    const withText = images.find((img) => evidence.data.ocr_items.some((o) => o.image_id === img.id));
    renderEvidencePanels();
    selectEvidenceImage((withText || images[0]).id);
  } catch (_) {
    card.style.display = "none";
  }
}

function renderEvidencePanels() {
  const panels = document.getElementById("evPanels");
  const images = evImages();
  panels.innerHTML = images.map((img, idx) => {
    const lines = evidence.data.ocr_items.filter((o) => o.image_id === img.id).length;
    return `
      <button type="button" class="ev-panel" role="tab" data-ev-image="${escapeHtml(img.id)}">
        <img src="/api/scans/${encodeURIComponent(state.scanId)}/images/${encodeURIComponent(img.id)}/file" alt="" loading="lazy" />
        <span>${escapeHtml(evPanelLabel(idx))}<small>${lines} text line${lines === 1 ? "" : "s"}</small></span>
      </button>`;
  }).join("");
  panels.hidden = images.length < 2;
}

function selectEvidenceImage(imageId) {
  evidence.imageId = imageId;
  document.querySelectorAll("#evPanels .ev-panel").forEach((b) => {
    const on = b.dataset.evImage === imageId;
    b.classList.toggle("active", on);
    b.setAttribute("aria-selected", String(on));
  });
  const img = document.getElementById("evImage");
  img.onload = drawEvidenceOverlay;
  img.src = `/api/scans/${encodeURIComponent(state.scanId)}/images/${encodeURIComponent(imageId)}/file`;
  if (img.complete && img.naturalWidth) drawEvidenceOverlay();
  renderEvidenceLists();
}

function drawEvidenceOverlay() {
  const img = document.getElementById("evImage");
  const svg = document.getElementById("evOverlay");
  const W = img.naturalWidth, H = img.naturalHeight;
  if (!W || !H || !evidence.data) return;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const showAll = document.getElementById("evShowAll").checked;
  const fields = evidence.data.detected_fields.filter((f) => f.image_id === evidence.imageId && evBox(f));
  const fieldByKey = new Map(fields.map((f) => [evFieldKey(f), f]));
  // Label text renders at ~12px on screen whatever the photo resolution
  const fontSize = Math.round(12 * (W / (img.clientWidth || W)));
  const shapes = [];

  const shape = (key, item, cls, label) => {
    const [x1, y1, x2, y2] = evBox(item);
    const poly = Array.isArray(item.polygon) && item.polygon.length >= 4
      ? item.polygon.map((p) => `${Number(p[0])},${Number(p[1])}`).join(" ")
      : `${x1},${y1} ${x2},${y1} ${x2},${y2} ${x1},${y2}`;
    const active = key === evidence.activeKey ? " is-active" : "";
    let out = `<polygon class="ev-box ${cls}${active}" data-key="${escapeHtml(key)}" points="${poly}" vector-effect="non-scaling-stroke"><title>${escapeHtml(label)}</title></polygon>`;
    if (active) {
      const ty = y1 - fontSize * 0.35 > fontSize ? y1 - fontSize * 0.35 : y2 + fontSize;
      out += `<text class="ev-tag${active}" x="${x1}" y="${ty}" font-size="${fontSize}">${escapeHtml(label)}</text>`;
    }
    return out;
  };

  evidence.data.ocr_items.filter((o) => o.image_id === evidence.imageId && evBox(o)).forEach((o) => {
    const key = `ocr:${o.id}`;
    const field = fieldByKey.get(key);
    if (!field && !showAll && key !== evidence.activeKey) return;
    const low = (o.confidence ?? 1) < 0.6 ? " is-low" : "";
    const label = field
      ? `${FIELD_LABELS[field.field_name] || field.field_name} (${Math.round((o.confidence || 0) * 100)}%)`
      : `${o.text} (${Math.round((o.confidence || 0) * 100)}%)`;
    shapes.push(shape(key, o, field ? `is-field${low}` : `is-ocr${low}`, label));
  });
  // Fields whose box does not match a stored OCR line still get drawn
  fields.filter((f) => !evFieldSource(f)).forEach((f) => {
    shapes.push(shape(`field:${f.id}`, f, "is-field", FIELD_LABELS[f.field_name] || f.field_name));
  });
  // Active box last so it sits on top
  shapes.sort((a, b) => (a.includes("is-active") ? 1 : 0) - (b.includes("is-active") ? 1 : 0));
  svg.innerHTML = shapes.join("");
}

function renderEvidenceLists() {
  const data = evidence.data;
  const images = evImages();
  const imageIdx = (id) => images.findIndex((i) => i.id === id);

  document.getElementById("evFields").innerHTML = data.detected_fields.length
    ? data.detected_fields.map((f) => {
        const located = f.image_id && evBox(f) && imageIdx(f.image_id) >= 0;
        const where = !located
          ? `<span class="ev-where ev-where-none">${{ "AI-assisted": "Inferred by AI from label text; no single location", Catalog: "Taken from the reference catalog, not read from the photo" }[evMethodLabel(f.extraction_method)] || "No location recorded"}</span>`
          : f.image_id === evidence.imageId
            ? `<span class="ev-where">On this photo</span>`
            : `<span class="ev-where">On ${escapeHtml(evPanelLabel(imageIdx(f.image_id)))}</span>`;
        const key = located ? evFieldKey(f) : "";
        return `
          <button type="button" class="ev-row ev-field-row${key && key === evidence.activeKey ? " active" : ""}" ${located ? `data-key="${escapeHtml(key)}" data-image="${escapeHtml(f.image_id)}"` : "disabled"} data-field-name="${escapeHtml(f.field_name)}">
            <span class="ev-row-main">
              <strong>${escapeHtml(FIELD_LABELS[f.field_name] || f.field_name)}</strong>
              <span class="ev-row-value">${escapeHtml(f.value)}</span>
              ${f.raw_text && f.raw_text !== f.value ? `<span class="ev-row-raw">Read as: "${escapeHtml(f.raw_text)}"</span>` : ""}
              ${where}
            </span>
            <span class="ev-row-meta">
              <span class="ev-method ev-method-${escapeHtml(evMethodLabel(f.extraction_method).toLowerCase().replace(/[^a-z]/g, ""))}">${escapeHtml(evMethodLabel(f.extraction_method))}</span>
              <span class="ev-conf">${Math.round((f.confidence || 0) * 100)}%</span>
            </span>
          </button>`;
      }).join("")
    : `<p class="muted">No declarations were extracted.</p>`;

  const lines = data.ocr_items.filter((o) => o.image_id === evidence.imageId);
  const fieldKeys = new Map(data.detected_fields.map((f) => [evFieldKey(f), f]));
  document.getElementById("evOcrCount").textContent = lines.length ? `(${lines.length})` : "";
  document.getElementById("evOcrLines").innerHTML = lines.length
    ? lines.map((o) => {
        const key = `ocr:${o.id}`;
        const field = fieldKeys.get(key);
        const pct = Math.round((o.confidence || 0) * 100);
        const level = pct < 60 ? "low" : pct < 85 ? "mid" : "high";
        return `
          <button type="button" class="ev-row ev-ocr-row${key === evidence.activeKey ? " active" : ""}" data-key="${escapeHtml(key)}" data-image="${escapeHtml(o.image_id)}" ${evBox(o) ? "" : "disabled"}>
            <span class="ev-row-main">
              <span class="ev-ocr-text">${escapeHtml(o.text)}</span>
              ${field ? `<span class="ev-where">${escapeHtml(FIELD_LABELS[field.field_name] || field.field_name)}</span>` : ""}
            </span>
            <span class="ev-confbar ev-conf-${level}" title="OCR confidence ${pct}%"><i style="width:${pct}%"></i><b>${pct}%</b></span>
          </button>`;
      }).join("")
    : `<p class="muted">No OCR text was recorded for this photo${data.ocr_items.length ? "" : " (the OCR engine did not run for this inspection)"}.</p>`;
}

function setEvidenceActive(key, imageId, scrollList) {
  evidence.activeKey = evidence.activeKey === key ? null : key;
  if (imageId && imageId !== evidence.imageId) {
    selectEvidenceImage(imageId);
  } else {
    drawEvidenceOverlay();
    renderEvidenceLists();
  }
  if (scrollList && evidence.activeKey) {
    const row = document.querySelector(`#evOcrLines [data-key="${CSS.escape(evidence.activeKey)}"], #evFields [data-key="${CSS.escape(evidence.activeKey)}"]`);
    if (row) row.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
}

document.getElementById("evPanels").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-ev-image]");
  if (btn) {
    evidence.activeKey = null;
    selectEvidenceImage(btn.dataset.evImage);
  }
});
document.getElementById("evOverlay").addEventListener("click", (e) => {
  const box = e.target.closest("[data-key]");
  if (box) setEvidenceActive(box.dataset.key, evidence.imageId, true);
});
["evFields", "evOcrLines"].forEach((id) => {
  document.getElementById(id).addEventListener("click", (e) => {
    const row = e.target.closest("[data-key]");
    if (!row || row.disabled) return;
    setEvidenceActive(row.dataset.key, row.dataset.image, false);
    if (window.matchMedia("(max-width: 860px)").matches) {
      document.getElementById("evStage").scrollIntoView({ block: "center", behavior: "smooth" });
    }
  });
});
document.getElementById("evShowAll").addEventListener("change", drawEvidenceOverlay);
let evResizeTimer = null;
window.addEventListener("resize", () => {
  clearTimeout(evResizeTimer);
  evResizeTimer = setTimeout(() => { if (evidence.data && evidence.activeKey) drawEvidenceOverlay(); }, 150);
});
document.getElementById("fieldsGrid").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-ev-field]");
  if (!btn || !evidence.data) return;
  const card = document.getElementById("evidenceCard");
  card.scrollIntoView({ block: "start", behavior: "smooth" });
  const row = document.querySelector(`#evFields [data-field-name="${CSS.escape(btn.dataset.evField)}"]`);
  if (row && !row.disabled) {
    evidence.activeKey = null;
    setEvidenceActive(row.dataset.key, row.dataset.image, false);
  } else {
    toast("This declaration has no recorded location on the photos.");
  }
});

async function generateReport() {
  if (!state.scanId) return;
  try {
    const report = await api(`/api/scans/${state.scanId}/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        officer_notes: document.getElementById("notes").value.trim() || null,
        authority_name: "Legal Metrology Enforcement Directorate",
        authority_jurisdiction: document.getElementById("location").value.trim() || "National Jurisdiction",
      }),
    });
    const link = document.getElementById("pdfLink");
    link.href = API + (report.pdf_download_url || `/api/scans/${state.scanId}/report/pdf`);
    link.style.display = "inline-flex";
    toast(`Inspection report ${report.report_number} generated`);
  } catch (err) {
    toast(err.message);
  }
}

async function submitReview() {
  if (!state.scanId) return;
  try {
    await api(`/api/scans/${state.scanId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        officer_determination: document.getElementById("determination").value,
        officer_remarks: document.getElementById("remarks").value.trim() || null,
        officer_id: document.getElementById("officerId").value.trim() || null,
      }),
    });
    toast("Officer determination recorded successfully");
  } catch (err) {
    toast(err.message);
  }
}

const chatHistory = [];

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatInlineMarkdown(text) {
  return text
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*]+)\*(?!\*)/g, "$1<em>$2</em>")
    .replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
    );
}

function formatChatMarkdown(raw) {
  const escaped = escapeHtml(String(raw || "").trim());
  const lines = escaped.split(/\r?\n/);
  const html = [];
  let i = 0;
  let inFence = false;
  let code = [];
  let listKind = null;
  let items = [];
  let para = [];

  const flushList = () => {
    if (!listKind) return;
    html.push(
      `<${listKind}>${items.map((item) => `<li>${formatInlineMarkdown(item)}</li>`).join("")}</${listKind}>`
    );
    listKind = null;
    items = [];
  };
  const flushPara = () => {
    if (!para.length) return;
    html.push(`<p>${formatInlineMarkdown(para.join(" "))}</p>`);
    para = [];
  };

  while (i < lines.length) {
    const line = lines[i];
    if (line.startsWith("```")) {
      flushList();
      flushPara();
      if (inFence) {
        html.push(`<pre><code>${code.join("\n")}</code></pre>`);
        code = [];
        inFence = false;
      } else {
        inFence = true;
      }
      i += 1;
      continue;
    }
    if (inFence) {
      code.push(line);
      i += 1;
      continue;
    }
    if (/^\s*$/.test(line)) {
      flushList();
      flushPara();
      i += 1;
      continue;
    }
    const heading = line.match(/^#{1,6}\s+(.+)$/);
    const ul = line.match(/^\s*[-*]\s+(.+)$/);
    const ol = line.match(/^\s*\d+[.)]\s+(.+)$/);
    if (heading) {
      flushList();
      flushPara();
      html.push(`<p><strong>${formatInlineMarkdown(heading[1])}</strong></p>`);
      i += 1;
      continue;
    }
    if (ul) {
      flushPara();
      if (listKind && listKind !== "ul") flushList();
      listKind = "ul";
      items.push(ul[1]);
      i += 1;
      continue;
    }
    if (ol) {
      flushPara();
      if (listKind && listKind !== "ol") flushList();
      listKind = "ol";
      items.push(ol[1]);
      i += 1;
      continue;
    }
    flushList();
    para.push(line);
    i += 1;
  }
  if (inFence) html.push(`<pre><code>${code.join("\n")}</code></pre>`);
  flushList();
  flushPara();
  return html.join("") || "<p></p>";
}

function currentScanContext() {
  const a = state.analysis;
  if (!a) return null;
  return {
    scan_id: state.scanId,
    product: state.product ? { name: state.product.name, barcode: state.product.barcode } : null,
    overall_score: a.overall_score,
    risk_level: a.risk_level,
    status: a.status,
    summary: a.summary,
    results: (a.results || []).map((r) => ({
      name: r.name,
      status: r.status,
      reason: r.reason,
    })),
  };
}

async function sendChat() {
  const input = document.getElementById("chatInput");
  const sendBtn = document.getElementById("chatSend");
  const text = input.value.trim();
  if (!text || sendBtn.disabled) return;
  const box = document.getElementById("messages");
  const user = document.createElement("div");
  user.className = "msg user";
  user.textContent = text;
  box.appendChild(user);
  input.value = "";
  const bot = document.createElement("div");
  bot.className = "msg bot";
  bot.textContent = "Processing inquiry...";
  box.appendChild(bot);
  box.scrollTop = box.scrollHeight;
  sendBtn.disabled = true;
  try {
    const data = await api("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        history: chatHistory,
        scan_context: currentScanContext(),
      }),
    });
    bot.innerHTML = formatChatMarkdown(data.reply);
    chatHistory.push({ role: "user", content: text });
    chatHistory.push({ role: "assistant", content: data.reply });
  } catch (err) {
    bot.textContent = err.message || "Query communication failure.";
  } finally {
    sendBtn.disabled = false;
    box.scrollTop = box.scrollHeight;
  }
}

document.getElementById("lookupBtn").addEventListener("click", lookup);
document.getElementById("createBtn").addEventListener("click", createSession);
document.getElementById("analyzeBtn").addEventListener("click", analyze);
document.getElementById("reportBtn").addEventListener("click", generateReport);
document.getElementById("reviewBtn").addEventListener("click", submitReview);
document.getElementById("chatSend").addEventListener("click", sendChat);
document.getElementById("chatInput").addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendChat();
});

const catSearch = document.getElementById("catalogSearch");
if (catSearch) {
  catSearch.addEventListener("input", renderCatalog);
}
const catFilter = document.getElementById("catalogCategoryFilter");
if (catFilter) {
  catFilter.addEventListener("change", renderCatalog);
}

/* =====================================================
   CAMERA & PHOTO BARCODE & LABEL CAPTURE
===================================================== */
let cameraStream = null;
let cameraFacingMode = "environment";
let barcodeScanningActive = false;
let cameraMode = "barcode"; // "barcode" or "label"

async function startCamera(mode = "barcode") {
  cameraMode = mode;
  const modal = document.getElementById("cameraModal");
  const video = document.getElementById("cameraVideo");
  const status = document.getElementById("cameraStatus");
  const title = modal.querySelector(".modal-header span");
  const reticle = modal.querySelector(".camera-reticle");
  const captureBtn = document.getElementById("captureFrameBtn");
  const doneBtn = document.getElementById("doneCameraBtn");
  if (!modal || !video) return;

  modal.style.display = "flex";
  status.textContent = "Requesting camera access...";

  if (cameraMode === "label" || cameraMode === "complaint") {
    title.textContent = cameraMode === "complaint" ? "Photograph the Product Label" : "Capture Package Label Photo (Multiple Panels)";
    reticle.style.width = "88%";
    reticle.style.height = "80%";
    reticle.style.borderColor = "#0f766e";
    captureBtn.textContent = "Capture Photo";
    if (doneBtn) doneBtn.style.display = "inline-flex";
  } else {
    title.textContent = "Camera Barcode Scanner";
    reticle.style.width = "75%";
    reticle.style.height = "48%";
    reticle.style.borderColor = "#38bdf8";
    captureBtn.textContent = "Capture Frame";
    if (doneBtn) doneBtn.style.display = "none";
  }

  try {
    if (cameraStream) {
      cameraStream.getTracks().forEach((t) => t.stop());
    }
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: cameraFacingMode, width: { ideal: 1920 }, height: { ideal: 1080 } },
      audio: false,
    });
    video.srcObject = cameraStream;
    await video.play();

    if (cameraMode === "label" || cameraMode === "complaint") {
      status.textContent = `Position packaging panel (front, back, or side declarations) and tap Capture Photo.`;
      barcodeScanningActive = false;
    } else {
      status.textContent = "Align barcode within the reticle...";
      barcodeScanningActive = true;
      startBarcodeScanLoop();
    }
  } catch (err) {
    status.textContent = "Camera access unavailable: " + err.message;
  }
}

function stopCamera() {
  barcodeScanningActive = false;
  if (cameraStream) {
    cameraStream.getTracks().forEach((t) => t.stop());
    cameraStream = null;
  }
  const modal = document.getElementById("cameraModal");
  if (modal) modal.style.display = "none";
}

async function captureAction() {
  if (cameraMode === "label" || cameraMode === "complaint") {
    captureLabelPhoto();
  } else {
    captureAndDecodeFrame(true);
  }
}

function captureLabelPhoto() {
  const video = document.getElementById("cameraVideo");
  const canvas = document.getElementById("cameraCanvas");
  const status = document.getElementById("cameraStatus");
  if (!video || video.readyState < 2) return;

  canvas.width = video.videoWidth || 1280;
  canvas.height = video.videoHeight || 720;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  canvas.toBlob((blob) => {
    if (!blob) return;
    if (cameraMode === "complaint") {
      const added = addComplaintPhotos([new File([blob], `label_photo_${Date.now()}.jpg`, { type: "image/jpeg" })]);
      if (added) status.textContent = `Photo ${complaintPhotos.length} captured. Take another or tap Done.`;
      return;
    }
    const count = state.evidenceFiles.length + 1;
    const file = new File([blob], `packaging_panel_${count}.jpg`, { type: "image/jpeg" });
    addEvidenceFiles([file]);
    status.textContent = `Panel #${count} captured! Position another panel (back, side, or barcode) and tap Capture Photo, or tap Done.`;
    toast(`Packaging panel #${count} added to evidence queue`);
  }, "image/jpeg", 0.92);
}

async function startBarcodeScanLoop() {
  if (!barcodeScanningActive || cameraMode !== "barcode") return;

  // 1. Modern browser BarcodeDetector API
  if ("BarcodeDetector" in window) {
    try {
      const barcodeDetector = new window.BarcodeDetector({
        formats: ["ean_13", "ean_8", "upc_a", "upc_e", "code_128", "code_39", "qr_code"],
      });
      const video = document.getElementById("cameraVideo");
      const detectFrame = async () => {
        if (!barcodeScanningActive || cameraMode !== "barcode") return;
        if (video.readyState >= 2) {
          try {
            const barcodes = await barcodeDetector.detect(video);
            if (barcodes.length > 0) {
              const code = barcodes[0].rawValue;
              if (code && code.trim()) {
                onBarcodeDetected(code.trim(), "Camera Real-Time Scanner");
                return;
              }
            }
          } catch (_) {}
        }
        requestAnimationFrame(detectFrame);
      };
      requestAnimationFrame(detectFrame);
      return;
    } catch (_) {}
  }

  // 2. Periodic frame fallback to OpenCV backend /api/products/scan-barcode
  const intervalId = setInterval(async () => {
    if (!barcodeScanningActive || cameraMode !== "barcode") {
      clearInterval(intervalId);
      return;
    }
    await captureAndDecodeFrame(false);
  }, 1400);
}

async function captureAndDecodeFrame(manual = true) {
  const video = document.getElementById("cameraVideo");
  const canvas = document.getElementById("cameraCanvas");
  const status = document.getElementById("cameraStatus");
  if (!video || video.readyState < 2) return;

  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  if (manual) {
    status.textContent = "Analyzing captured frame...";
  }

  canvas.toBlob(async (blob) => {
    if (!blob || !barcodeScanningActive) return;
    try {
      const formData = new FormData();
      formData.append("file", blob, "camera_frame.jpg");
      const res = await api("/api/products/scan-barcode", { method: "POST", body: formData });
      if (res && res.found && res.barcode) {
        onBarcodeDetected(res.barcode, "OpenCV Vision Pipeline");
      } else if (manual) {
        status.textContent = "No barcode detected in frame. Adjust distance or lighting and retry.";
      }
    } catch (err) {
      if (manual) status.textContent = "Frame analysis error: " + err.message;
    }
  }, "image/jpeg", 0.85);
}

function onBarcodeDetected(code, source = "Scanner") {
  stopCamera();
  const input = document.getElementById("barcode");
  input.value = code;
  lookup();
  toast(`Barcode ${code} detected via ${source}`);
}

async function scanBarcodeFromFile(file) {
  if (!file) return;
  toast("Scanning photo for barcode...");
  try {
    const formData = new FormData();
    formData.append("file", file);
    const res = await api("/api/products/scan-barcode", { method: "POST", body: formData });
    if (res && res.found && res.barcode) {
      onBarcodeDetected(res.barcode, "Image Decoder");
    } else {
      toast("No barcode or QR code recognized in selected photo.");
    }
  } catch (err) {
    toast("Barcode extraction error: " + err.message);
  }
}

// Mobile Nav Toggle Listener
const navToggleBtn = document.getElementById("navToggle");
if (navToggleBtn) {
  navToggleBtn.addEventListener("click", () => {
    const nav = document.getElementById("mainNav");
    if (nav) {
      const isOpen = nav.classList.toggle("nav-open");
      navToggleBtn.setAttribute("aria-expanded", String(isOpen));
    }
  });
}

document.getElementById("scanCameraBtn").addEventListener("click", () => startCamera("barcode"));
document.getElementById("snapLabelCameraBtn").addEventListener("click", () => startCamera("label"));
document.getElementById("closeCameraBtn").addEventListener("click", stopCamera);
const doneCam = document.getElementById("doneCameraBtn");
if (doneCam) doneCam.addEventListener("click", stopCamera);
document.getElementById("captureFrameBtn").addEventListener("click", captureAction);
document.getElementById("switchCameraBtn").addEventListener("click", () => {
  cameraFacingMode = cameraFacingMode === "environment" ? "user" : "environment";
  startCamera(cameraMode);
});
document.getElementById("barcodeImageInput").addEventListener("change", (e) => {
  if (e.target.files && e.target.files[0]) {
    scanBarcodeFromFile(e.target.files[0]);
  }
});
document.getElementById("mobileCameraInput").addEventListener("change", (e) => {
  if (e.target.files && e.target.files.length) {
    addEvidenceFiles(e.target.files);
    e.target.value = "";
  }
});

// Accessibility font scaling (A-, A, A+)
let currentFontScale = 100;
function setFontScale(scale) {
  currentFontScale = Math.max(80, Math.min(135, scale));
  document.documentElement.style.fontSize = `${currentFontScale}%`;
  try {
    localStorage.setItem("packsure_font_scale", String(currentFontScale));
  } catch (_) {}
}
try {
  const savedScale = localStorage.getItem("packsure_font_scale");
  if (savedScale) setFontScale(parseInt(savedScale, 10));
} catch (_) {}

const fontDecBtn = document.getElementById("fontDec");
if (fontDecBtn) fontDecBtn.addEventListener("click", () => setFontScale(currentFontScale - 10));
const fontNormalBtn = document.getElementById("fontNormal");
if (fontNormalBtn) fontNormalBtn.addEventListener("click", () => setFontScale(100));
const fontIncBtn = document.getElementById("fontInc");
if (fontIncBtn) fontIncBtn.addEventListener("click", () => setFontScale(currentFontScale + 10));

// Keyboard interaction for card buttons
document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    const card = e.target.closest('.service-card[data-page]');
    if (card && card.dataset.page) {
      e.preventDefault();
      showPage(card.dataset.page);
    }
  }
});

// ==========================================
// Officer Authentication & Verification Gate
// ==========================================
function renderOfficerStatus() {
  const topContainer = document.getElementById("topbarOfficerContainer");
  const bannerContainer = document.getElementById("officerInspectBannerContainer");
  const officerInput = document.getElementById("officerId");

  const loginActiveCard = document.getElementById("loginActiveOfficerCard");
  const loginFormCard = document.getElementById("loginFormCard");
  const loginActiveName = document.getElementById("loginActiveName");
  const loginActiveBadge = document.getElementById("loginActiveBadge");
  const loginActiveJurisdiction = document.getElementById("loginActiveJurisdiction");
  const loginActiveProvider = document.getElementById("loginActiveProvider");

  // Modal active card elements
  const modalActiveCard = document.getElementById("modalActiveOfficerCard");
  const modalOfficerName = document.getElementById("modalOfficerName");
  const modalOfficerBadge = document.getElementById("modalOfficerBadge");
  const modalOfficerJurisdiction = document.getElementById("modalOfficerJurisdiction");
  const modalOfficerEmail = document.getElementById("modalOfficerEmail");
  const modalOfficerProvider = document.getElementById("modalOfficerProvider");
  const modalLogoutBtn = document.getElementById("modalOfficerLogoutBtn");

  if (state.officer) {
    // Only profile pic in corner with green status dot - NO NAMES OR SIGN IN/OUT ON TOPBAR
    if (topContainer) {
      topContainer.innerHTML = `
        <button type="button" class="officer-profile-btn logged-in" id="openOfficerAuthBtn" title="Officer Profile: ${escapeHtml(state.officer.name)} (${escapeHtml(state.officer.officer_badge)})" aria-label="Officer Profile">
          <span class="officer-avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
          </span>
          <span class="officer-status-dot" title="Active Official Session"></span>
        </button>
      `;
      const btn = document.getElementById("openOfficerAuthBtn");
      if (btn) btn.addEventListener("click", openOfficerModal);
    }

    // Modal Active Card
    if (modalActiveCard) {
      modalActiveCard.style.display = "block";
      if (modalOfficerName) modalOfficerName.textContent = state.officer.name;
      if (modalOfficerBadge) modalOfficerBadge.textContent = state.officer.officer_badge;
      if (modalOfficerJurisdiction) modalOfficerJurisdiction.textContent = state.officer.jurisdiction || "National Directorate, New Delhi";
      if (modalOfficerEmail) modalOfficerEmail.textContent = state.officer.email || "";
      if (modalOfficerProvider) modalOfficerProvider.textContent = (state.officer.authorized_provider || "Gov ID").toUpperCase();
      if (modalLogoutBtn) {
        modalLogoutBtn.onclick = () => {
          logoutOfficer();
          closeOfficerModal();
        };
      }
    }

    // Inspection Banner
    if (bannerContainer) {
      bannerContainer.innerHTML = `
        <div class="officer-inspect-banner">
          <div>
            <strong>Authorized Enforcement Officer:</strong> ${escapeHtml(state.officer.name)} &middot; Badge <span class="badge">${escapeHtml(state.officer.officer_badge)}</span> &middot; Jurisdiction: ${escapeHtml(state.officer.jurisdiction || "National")}
          </div>
          <div style="display:flex;gap:8px;align-items:center;">
            <button type="button" class="btn btn-ghost btn-sm" id="inspectSwitchOfficerBtn" style="padding:4px 8px;font-size:11.5px;color:#cbd5e1;border-color:#334155;">Switch Officer</button>
            <button type="button" class="btn-officer-logout" id="inspectLogoutBtn" style="padding:4px 8px;font-size:11.5px;">Logout</button>
          </div>
        </div>
      `;
      const switchBtn = document.getElementById("inspectSwitchOfficerBtn");
      if (switchBtn) switchBtn.addEventListener("click", openOfficerModal);
      const bannerLogout = document.getElementById("inspectLogoutBtn");
      if (bannerLogout) bannerLogout.addEventListener("click", logoutOfficer);
    }

    // Dedicated Login Page Card
    if (loginActiveCard) loginActiveCard.style.display = "block";
    if (loginFormCard) loginFormCard.style.display = "none";
    if (loginActiveName) loginActiveName.textContent = state.officer.name;
    if (loginActiveBadge) loginActiveBadge.textContent = state.officer.officer_badge;
    if (loginActiveJurisdiction) loginActiveJurisdiction.textContent = state.officer.jurisdiction || "National Directorate, New Delhi";
    if (loginActiveProvider) loginActiveProvider.textContent = (state.officer.authorized_provider || "Government Identity").toUpperCase();

    // Auto-fill officer input
    if (officerInput && (!officerInput.value || officerInput.dataset.autoFilled === "true")) {
      officerInput.value = state.officer.officer_badge;
      officerInput.dataset.autoFilled = "true";
    }
  } else {
    // Only profile pic in corner - NO NAME OR SIGN IN TEXT ON TOPBAR
    if (topContainer) {
      topContainer.innerHTML = `
        <button type="button" class="officer-profile-btn" id="openOfficerAuthBtn" title="Official Government Access" aria-label="Official Sign In">
          <span class="officer-avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
          </span>
        </button>
      `;
      const btn = document.getElementById("openOfficerAuthBtn");
      if (btn) btn.addEventListener("click", openOfficerModal);
    }

    if (modalActiveCard) {
      modalActiveCard.style.display = "none";
    }

    // Inspection Banner
    if (bannerContainer) {
      bannerContainer.innerHTML = `
        <div class="helpdesk-alert" style="margin-bottom:20px">
          <div style="font-weight:700;margin-bottom:2px">Official Access Required</div>
          <div>Package compliance screening is restricted to authorized Legal Metrology enforcement officers under Section 18 of the Legal Metrology Act, 2009. Please authenticate your credentials to conduct an inspection.</div>
          <div style="display:flex;gap:10px;margin-top:10px;flex-wrap:wrap;">
            <button type="button" class="btn btn-primary btn-sm" id="inspectLoginPromptBtn">Authenticate Officer ID</button>
            <button type="button" class="btn btn-ghost btn-sm" id="inspectPortalPromptBtn" data-page="login">Open Officer Portal</button>
          </div>
        </div>
      `;
      const promptBtn = document.getElementById("inspectLoginPromptBtn");
      if (promptBtn) promptBtn.addEventListener("click", openOfficerModal);
      const portalBtn = document.getElementById("inspectPortalPromptBtn");
      if (portalBtn) portalBtn.addEventListener("click", () => showPage("login"));
    }

    // Dedicated Login Page Card
    if (loginActiveCard) loginActiveCard.style.display = "none";
    if (loginFormCard) loginFormCard.style.display = "block";

    // Clear officer input if previously auto-filled
    if (officerInput && officerInput.dataset.autoFilled === "true") {
      officerInput.value = "";
      delete officerInput.dataset.autoFilled;
    }
  }
}

function openOfficerModal() {
  const modal = document.getElementById("officerAuthModal");
  if (modal) modal.style.display = "flex";
  const notice = document.getElementById("officerHelpdeskNotice");
  if (notice) notice.style.display = "none";
  renderOfficerStatus();
}

function closeOfficerModal() {
  const modal = document.getElementById("officerAuthModal");
  if (modal) modal.style.display = "none";
}

function logoutOfficer() {
  endSession("Officer session ended. Logged out successfully.");
}

async function verifyOfficerEmail(email, provider = "gmail", claimedName = null) {
  if (!email || !email.trim()) {
    toast("Please enter an official email address.");
    return;
  }
  toast("Verifying credentials against National Legal Metrology Officer Database...");
  const noticeModal = document.getElementById("officerHelpdeskNotice");
  const noticePage = document.getElementById("loginPageHelpdeskNotice");
  if (noticeModal) noticeModal.style.display = "none";
  if (noticePage) noticePage.style.display = "none";

  try {
    const res = await api("/api/officers/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.trim(), provider, claimed_name: claimedName }),
    });

    if (res.verified && res.officer) {
      startSession(res.token, res.officer);
      closeOfficerModal();
      toast(res.message);
      showPage("inspect");
    } else {
      if (noticeModal) {
        noticeModal.style.display = "block";
        const msgEl = document.getElementById("officerHelpdeskMessage");
        if (msgEl) msgEl.textContent = res.message;
        const ticketEl = document.getElementById("officerHelpdeskTicket");
        if (ticketEl) ticketEl.textContent = res.ticket_no || "LM-HLP-QUEUED";
      }
      if (noticePage) {
        noticePage.style.display = "block";
        const msgEl = document.getElementById("loginPageHelpdeskMsg");
        if (msgEl) msgEl.textContent = res.message;
        const ticketEl = document.getElementById("loginPageHelpdeskTicket");
        if (ticketEl) ticketEl.textContent = res.ticket_no || "LM-HLP-QUEUED";
      }
      toast(`Access Denied: Ticket ${res.ticket_no} created.`);
    }
  } catch (err) {
    toast("Verification service error: " + err.message);
  }
}

// Wire up Officer Authentication listeners
const closeAuthBtn = document.getElementById("closeOfficerAuthBtn");
if (closeAuthBtn) closeAuthBtn.addEventListener("click", closeOfficerModal);

const officerForm = document.getElementById("officerVerifyForm");
if (officerForm) {
  officerForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const email = document.getElementById("officerEmailInput").value;
    verifyOfficerEmail(email, "email");
  });
}

// Quick pre-authorized test officer buttons in modal
document.querySelectorAll("#officerDemoCardsGrid .officer-card-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const email = btn.dataset.officerEmail;
    if (email) verifyOfficerEmail(email, "demo");
  });
});

// Identity Provider Buttons in modal (Gmail, Yahoo, Apple ID, NIC)
const providerGmail = document.getElementById("providerGmailBtn");
if (providerGmail) {
  providerGmail.addEventListener("click", () => {
    verifyOfficerEmail("ronak.pandey@gmail.com", "gmail", "Ronak Pandey");
  });
}
const providerYahoo = document.getElementById("providerYahooBtn");
if (providerYahoo) {
  providerYahoo.addEventListener("click", () => {
    verifyOfficerEmail("vibha.pawar@yahoo.com", "yahoo", "Vibha Pawar");
  });
}
const providerApple = document.getElementById("providerAppleBtn");
if (providerApple) {
  providerApple.addEventListener("click", () => {
    verifyOfficerEmail("harsh.nagvekar@icloud.com", "apple", "Harsh Nagvekar");
  });
}
const providerGov = document.getElementById("providerGovBtn");
if (providerGov) {
  providerGov.addEventListener("click", () => {
    verifyOfficerEmail("ronak.pandey@gov.in", "gov", "Ronak Pandey");
  });
}

// Dedicated Login Page Listeners
const loginPageForm = document.getElementById("loginPageOfficerForm");
if (loginPageForm) {
  loginPageForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const input = document.getElementById("loginPageEmailInput");
    if (input) verifyOfficerEmail(input.value, "email");
  });
}

document.querySelectorAll(".page-provider-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const email = btn.dataset.email;
    const provider = btn.dataset.provider || "gov";
    const name = btn.dataset.name || null;
    if (email) verifyOfficerEmail(email, provider, name);
  });
});

document.querySelectorAll(".page-card-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const email = btn.dataset.officerEmail;
    if (email) verifyOfficerEmail(email, "demo");
  });
});

const loginPageLogout = document.getElementById("loginPageLogoutBtn");
if (loginPageLogout) {
  loginPageLogout.addEventListener("click", logoutOfficer);
}

// ==========================================
// Session & Entry Gate (Sign In / Register)
// ==========================================
function startSession(token, officer) {
  state.token = token || null;
  state.officer = officer;
  try {
    if (token) localStorage.setItem("packsure_token", token);
    localStorage.setItem("packsure_officer", JSON.stringify(officer));
  } catch (_) {}
  renderOfficerStatus();
  hideGate();
  startComplaintPolling();
}

function endSession(message) {
  const wasSignedIn = !!state.token;
  state.token = null;
  state.officer = null;
  try {
    localStorage.removeItem("packsure_token");
    localStorage.removeItem("packsure_officer");
  } catch (_) {}
  stopComplaintPolling();
  photoBlobCache.forEach((url) => URL.revokeObjectURL(url));
  photoBlobCache.clear();
  renderOfficerStatus();
  closeOfficerModal();
  showGate("auth");
  if (message && wasSignedIn) toast(message);
}

function showGate(view = "auth") {
  document.documentElement.classList.add("gate-open");
  setGateView(view);
}

function hideGate() {
  document.documentElement.classList.remove("gate-open");
  window.scrollTo({ top: 0, behavior: "instant" });
}

function setGateView(view) {
  const views = { auth: "gateAuthView", complaint: "gateComplaintView", success: "gateSuccessView" };
  Object.entries(views).forEach(([key, id]) => {
    const el = document.getElementById(id);
    if (el) el.hidden = key !== view;
  });
  if (view === "complaint") loadIssueTypes();
  window.scrollTo({ top: 0, behavior: "instant" });
}

function setGateTab(tab) {
  document.querySelectorAll(".gate-tab").forEach((b) => {
    const on = b.dataset.gateTab === tab;
    b.classList.toggle("active", on);
    b.setAttribute("aria-selected", String(on));
  });
  document.getElementById("gateSigninForm").hidden = tab !== "signin";
  document.getElementById("gateSignupForm").hidden = tab !== "signup";
  document.getElementById("signinError").textContent = "";
  document.getElementById("signupError").textContent = "";
}

async function withBusy(button, label, fn) {
  const original = button.innerHTML;
  button.disabled = true;
  button.textContent = label;
  try {
    return await fn();
  } finally {
    button.disabled = false;
    button.innerHTML = original;
  }
}

async function submitSignin(e) {
  e.preventDefault();
  const email = document.getElementById("signinEmail").value.trim();
  const password = document.getElementById("signinPassword").value;
  const errEl = document.getElementById("signinError");
  errEl.textContent = "";
  if (!email || !password) {
    errEl.textContent = "Enter your email and password.";
    return;
  }
  await withBusy(e.target.querySelector("button[type=submit]"), "Signing in...", async () => {
    try {
      const res = await api("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      document.getElementById("signinPassword").value = "";
      startSession(res.token, res.officer);
      showPage("dashboard");
      toast(res.message);
    } catch (err) {
      errEl.textContent = err.message;
    }
  });
}

async function submitSignup(e) {
  e.preventDefault();
  const val = (id) => document.getElementById(id).value.trim();
  const errEl = document.getElementById("signupError");
  errEl.textContent = "";
  const payload = {
    name: val("signupName"),
    email: val("signupEmail"),
    designation: val("signupDesignation"),
    jurisdiction: val("signupJurisdiction") || null,
    phone: val("signupPhone") || null,
    password: document.getElementById("signupPassword").value,
  };
  let problem = "";
  if (payload.name.length < 2) problem = "Enter your full name.";
  else if (!/^\S+@\S+\.\S+$/.test(payload.email)) problem = "Enter a valid email address.";
  else if (payload.password.length < 8) problem = "Password must be at least 8 characters.";
  else if (payload.password !== document.getElementById("signupConfirm").value) problem = "Passwords do not match.";
  if (problem) {
    errEl.textContent = problem;
    return;
  }
  await withBusy(e.target.querySelector("button[type=submit]"), "Creating account...", async () => {
    try {
      const res = await api("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      e.target.reset();
      startSession(res.token, res.officer);
      showPage("dashboard");
      toast(res.message);
    } catch (err) {
      errEl.textContent = err.message;
    }
  });
}

async function initSession() {
  if (!state.token) {
    // Sessions saved before password sign-in existed carry no token
    state.officer = null;
    try { localStorage.removeItem("packsure_officer"); } catch (_) {}
    renderOfficerStatus();
    showGate("auth");
    return;
  }
  hideGate();
  try {
    const officer = await api("/api/auth/me");
    state.officer = officer;
    try { localStorage.setItem("packsure_officer", JSON.stringify(officer)); } catch (_) {}
    renderOfficerStatus();
    startComplaintPolling();
  } catch (_) {
    // A 401 has already gone through endSession; on network errors keep the cached session
  }
}

document.querySelectorAll("[data-gate-tab]").forEach((el) => {
  el.addEventListener("click", (e) => {
    e.preventDefault();
    setGateTab(el.dataset.gateTab);
  });
});
document.querySelectorAll("[data-gate-view]").forEach((el) => {
  el.addEventListener("click", () => setGateView(el.dataset.gateView));
});
document.querySelectorAll("[data-pw-toggle]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const input = document.getElementById(btn.dataset.pwToggle);
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    btn.textContent = show ? "Hide" : "Show";
    btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
  });
});
document.getElementById("gateSigninForm").addEventListener("submit", submitSignin);
document.getElementById("gateSignupForm").addEventListener("submit", submitSignup);
document.querySelectorAll(".gate-demo-btn").forEach((btn) => {
  btn.addEventListener("click", () => verifyOfficerEmail(btn.dataset.officerEmail, "demo"));
});

// ==========================================
// Public Complaint (anonymous, no sign-in)
// ==========================================
const MAX_COMPLAINT_PHOTOS = 6;
let complaintPhotos = [];
let issueTypesLoaded = false;

async function loadIssueTypes() {
  if (issueTypesLoaded) return;
  const grid = document.getElementById("issueGrid");
  try {
    const types = await api("/api/public-complaints/issue-types");
    grid.innerHTML = types.map((t) => `
      <label class="issue-option">
        <input type="checkbox" name="issue" value="${escapeHtml(t.code)}" />
        <span>${escapeHtml(t.label)}</span>
      </label>
    `).join("");
    issueTypesLoaded = true;
  } catch (err) {
    grid.innerHTML = `<p class="gate-error">Could not load issue list: ${escapeHtml(err.message)}</p>`;
  }
}

// Downscale large phone photos before upload to save mobile data
async function compressImage(file) {
  if (!/^image\/(jpeg|png|webp)$/i.test(file.type) || file.size < 600 * 1024) return file;
  try {
    const bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
    const scale = Math.min(1, 1800 / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    if (bitmap.close) bitmap.close();
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.85));
    if (!blob || blob.size >= file.size) return file;
    return new File([blob], file.name.replace(/\.\w+$/, "") + ".jpg", { type: "image/jpeg" });
  } catch (_) {
    return file;
  }
}

function addComplaintPhotos(files) {
  let added = 0;
  for (const file of Array.from(files || [])) {
    if (complaintPhotos.length >= MAX_COMPLAINT_PHOTOS) {
      toast(`You can attach up to ${MAX_COMPLAINT_PHOTOS} photos.`);
      break;
    }
    const okType = /^image\/(jpeg|jpg|png|webp)$/i.test(file.type) || /\.(jpe?g|png|webp)$/i.test(file.name);
    if (!okType) {
      toast(`Skipped ${file.name}: please attach a JPG, PNG or WebP photo.`);
      continue;
    }
    const entry = { file, url: URL.createObjectURL(file), ready: null };
    entry.ready = compressImage(file).then((smaller) => { entry.file = smaller; });
    complaintPhotos.push(entry);
    added++;
  }
  renderComplaintPhotos();
  return added;
}

function renderComplaintPhotos() {
  const gallery = document.getElementById("cPhotoGallery");
  gallery.hidden = complaintPhotos.length === 0;
  gallery.innerHTML = complaintPhotos.map((p, idx) => `
    <div class="evidence-item">
      <div class="evidence-thumb-wrap">
        <img class="evidence-thumb" src="${p.url}" alt="Label photo ${idx + 1}" />
        <span class="evidence-tag">Photo ${idx + 1}</span>
        <button class="evidence-del" type="button" data-cphoto-del="${idx}" aria-label="Remove photo ${idx + 1}">&times;</button>
      </div>
    </div>
  `).join("");
  gallery.querySelectorAll("[data-cphoto-del]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const [removed] = complaintPhotos.splice(parseInt(btn.dataset.cphotoDel, 10), 1);
      if (removed) URL.revokeObjectURL(removed.url);
      renderComplaintPhotos();
    });
  });
}

function resetComplaintForm() {
  document.getElementById("complaintForm").reset();
  complaintPhotos.forEach((p) => URL.revokeObjectURL(p.url));
  complaintPhotos = [];
  renderComplaintPhotos();
  document.getElementById("complaintError").textContent = "";
}

async function submitComplaint(e) {
  e.preventDefault();
  const errEl = document.getElementById("complaintError");
  errEl.textContent = "";
  const val = (id) => document.getElementById(id).value.trim();
  const issues = [...document.querySelectorAll('#issueGrid input[name="issue"]:checked')].map((i) => i.value);

  const missing = [];
  if (!val("cProduct")) missing.push("product name");
  if (!issues.length) missing.push("at least one issue");
  if (!val("cDescription")) missing.push("description");
  if (!val("cLocation")) missing.push("location");
  if (missing.length) {
    errEl.textContent = `Please add: ${missing.join(", ")}.`;
    return;
  }

  await withBusy(document.getElementById("complaintSubmitBtn"), "Submitting...", async () => {
    await Promise.all(complaintPhotos.map((p) => p.ready));
    const form = new FormData();
    form.append("product_name", val("cProduct"));
    issues.forEach((code) => form.append("issue_types", code));
    form.append("description", val("cDescription"));
    form.append("location", val("cLocation"));
    [["brand", "cBrand"], ["barcode", "cBarcode"], ["store_name", "cStore"], ["purchase_date", "cPurchaseDate"], ["contact", "cContact"]]
      .forEach(([key, id]) => { if (val(id)) form.append(key, val(id)); });
    complaintPhotos.forEach((p) => form.append("photos", p.file, p.file.name));
    try {
      const res = await api("/api/public-complaints", { method: "POST", body: form });
      document.getElementById("successRef").textContent = res.reference_no;
      resetComplaintForm();
      setGateView("success");
    } catch (err) {
      errEl.textContent = err.message || "Could not submit complaint. Please try again.";
    }
  });
}

const COMPLAINT_STATUS_LABELS = {
  NEW: "Received, awaiting review",
  UNDER_REVIEW: "Under review by an officer",
  ACTION_TAKEN: "Action taken",
  DISMISSED: "Closed without action",
};

async function trackComplaint(e) {
  e.preventDefault();
  const ref = document.getElementById("trackRef").value.trim();
  const box = document.getElementById("trackResult");
  if (!ref) {
    box.innerHTML = `<span class="gate-error">Enter your reference number.</span>`;
    return;
  }
  box.textContent = "Checking...";
  try {
    const res = await api(`/api/public-complaints/track/${encodeURIComponent(ref)}`);
    box.innerHTML = `<strong>${escapeHtml(res.reference_no)}</strong> &middot; ${escapeHtml(res.product_name)}<br>
      Status: <span class="complaint-status s-${escapeHtml(res.status.toLowerCase())}">${escapeHtml(COMPLAINT_STATUS_LABELS[res.status] || res.status)}</span>`;
  } catch (err) {
    box.innerHTML = `<span class="gate-error">${escapeHtml(err.message)}</span>`;
  }
}

function openComplaintCamera() {
  const coarse = window.matchMedia && window.matchMedia("(pointer: coarse)").matches;
  // Phones open the native camera app; desktops/laptops use the in-page webcam modal
  if (!coarse && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    startCamera("complaint");
  } else {
    document.getElementById("cCameraInput").click();
  }
}

document.getElementById("openComplaintBtn").addEventListener("click", () => setGateView("complaint"));
document.getElementById("fileAnotherBtn").addEventListener("click", () => setGateView("complaint"));
document.getElementById("complaintForm").addEventListener("submit", submitComplaint);
document.getElementById("trackForm").addEventListener("submit", trackComplaint);
document.getElementById("cTakePhotoBtn").addEventListener("click", openComplaintCamera);
document.getElementById("cChoosePhotoBtn").addEventListener("click", () => document.getElementById("cGalleryInput").click());
["cCameraInput", "cGalleryInput"].forEach((id) => {
  document.getElementById(id).addEventListener("change", (e) => {
    addComplaintPhotos(e.target.files);
    e.target.value = "";
  });
});
document.getElementById("copyRefBtn").addEventListener("click", async () => {
  const ref = document.getElementById("successRef").textContent;
  try {
    await navigator.clipboard.writeText(ref);
    toast("Reference number copied");
  } catch (_) {
    toast(`Reference number: ${ref}`);
  }
});

// ==========================================
// Officer: Citizen Complaint Inbox & Notifications
// ==========================================
let complaintPollTimer = null;
let lastComplaintSummary = null;
const photoBlobCache = new Map();

function startComplaintPolling() {
  stopComplaintPolling();
  lastComplaintSummary = null;
  pollComplaintSummary();
  complaintPollTimer = setInterval(pollComplaintSummary, 30000);
}

function stopComplaintPolling() {
  if (complaintPollTimer) clearInterval(complaintPollTimer);
  complaintPollTimer = null;
  setComplaintBadge(0);
}

function setComplaintBadge(count) {
  const label = count > 99 ? "99+" : String(count);
  [document.getElementById("notifyCount"), document.getElementById("navComplaintCount")].forEach((el) => {
    if (!el) return;
    el.textContent = label;
    el.hidden = count === 0;
  });
  const bell = document.getElementById("notifyBell");
  if (bell) {
    bell.classList.toggle("has-new", count > 0);
    bell.setAttribute("aria-label", count ? `Citizen complaints, ${count} new` : "Citizen complaints, no new");
  }
}

async function pollComplaintSummary() {
  if (!state.token) return;
  try {
    const summary = await api("/api/public-complaints/summary");
    const prev = lastComplaintSummary;
    lastComplaintSummary = summary;
    setComplaintBadge(summary.new_count);
    if (prev && summary.latest_reference_no && summary.latest_reference_no !== prev.latest_reference_no) {
      toast(`New public complaint received: ${summary.latest_reference_no}`);
      if (document.getElementById("complaints").classList.contains("active")) loadComplaints();
    }
  } catch (_) {
    // Offline or signed out; the next poll retries
  }
}

function formatWhen(iso) {
  if (!iso) return "";
  // Backend datetimes are UTC; SQLite drops the offset
  const d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + "Z");
  return d.toLocaleString(undefined, { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

async function loadComplaintPhoto(img) {
  const url = img.dataset.src;
  const link = img.closest("a");
  if (/^https?:\/\//.test(url)) {
    img.src = url;
    link.href = url;
    return;
  }
  try {
    if (!photoBlobCache.has(url)) {
      const res = await fetch(API + url, { headers: { Authorization: `Bearer ${state.token}` } });
      if (!res.ok) throw new Error(res.statusText);
      photoBlobCache.set(url, URL.createObjectURL(await res.blob()));
    }
    img.src = photoBlobCache.get(url);
    link.href = img.src;
  } catch (_) {
    img.alt = "Photo unavailable";
  }
}

function renderComplaintCard(c) {
  const statusOptions = Object.keys(COMPLAINT_STATUS_LABELS)
    .map((s) => `<option value="${s}" ${s === c.status ? "selected" : ""}>${s.replace("_", " ")}</option>`).join("");
  const meta = [
    c.brand && `<div><span>Brand</span><b>${escapeHtml(c.brand)}</b></div>`,
    c.barcode && `<div><span>Barcode</span><b>${escapeHtml(c.barcode)}</b></div>`,
    `<div><span>Location</span><b>${escapeHtml(c.location)}</b></div>`,
    c.store_name && `<div><span>Shop</span><b>${escapeHtml(c.store_name)}</b></div>`,
    c.purchase_date && `<div><span>Purchased</span><b>${escapeHtml(c.purchase_date)}</b></div>`,
    `<div><span>Contact</span><b>${c.contact ? escapeHtml(c.contact) : "Anonymous"}</b></div>`,
  ].filter(Boolean).join("");
  const photos = c.photos.length
    ? `<div class="complaint-photos">${c.photos.map((p, i) => `
        <a href="#" target="_blank" rel="noopener" class="complaint-photo"><img data-src="${escapeHtml(p.url)}" alt="Label photo ${i + 1}" loading="lazy" /></a>`).join("")}</div>`
    : `<p class="muted" style="font-size:12.5px">No photos attached.</p>`;
  return `
    <article class="card complaint-card" data-complaint-id="${escapeHtml(c.id)}">
      <div class="complaint-head">
        <div>
          <div class="complaint-ref">${escapeHtml(c.reference_no)} &middot; ${escapeHtml(formatWhen(c.created_at))}</div>
          <h3>${escapeHtml(c.product_name)}</h3>
        </div>
        <span class="complaint-status s-${escapeHtml(c.status.toLowerCase())}">${escapeHtml(c.status.replace("_", " "))}</span>
      </div>
      <div class="complaint-issues">${c.issue_labels.map((l) => `<span class="status-tag fail">${escapeHtml(l)}</span>`).join("")}</div>
      <p class="complaint-desc">${escapeHtml(c.description)}</p>
      <div class="complaint-meta">${meta}</div>
      ${photos}
      <div class="complaint-actions">
        <div>
          <label class="field">Status</label>
          <select data-field="status">${statusOptions}</select>
        </div>
        <div class="complaint-notes">
          <label class="field">Officer notes</label>
          <textarea data-field="notes" placeholder="Action taken, inspection reference, etc.">${escapeHtml(c.officer_notes || "")}</textarea>
        </div>
        <button type="button" class="btn btn-primary" data-save-complaint>Save Update</button>
      </div>
      ${c.handled_by_badge ? `<p class="muted complaint-handled">Last updated by ${escapeHtml(c.handled_by_badge)} &middot; ${escapeHtml(formatWhen(c.updated_at))}</p>` : ""}
    </article>`;
}

async function loadComplaints() {
  const list = document.getElementById("complaintsList");
  if (!list || !state.token) return;
  const filter = document.getElementById("complaintStatusFilter").value;
  try {
    const items = await api(`/api/public-complaints?status=${encodeURIComponent(filter)}`);
    if (!items.length) {
      const label = filter === "ALL" ? "" : `${filter.replace("_", " ").toLowerCase()} `;
      list.innerHTML = `<div class="card"><p class="muted">No ${label}complaints right now.</p></div>`;
      return;
    }
    list.innerHTML = items.map(renderComplaintCard).join("");
    list.querySelectorAll(".complaint-photos img").forEach(loadComplaintPhoto);
  } catch (err) {
    list.innerHTML = `<div class="card"><p class="muted">${escapeHtml(err.message)}</p></div>`;
  }
}

document.getElementById("complaintStatusFilter").addEventListener("change", loadComplaints);
document.getElementById("refreshComplaintsBtn").addEventListener("click", () => {
  loadComplaints();
  pollComplaintSummary();
});
document.getElementById("complaintsList").addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-save-complaint]");
  if (!btn) return;
  const card = btn.closest("[data-complaint-id]");
  await withBusy(btn, "Saving...", async () => {
    try {
      await api(`/api/public-complaints/${card.dataset.complaintId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: card.querySelector('[data-field="status"]').value,
          officer_notes: card.querySelector('[data-field="notes"]').value,
        }),
      });
      toast("Complaint updated");
      pollComplaintSummary();
      loadComplaints();
    } catch (err) {
      toast(err.message);
    }
  });
});

renderDemoChips();
renderDashboard();
renderOfficerStatus();
initSession();
ping();
loadBootstrap();
setInterval(ping, 20000);

