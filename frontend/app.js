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
};

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.style.display = "block";
  setTimeout(() => { el.style.display = "none"; }, 4200);
}

async function api(path, opts = {}) {
  const res = await fetch(API + path, opts);
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
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  const target = document.getElementById(id);
  if (target) {
    target.classList.add("active");
  }
  document.querySelectorAll("nav button").forEach((b) => {
    b.classList.toggle("active", b.dataset.page === id);
  });
  if (PAGE_TITLES[id]) {
    document.title = `PackSure | ${PAGE_TITLES[id]}`;
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

  const panelLabels = ["Front PDP", "Back Declarations", "Side / MRP Panel", "Barcode / Batch Panel", "Supplementary Panel"];

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

  const labels = {
    product_name: "Product Designation",
    net_quantity: "Net Quantity",
    mrp: "Maximum Retail Price (MRP)",
    unit_sale_price: "Unit Sale Price (USP)",
    manufacturer_name_and_address: "Manufacturer / Packer Details",
    consumer_care: "Consumer Care Coordinates",
    manufacture_or_import_date: "Date of Manufacture / Import",
    dimensions: "Package Dimensions",
  };
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
      </div>
    `;
  }).join("") || `<p class="muted">No declarations extracted. Ensure the label photograph is sharp and well lit.</p>`;
}

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

  if (cameraMode === "label") {
    title.textContent = "Capture Package Label Photo (Multiple Panels)";
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

    if (cameraMode === "label") {
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
  if (cameraMode === "label") {
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
  const headerArea = document.getElementById("headerOfficerArea");
  const bannerContainer = document.getElementById("officerInspectBannerContainer");
  const officerInput = document.getElementById("officerId");

  const loginActiveCard = document.getElementById("loginActiveOfficerCard");
  const loginFormCard = document.getElementById("loginFormCard");
  const loginActiveName = document.getElementById("loginActiveName");
  const loginActiveBadge = document.getElementById("loginActiveBadge");
  const loginActiveJurisdiction = document.getElementById("loginActiveJurisdiction");
  const loginActiveProvider = document.getElementById("loginActiveProvider");

  if (state.officer) {
    // Masthead Topbar
    if (topContainer) {
      topContainer.innerHTML = `
        <span class="officer-topbar-active">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
          Officer: ${escapeHtml(state.officer.name)} (${escapeHtml(state.officer.officer_badge)})
        </span>
        <button type="button" class="officer-logout-btn" id="topbarLogoutBtn" title="Sign out of official terminal">Sign Out</button>
      `;
      const outBtn = document.getElementById("topbarLogoutBtn");
      if (outBtn) outBtn.addEventListener("click", logoutOfficer);
    }

    // Main Header Officer Area
    if (headerArea) {
      headerArea.innerHTML = `
        <div class="header-officer-pill">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
          <span class="officer-name">${escapeHtml(state.officer.name)}</span>
          <span class="officer-badge-tag">${escapeHtml(state.officer.officer_badge)}</span>
          <button type="button" class="btn-officer-logout" id="headerLogoutBtn" title="Logout of Officer Account">Logout</button>
        </div>
      `;
      const hLogout = document.getElementById("headerLogoutBtn");
      if (hLogout) hLogout.addEventListener("click", logoutOfficer);
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
    // Masthead Topbar
    if (topContainer) {
      topContainer.innerHTML = `
        <button type="button" class="officer-topbar-btn" id="openOfficerAuthBtn" title="Official Government Access">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
          Officer Sign In
        </button>
      `;
      const inBtn = document.getElementById("openOfficerAuthBtn");
      if (inBtn) inBtn.addEventListener("click", openOfficerModal);
    }

    // Main Header Officer Area
    if (headerArea) {
      headerArea.innerHTML = `
        <button type="button" class="btn-header-login" id="headerLoginBtn" data-page="login">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          Officer Login
        </button>
      `;
      const hLogin = document.getElementById("headerLoginBtn");
      if (hLogin) {
        hLogin.addEventListener("click", () => showPage("login"));
      }
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
}

function closeOfficerModal() {
  const modal = document.getElementById("officerAuthModal");
  if (modal) modal.style.display = "none";
}

function logoutOfficer() {
  state.officer = null;
  localStorage.removeItem("packsure_officer");
  renderOfficerStatus();
  toast("Officer session ended. Logged out successfully.");
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
      state.officer = res.officer;
      localStorage.setItem("packsure_officer", JSON.stringify(res.officer));
      renderOfficerStatus();
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

renderDemoChips();
renderDashboard();
renderOfficerStatus();
ping();
loadBootstrap();
setInterval(ping, 20000);

