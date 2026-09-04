const API = "";
const DEMO_BARCODES = [
  ["8901234567890", "DemoBakes biscuits"],
  ["8909876543210", "Sunflower oil"],
  ["8901122334455", "Herbal soap"],
  ["8905544332211", "Garam masala"],
  ["8907788990011", "Wheat atta"],
  ["8906677889900", "Instant coffee"],
  ["8904433221100", "Almonds"],
  ["8903322110099", "Fruit juice"],
];

const state = {
  scanId: null,
  product: null,
  analysis: null,
  fields: [],
  history: JSON.parse(localStorage.getItem("packsure_history") || "[]"),
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
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  document.getElementById(id).classList.add("active");
  document.querySelectorAll("nav button").forEach((b) => {
    b.classList.toggle("active", b.dataset.page === id);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

document.querySelectorAll("[data-page]").forEach((el) => {
  el.addEventListener("click", (e) => {
    e.preventDefault();
    showPage(el.dataset.page);
  });
});

function saveHistory() {
  localStorage.setItem("packsure_history", JSON.stringify(state.history.slice(0, 20)));
  renderDashboard();
}

function pill(status) {
  const map = {
    PASS: ["pass", "PASS"],
    POTENTIAL_NON_COMPLIANCE: ["fail", "FLAG"],
    POTENTIAL_DISCREPANCY: ["fail", "FLAG"],
    NEEDS_REVIEW: ["review", "REVIEW"],
    NOT_APPLICABLE: ["na", "N/A"],
    INFO: ["na", "INFO"],
  };
  const [cls, label] = map[status] || ["na", status || "—"];
  return `<span class="status-pill ${cls}">${label}</span>`;
}

function renderDashboard() {
  document.getElementById("statScans").textContent = String(state.history.length);
  const last = state.history[0];
  document.getElementById("statLast").textContent = last && last.score != null ? `${Math.round(last.score)}%` : "—";
  const list = document.getElementById("recentList");
  if (!state.history.length) {
    list.innerHTML = `<p class="muted">No inspections yet.</p>`;
    return;
  }
  list.innerHTML = state.history.slice(0, 6).map((h) => `
    <div class="list-item">
      <div>
        <div>${h.name || h.barcode || "Unlisted pack"}</div>
        <div class="muted">${h.id.slice(0, 8)} · ${h.status || ""}</div>
      </div>
      <div>${h.score != null ? Math.round(h.score) + "%" : "—"}</div>
    </div>
  `).join("");
}

function renderDemoChips() {
  document.getElementById("demoChips").innerHTML = DEMO_BARCODES.map(
    ([code, name]) => `<button class="chip" data-code="${code}">${name} · ${code}</button>`
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
    dot.querySelector("span").textContent = h.status === "ok" ? "API online" : "API";
  } catch {
    dot.className = "health-dot bad";
    dot.querySelector("span").textContent = "API offline";
  }
}

async function loadBootstrap() {
  try {
    const [products, rules] = await Promise.all([
      api("/api/products/"),
      api("/api/compliance/rules"),
    ]);
    document.getElementById("statProducts").textContent = String(products.length);
    document.getElementById("statRules").textContent = String(rules.total_rules);
    document.getElementById("catalogGrid").innerHTML = products.map((p) => `
      <div class="card">
        <h2>${p.name}</h2>
        <p class="muted">${p.brand} · ${p.category || ""}</p>
        <div class="list-item"><span>Barcode</span><b>${p.barcode}</b></div>
        <div class="list-item"><span>Net qty</span><b>${p.expected_net_quantity}</b></div>
        <div class="list-item"><span>MRP</span><b>${p.expected_mrp}</b></div>
        <button class="btn btn-cyan" style="margin-top:10px" data-use="${p.barcode}">Use barcode</button>
      </div>
    `).join("");
    document.querySelectorAll("[data-use]").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.getElementById("barcode").value = btn.dataset.use;
        showPage("inspect");
        lookup();
      });
    });
    document.getElementById("rulesCards").innerHTML = rules.rules.map((r) => `
      <div class="card">
        <h2>${r.id} · ${r.name}</h2>
        <p class="muted">${r.rule_number} · ${r.severity} · ${r.mandatory ? "Mandatory" : "Optional"}</p>
        <p class="muted" style="margin-top:8px">${r.description}</p>
        <p class="muted" style="margin-top:8px">${r.legal_reference || ""}</p>
      </div>
    `).join("");
  } catch (err) {
    toast(err.message);
  }
}

async function lookup() {
  const barcode = document.getElementById("barcode").value.trim();
  const box = document.getElementById("lookupBox");
  if (!barcode) {
    box.textContent = "Enter a barcode first.";
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
      box.innerHTML = `<strong>${p.name}</strong> · ${p.brand}<br>Expected ${p.expected_net_quantity} · ${p.expected_mrp}`;
    } else {
      box.textContent = "Not in catalog. You can still inspect the pack label.";
    }
  } catch (err) {
    box.textContent = err.message;
  }
}

function sessionPayload() {
  return {
    barcode: document.getElementById("barcode").value.trim() || null,
    officer_id: document.getElementById("officerId").value.trim() || null,
    establishment_name: document.getElementById("establishment").value.trim() || null,
    inspection_location: document.getElementById("location").value.trim() || null,
    notes: document.getElementById("notes").value.trim() || null,
  };
}

function setSession(created) {
  state.scanId = created.scan_id || created.inspection_id;
  document.getElementById("sessionMeta").textContent = `Session ${state.scanId} · ${created.status}`;
}

async function ensureSession() {
  if (state.scanId) return state.scanId;
  const created = await api("/api/scans/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(sessionPayload()),
  });
  setSession(created);
  return state.scanId;
}

async function createSession() {
  try {
    const created = await api("/api/scans/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sessionPayload()),
    });
    setSession(created);
    toast("Inspection created");
  } catch (err) {
    toast(err.message);
  }
}

function setChosenFile(file) {
  if (!file) return false;
  const okType = /^image\/(jpeg|jpg|png|webp)$/i.test(file.type) || /\.(jpe?g|png|webp)$/i.test(file.name);
  if (!okType) {
    toast("Use a JPG, PNG, or WebP of the pack label.");
    return false;
  }
  const input = document.getElementById("fileInput");
  if (input.files[0] !== file) {
    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
  }
  const img = document.getElementById("preview");
  img.src = URL.createObjectURL(file);
  img.style.display = "block";
  return true;
}

const fileInput = document.getElementById("fileInput");
fileInput.addEventListener("change", (e) => setChosenFile(e.target.files[0]));
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
  setChosenFile(e.dataTransfer.files[0]);
});

function statusClass(score, risk) {
  if (risk === "HIGH" || (score != null && score < 60)) return "fail";
  if (risk === "MEDIUM") return "review";
  return "pass";
}

async function analyze() {
  const file = document.getElementById("fileInput").files[0];
  if (!file) {
    toast("Choose a label photograph.");
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
    const form = new FormData();
    form.append("file", file);
    const loc = document.getElementById("location").value.trim();
    if (loc) form.append("user_location", loc);
    await api(`/api/scans/${scanId}/images`, { method: "POST", body: form });
    const analysis = await api(`/api/scans/${scanId}/analyze`, { method: "POST" });
    state.analysis = analysis;
    try {
      const fields = await api(`/api/scans/${state.scanId}/extract-fields`, { method: "POST" });
      state.fields = fields.fields || [];
    } catch {
      state.fields = [];
    }
    const name = state.product?.name || document.getElementById("barcode").value.trim() || "Pack";
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
    toast("Screening complete");
  } catch (err) {
    toast(err.message);
  } finally {
    busy.style.display = "none";
    btn.disabled = false;
  }
}

function renderResults() {
  const a = state.analysis;
  if (!a) return;
  document.getElementById("resultLede").textContent = `Inspection ${a.inspection_id || a.scan_id}`;
  const score = Math.round(a.overall_score ?? 0);
  document.getElementById("scoreValue").textContent = `${score}%`;
  document.getElementById("scoreRing").style.setProperty("--p", String(score));
  document.getElementById("riskTitle").textContent = `${a.risk_level || "PENDING"} risk`;
  document.getElementById("summaryText").textContent = a.summary || "";
  document.getElementById("reportBtn").disabled = false;
  document.getElementById("reviewBtn").disabled = false;
  document.getElementById("pdfLink").style.display = "none";

  const rules = a.rules_summary || [];
  document.getElementById("rulesTable").innerHTML = rules.length
    ? `<table><thead><tr><th>Rule</th><th>Status</th><th>Reason</th></tr></thead><tbody>${
        rules.map((r) => `<tr><td>${r.rule_id}<br><span class="muted">${r.name || ""}</span></td><td>${pill(r.status)}</td><td>${r.reason || ""}</td></tr>`).join("")
      }</tbody></table>`
    : "No rule rows returned.";

  const discs = a.discrepancies || [];
  document.getElementById("discList").innerHTML = discs.length
    ? discs.map((d) => `
        <div class="list-item">
          <div>
            <div>${d.field}</div>
            <div class="muted">${d.difference_summary || ""}</div>
            <div class="muted">Catalog: ${d.catalog_value || "—"} · Pack: ${d.detected_value || "—"}</div>
          </div>
          ${pill(d.status)}
        </div>`).join("")
    : "No catalog discrepancies flagged.";

  const labels = {
    product_name: "Product name",
    net_quantity: "Net quantity",
    mrp: "MRP",
    unit_sale_price: "Unit sale price",
    manufacturer_name_and_address: "Manufacturer",
    consumer_care: "Consumer care",
    manufacture_or_import_date: "Date",
    dimensions: "Dimensions",
  };
  document.getElementById("fieldsGrid").innerHTML = (state.fields || []).map((f) => `
    <div class="card">
      <div class="muted">${labels[f.field_name] || f.field_name}</div>
      <div style="margin-top:6px;font-weight:700">${f.value}</div>
      <div class="muted">${Math.round((f.confidence || 0) * 100)}% confidence</div>
    </div>
  `).join("") || `<p class="muted">No fields extracted. OCR may have found little text on this image.</p>`;
}

async function generateReport() {
  if (!state.scanId) return;
  try {
    const report = await api(`/api/scans/${state.scanId}/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        officer_notes: document.getElementById("notes").value.trim() || null,
        authority_name: "PackSure · Legal Metrology screening",
        authority_jurisdiction: document.getElementById("location").value.trim() || "Demo jurisdiction",
      }),
    });
    const link = document.getElementById("pdfLink");
    link.href = API + (report.pdf_download_url || `/api/scans/${state.scanId}/report/pdf`);
    link.style.display = "inline-flex";
    toast(`Report ${report.report_number} ready`);
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
    toast("Officer review recorded");
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
  bot.textContent = "Thinking…";
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
    bot.textContent = err.message || "Chat request failed.";
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

renderDemoChips();
renderDashboard();
ping();
loadBootstrap();
setInterval(ping, 20000);
