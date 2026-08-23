// =========================================================================
//  Shivshakti Transport — Receipt Manager
// =========================================================================

// --- DOM refs ---
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];

const tripRows = $("#tripRows");
const errors = $("#errorContainer");
const preview = $("#documentPreview");
const clientNameInput = $("#clientName");
const clientAddressInput = $("#clientAddress");
const clientPhoneInput = $("#clientPhone");
const clientSelect = $("#clientSelect");
const clientList = $("#clientList");
const addTripButton = $("#addTripButton");
const quickFillBtn = $("#quickFillBtn");
const invoiceButton = $("#invoiceButton");
const receiptsButton = $("#receiptsButton");
const invoiceDateInput = $("#invoiceDate");
const customReceiptNumberInput = $("#customReceiptNumber");

// Set invoice date default to today
const todayStr = new Date().toISOString().slice(0, 10);
invoiceDateInput.value = todayStr;

// --- Client cache ---
let allClients = [];

// =========================================================================
//  TABS
// =========================================================================
$$(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    $$(".tab").forEach((t) => t.classList.remove("active"));
    $$(".tab-panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    $(`#panel-${tab.dataset.tab}`).classList.add("active");
    if (tab.dataset.tab === "saved") loadSavedReceipts();
    if (tab.dataset.tab === "clients") loadClients();
    if (tab.dataset.tab === "create") refreshClientList();
  });
});

// =========================================================================
//  CLIENTS
// =========================================================================
async function loadClients() {
  try {
    const res = await fetch("/api/clients");
    const data = await res.json();
    allClients = data.clients || [];
    renderClientTable();
  } catch (e) { console.error(e); }
}

function renderClientTable() {
  const body = $("#clientBody");
  if (!allClients.length) {
    body.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#667085;padding:20px">No clients yet. Add one above.</td></tr>';
    return;
  }
  body.innerHTML = allClients.map((c) => `
    <tr>
      <td>${esc(c.name)}</td>
      <td>${esc(c.address)}</td>
      <td>${esc(c.phone)}</td>
      <td>
        <button class="btn-tiny" onclick="editClient(${c.id})">Edit</button>
        <button class="btn-tiny danger" onclick="deleteClient(${c.id})">Del</button>
      </td>
    </tr>`).join("");
}

function refreshClientList() {
  fetch("/api/clients").then((r) => r.json()).then((data) => {
    allClients = data.clients || [];
    clientList.innerHTML = allClients.map((c) => `<option value="${esc(c.name)}" data-id="${c.id}">`).join("");
  });
}

clientSelect.addEventListener("input", () => {
  const match = allClients.find((c) => c.name.toLowerCase() === clientSelect.value.toLowerCase());
  if (match) {
    clientNameInput.value = match.name;
    clientAddressInput.value = match.address;
    clientPhoneInput.value = match.phone;
  }
});

// Save new client from create tab
$("#saveNewClientBtn").addEventListener("click", async () => {
  const name = clientNameInput.value.trim();
  if (!name) { showErrors(["Enter a client name first."]); return; }
  const res = await fetch("/api/clients", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, address: clientAddressInput.value.trim(), phone: clientPhoneInput.value.trim() }),
  });
  const data = await res.json();
  if (data.success) { refreshClientList(); showInfo("Client saved!"); }
  else showErrors(data.errors || ["Failed to save client."]);
});

// Client CRUD in manage tab
function editClient(id) {
  const c = allClients.find((x) => x.id === id);
  if (!c) return;
  $("#editClientId").value = id;
  $("#formClientName").value = c.name;
  $("#formClientAddress").value = c.address;
  $("#formClientPhone").value = c.phone;
  $("#clientForm").classList.remove("hidden");
}

async function deleteClient(id) {
  if (!confirm("Delete this client and all their receipts?")) return;
  await fetch(`/api/clients/${id}`, { method: "DELETE" });
  loadClients();
}

$("#addClientBtn").addEventListener("click", () => {
  $("#editClientId").value = "";
  $("#formClientName").value = "";
  $("#formClientAddress").value = "";
  $("#formClientPhone").value = "";
  $("#clientForm").classList.remove("hidden");
});

$("#cancelClientBtn").addEventListener("click", () => $("#clientForm").classList.add("hidden"));

$("#saveClientBtn").addEventListener("click", async () => {
  const id = $("#editClientId").value;
  const payload = {
    name: $("#formClientName").value.trim(),
    address: $("#formClientAddress").value.trim(),
    phone: $("#formClientPhone").value.trim(),
  };
  if (!payload.name) { alert("Name required"); return; }
  if (id) {
    await fetch(`/api/clients/${id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  } else {
    await fetch("/api/clients", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  }
  $("#clientForm").classList.add("hidden");
  loadClients();
  refreshClientList();
});

// =========================================================================
//  TRIP ROWS
// =========================================================================
function addTripRow(prefill) {
  const row = document.createElement("div");
  row.className = "trip-row";
  const v = (field) => (prefill && prefill[field]) || "";
  row.innerHTML = `
    <input placeholder="MH 12 AB 1234" aria-label="Truck number" data-field="truckNo" value="${esc(v("truckNo"))}">
    <input placeholder="From" aria-label="From location" data-field="from" value="${esc(v("from"))}">
    <input placeholder="To" aria-label="To location" data-field="to" value="${esc(v("to"))}">
    <input type="number" min="1" step="1" placeholder="1" aria-label="Number of trips" data-field="trips">
    <input type="number" min="0" step="0.01" placeholder="0.00" aria-label="Rate per trip" data-field="rate">
    <input type="date" aria-label="Trip date" data-field="tripDate" value="${esc(v("tripDate") || todayStr)}">
    <button type="button" class="remove-row" aria-label="Remove this row">×</button>`;
  row.querySelector("button").addEventListener("click", () => row.remove());
  tripRows.appendChild(row);
  return row;
}

addTripButton.addEventListener("click", () => addTripRow());

// Quick fill: copy truck, from, to from last row
quickFillBtn.addEventListener("click", () => {
  const rows = [...tripRows.children];
  if (!rows.length) return;
  const last = rows[rows.length - 1];
  const val = (f) => last.querySelector(`[data-field="${f}"]`).value;
  addTripRow({ truckNo: val("truckNo"), from: val("from"), to: val("to") });
});

function collectTrips() {
  return [...tripRows.children].map((row) => {
    const v = (f) => row.querySelector(`[data-field="${f}"]`).value;
    return { truckNo: v("truckNo"), from: v("from"), to: v("to"), trips: v("trips"), rate: v("rate"), tripDate: v("tripDate") };
  });
}

// =========================================================================
//  GENERATE (same as before, but now saves to DB)
// =========================================================================
function showErrors(items) {
  errors.innerHTML = items.map((i) => `<div>${i}</div>`).join("");
  errors.classList.remove("hidden");
  errors.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function showInfo(msg) {
  errors.innerHTML = `<div style="color:#067647;background:#ecfdf3;border-color:#d1fadf">${msg}</div>`;
  errors.classList.remove("hidden");
}

async function generate(endpoint, button) {
  errors.classList.add("hidden");
  const orig = button.textContent;
  button.disabled = true;
  button.textContent = "Generating…";
  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ clientName: clientNameInput.value, clientAddress: clientAddressInput.value, invoiceDate: invoiceDateInput.value, receiptNumber: customReceiptNumberInput.value.trim(), trips: collectTrips() }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      showErrors(data.errors || ["Could not generate."]);
    } else {
      preview.innerHTML = data.html;
      preview.classList.remove("hidden");
      preview.scrollIntoView({ behavior: "smooth", block: "start" });
      const count = data.receipt_ids ? data.receipt_ids.length : (data.count || 0);
      showInfo(`✅ ${count} receipt${count !== 1 ? "s" : ""} saved to database. Go to "Saved Receipts" tab to print.`);
    }
  } catch (e) {
    showErrors(["Could not connect to the server."]);
  } finally {
    button.disabled = false;
    button.textContent = orig;
  }
}

invoiceButton.addEventListener("click", (e) => generate("/generate_invoice", e.currentTarget));
receiptsButton.addEventListener("click", (e) => generate("/generate_receipts", e.currentTarget));

// =========================================================================
//  SAVED RECEIPTS
// =========================================================================
let allReceipts = [];
let selectedIds = new Set();

async function loadSavedReceipts() {
  const clientId = $("#filterClient").value;
  let url = "/api/receipts";
  if (clientId) url += `?client_id=${clientId}`;
  try {
    const res = await fetch(url);
    const data = await res.json();
    allReceipts = data.receipts || [];
    renderBatches();
    renderReceiptTable();
    populateClientFilter();
  } catch (e) { console.error(e); }
}

function populateClientFilter() {
  const sel = $("#filterClient");
  const current = sel.value;
  // collect unique clients from receipts
  const clientMap = {};
  allReceipts.forEach((r) => { if (r.client) clientMap[r.client.id] = r.client.name; });
  sel.innerHTML = '<option value="">All clients</option>' +
    Object.entries(clientMap).map(([id, name]) => `<option value="${id}" ${id === current ? "selected" : ""}>${esc(name)}</option>`).join("");
}

$("#filterClient").addEventListener("change", loadSavedReceipts);
$("#refreshReceiptsBtn").addEventListener("click", loadSavedReceipts);

function renderBatches() {
  const wrap = $("#batchList");
  // Group receipts by batch_id
  const batches = {};
  allReceipts.forEach((r) => {
    if (!batches[r.batch_id]) batches[r.batch_id] = { batch_id: r.batch_id, receipts: [], total: 0, client: r.client };
    batches[r.batch_id].receipts.push(r);
    batches[r.batch_id].total += r.total;
  });
  const entries = Object.values(batches);
  if (!entries.length) {
    wrap.innerHTML = '<div class="empty-state">No saved receipts yet. Create some in the "Create" tab.</div>';
    return;
  }
  wrap.innerHTML = entries.map((b) => `
    <div class="batch-card">
      <div class="batch-info">
        <strong>Batch ${esc(b.batch_id)}</strong>
        <span>${b.receipts.length} receipt${b.receipts.length > 1 ? "s" : ""}</span>
        <span>₹${b.total.toFixed(2)}</span>
        <span>${b.client ? esc(b.client.name) : ""}</span>
      </div>
      <div class="batch-actions-inline">
        <button class="btn-tiny" onclick="printBatch('${b.batch_id}')">Print</button>
        <button class="btn-tiny danger" onclick="deleteBatch('${b.batch_id}')">Delete</button>
      </div>
    </div>`).join("");
}

function renderReceiptTable() {
  const wrap = $("#receiptTableWrap");
  const body = $("#receiptBody");
  if (!allReceipts.length) {
    wrap.classList.add("hidden");
    return;
  }
  wrap.classList.remove("hidden");
  selectedIds.clear();
  body.innerHTML = allReceipts.map((r) => `
    <tr>
      <td><input type="checkbox" class="receipt-check" value="${r.id}"></td>
      <td>${esc(r.receipt_number)}</td>
      <td>${r.client ? esc(r.client.name) : ""}</td>
      <td>${esc(r.truck_no)}</td>
      <td>${esc(r.from_loc)} → ${esc(r.to_loc)}</td>
      <td>${r.num_trips}</td>
      <td>₹${r.total.toFixed(2)}</td>
      <td>${r.invoice_date}</td>
      <td>${r.trip_date}</td>
      <td><button class="btn-tiny" onclick="editReceipt(${r.id})">Edit</button> <button class="btn-tiny danger" onclick="deleteReceipt(${r.id})">×</button></td>
    </tr>`).join("");
}

// Select all
$("#selectAll").addEventListener("change", (e) => {
  $$(".receipt-check").forEach((cb) => {
    cb.checked = e.target.checked;
    if (e.target.checked) selectedIds.add(Number(cb.value));
    else selectedIds.delete(Number(cb.value));
  });
  updateBatchBtns();
});

// Delegate checkbox clicks
$("#receiptBody").addEventListener("change", (e) => {
  if (e.target.classList.contains("receipt-check")) {
    const id = Number(e.target.value);
    if (e.target.checked) selectedIds.add(id); else selectedIds.delete(id);
    updateBatchBtns();
  }
});

function updateBatchBtns() {
  const has = selectedIds.size > 0;
  $("#printSelectedBtn").disabled = !has;
  $("#deleteSelectedBtn").disabled = !has;
}

function editReceipt(id) {
  const r = allReceipts.find((x) => x.id === id);
  if (!r) return;
  $("#editReceiptId").value = id;
  $("#editTruckNo").value = r.truck_no;
  $("#editFrom").value = r.from_loc;
  $("#editTo").value = r.to_loc;
  $("#editTrips").value = r.num_trips;
  $("#editRate").value = r.rate_per_trip;
  $("#editTripDate").value = r.trip_date;
  $("#editInvoiceDate").value = r.invoice_date;
  $("#editReceiptForm").classList.remove("hidden");
  $("#editReceiptForm").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

$("#cancelEditBtn").addEventListener("click", () => $("#editReceiptForm").classList.add("hidden"));

$("#saveEditBtn").addEventListener("click", async () => {
  const id = $("#editReceiptId").value;
  const payload = {
    truck_no: $("#editTruckNo").value.trim(),
    from_loc: $("#editFrom").value.trim(),
    to_loc: $("#editTo").value.trim(),
    num_trips: parseInt($("#editTrips").value) || 1,
    rate_per_trip: parseFloat($("#editRate").value) || 0,
    trip_date: $("#editTripDate").value,
    invoice_date: $("#editInvoiceDate").value,
  };
  await fetch(`/api/receipts/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  $("#editReceiptForm").classList.add("hidden");
  loadSavedReceipts();
});

async function deleteReceipt(id) {
  if (!confirm("Delete this receipt?")) return;
  await fetch(`/api/receipts/${id}`, { method: "DELETE" });
  loadSavedReceipts();
}

async function deleteBatch(batchId) {
  if (!confirm("Delete entire batch?")) return;
  await fetch(`/api/receipts/batch/${batchId}`, { method: "DELETE" });
  loadSavedReceipts();
}

function printBatch(batchId) {
  const mode = $("#printModeToggle").checked ? "single" : "multi";
  const override = $("#printReceiptOverride") ? $("#printReceiptOverride").value.trim() : "";
  localStorage.setItem("printMode", mode);
  if (override) localStorage.setItem("printReceiptOverride", override);
  else localStorage.removeItem("printReceiptOverride");
  window.open(`/print_batch_page/${batchId}`, "_blank");
}

$("#printSelectedBtn").addEventListener("click", () => {
  if (!selectedIds.size) return;
  const mode = $("#printModeToggle").checked ? "single" : "multi";
  localStorage.setItem("printReceiptIds", JSON.stringify([...selectedIds]));
  localStorage.setItem("printMode", mode);
  const override = $("#printReceiptOverride") ? $("#printReceiptOverride").value.trim() : "";
  if (override) localStorage.setItem("printReceiptOverride", override);
  else localStorage.removeItem("printReceiptOverride");
  window.open("/print_batch_page/multi", "_blank");
});

$("#deleteSelectedBtn").addEventListener("click", async () => {
  if (!selectedIds.size) return;
  if (!confirm(`Delete ${selectedIds.size} receipt(s)?`)) return;
  for (const id of selectedIds) {
    await fetch(`/api/receipts/${id}`, { method: "DELETE" });
  }
  loadSavedReceipts();
});

// =========================================================================
//  HELPERS
// =========================================================================
function esc(s) {
  const div = document.createElement("div");
  div.textContent = s || "";
  return div.innerHTML;
}

// =========================================================================
//  INIT
// =========================================================================
refreshClientList();
addTripRow();
