const datasetSelectEl = document.getElementById("datasetSelect");
const datasetHeadEl = document.getElementById("datasetHead");
const datasetBodyEl = document.getElementById("datasetBody");
const feedbackEl = document.getElementById("datasetFeedback");

let adminData = {};

function formatDate(value) {
  if (value == null || value === "") {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function formatCellValue(value) {
  if (value == null) {
    return "—";
  }
  if (typeof value === "string" && value.match(/^\d{4}-\d{2}-\d{2}T/)) {
    return formatDate(value);
  }
  if (typeof value === "string" && value.match(/^\d{4}-\d{2}-\d{2} /)) {
    return formatDate(value);
  }
  if (typeof value === "string" && value.includes("T") && value.length >= 19) {
    return formatDate(value);
  }
  return value;
}

function renderDatasetTable(datasetName) {
  const rows = adminData[datasetName] || [];
  datasetHeadEl.innerHTML = "";
  datasetBodyEl.innerHTML = "";
  if (!rows.length) {
    datasetHeadEl.innerHTML = "<tr><th>No data</th></tr>";
    datasetBodyEl.innerHTML = "<tr><td>No rows.</td></tr>";
    return;
  }
  const columns = Object.keys(rows[0]);
  const headRow = document.createElement("tr");
  columns.forEach((col) => {
    const th = document.createElement("th");
    th.textContent = col;
    headRow.appendChild(th);
  });
  datasetHeadEl.appendChild(headRow);
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    columns.forEach((col) => {
      const td = document.createElement("td");
      td.textContent = formatCellValue(row[col]);
      tr.appendChild(td);
    });
    datasetBodyEl.appendChild(tr);
  });
}

async function loadAdminData() {
  feedbackEl.textContent = "";
  const res = await fetch("/api/admin-overview");
  if (!res.ok) {
    feedbackEl.textContent = "Failed to load data.";
    return;
  }
  adminData = await res.json();
  renderDatasetTable(datasetSelectEl.value);
}

datasetSelectEl.addEventListener("change", () => {
  renderDatasetTable(datasetSelectEl.value);
});

loadAdminData();
