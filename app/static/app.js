const totalFilmsEl = document.getElementById("totalFilms");
const activeShowingsEl = document.getElementById("activeShowings");
const openTheatresEl = document.getElementById("openTheatres");
const totalRevenueEl = document.getElementById("totalRevenue");
const customerSelectEl = document.getElementById("customerSelect");
const showingSelectEl = document.getElementById("showingSelect");
const showingsContainerEl = document.getElementById("showingsContainer");
const ordersBodyEl = document.getElementById("ordersBody");
const concessionsContainerEl = document.getElementById("concessionsContainer");
const formEl = document.getElementById("orderForm");
const ticketQtyInputEl = document.getElementById("ticketQtyInput");
const feedbackEl = document.getElementById("formFeedback");
const datasetSelectEl = document.getElementById("datasetSelect");
const datasetHeadEl = document.getElementById("datasetHead");
const datasetBodyEl = document.getElementById("datasetBody");

let adminData = {};

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function renderStats(summary) {
  totalFilmsEl.textContent = summary.total_films ?? 0;
  activeShowingsEl.textContent = summary.active_showings ?? 0;
  openTheatresEl.textContent = summary.open_theatres ?? 0;
  totalRevenueEl.textContent = `$${summary.total_revenue ?? 0}`;
}

function renderShowings(showings) {
  showingsContainerEl.innerHTML = "";
  showingSelectEl.innerHTML = `<option value="">Select showing</option>`;

  showings.forEach((showing) => {
    const card = document.createElement("article");
    card.className = "showing-card";
    card.innerHTML = `
      <h4>${showing.film_title}</h4>
      <p>Theatre ${showing.film_theatre_number} | ${formatDate(showing.film_showing_datetime)}</p>
      <p>Available seats: ${showing.film_available_seats}</p>
    `;
    showingsContainerEl.appendChild(card);

    const option = document.createElement("option");
    option.value = showing.showing_id;
    option.textContent = `${showing.film_title} | Theatre ${showing.film_theatre_number} | ${formatDate(showing.film_showing_datetime)}`;
    showingSelectEl.appendChild(option);
  });
}

function renderOrders(orders) {
  ordersBodyEl.innerHTML = "";
  orders.forEach((order) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${order.order_number}</td>
      <td>${order.customer_name}</td>
      <td>${order.ticket_count}</td>
      <td>$${order.order_total}</td>
      <td>${formatDate(order.created_at)}</td>
    `;
    ordersBodyEl.appendChild(row);
  });
}

function renderBookingData(data) {
  customerSelectEl.innerHTML = `<option value="">Select customer</option>`;
  data.customers.forEach((customer) => {
    const option = document.createElement("option");
    option.value = customer.customer_id;
    option.textContent = `${customer.full_name} (${customer.customer_id})`;
    customerSelectEl.appendChild(option);
  });

  concessionsContainerEl.innerHTML = "";
  data.concessions.forEach((item) => {
    const row = document.createElement("label");
    row.className = "concession-item";
    row.innerHTML = `
      <input type="checkbox" data-id="${item.concession_id}" />
      <span>${item.concession_name} (${item.concession_size}) - $${item.concession_price}</span>
      <input type="number" data-qty="${item.concession_id}" min="1" max="20" value="1" />
    `;
    concessionsContainerEl.appendChild(row);
  });
}

async function loadDashboard() {
  try {
    const res = await fetch("/api/dashboard");
    const data = await res.json();
    renderStats(data.summary);
    renderShowings(data.showings);
    renderOrders(data.recentOrders);
  } catch (error) {
    feedbackEl.textContent = "Unable to load dashboard data.";
    feedbackEl.style.color = "#fb7185";
  }
}

async function loadBookingData() {
  try {
    const res = await fetch("/api/booking-data");
    const data = await res.json();
    renderBookingData(data);
  } catch (error) {
    feedbackEl.textContent = "Unable to load booking data.";
    feedbackEl.style.color = "#fb7185";
  }
}

function renderDatasetTable(datasetName) {
  const rows = adminData[datasetName] || [];
  datasetHeadEl.innerHTML = "";
  datasetBodyEl.innerHTML = "";

  if (!rows.length) {
    datasetHeadEl.innerHTML = "<tr><th>No data</th></tr>";
    datasetBodyEl.innerHTML = "<tr><td>Nothing found for this dataset.</td></tr>";
    return;
  }

  const columns = Object.keys(rows[0]);
  const headRow = document.createElement("tr");
  columns.forEach((column) => {
    const th = document.createElement("th");
    th.textContent = column;
    headRow.appendChild(th);
  });
  datasetHeadEl.appendChild(headRow);

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    columns.forEach((column) => {
      const td = document.createElement("td");
      const value = row[column];
      td.textContent = typeof value === "string" && value.includes("T") ? formatDate(value) : value ?? "-";
      tr.appendChild(td);
    });
    datasetBodyEl.appendChild(tr);
  });
}

async function loadAdminData() {
  try {
    const res = await fetch("/api/admin-overview");
    adminData = await res.json();
    renderDatasetTable(datasetSelectEl.value);
  } catch (error) {
    feedbackEl.textContent = "Unable to load admin overview data.";
    feedbackEl.style.color = "#fb7185";
  }
}

function collectConcessions() {
  const selected = [];
  const checkboxes = concessionsContainerEl.querySelectorAll("input[type='checkbox']");
  checkboxes.forEach((checkbox) => {
    if (!checkbox.checked) {
      return;
    }
    const id = checkbox.dataset.id;
    const qtyInput = concessionsContainerEl.querySelector(`input[data-qty='${id}']`);
    const qty = Number(qtyInput?.value || 0);
    if (qty > 0) {
      selected.push({ id, qty });
    }
  });
  return selected;
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();

  const customerId = customerSelectEl.value;
  const showingId = Number(showingSelectEl.value);
  const ticketQty = Number(ticketQtyInputEl.value);
  const concessions = collectConcessions();

  if (!customerId || !showingId || !ticketQty) {
    feedbackEl.textContent = "Customer, showing, and ticket quantity are required.";
    feedbackEl.style.color = "#fbbf24";
    return;
  }

  try {
    const res = await fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ customerId, showingId, ticketQty, concessions }),
    });

    const payload = await res.json();
    if (!res.ok) {
      throw new Error(payload.error || "Failed to create order.");
    }

    feedbackEl.textContent = `Order #${payload.orderNumber} created. Total: $${payload.orderTotal}`;
    feedbackEl.style.color = "#4ade80";
    ticketQtyInputEl.value = "1";
    concessionsContainerEl.querySelectorAll("input[type='checkbox']").forEach((el) => {
      el.checked = false;
    });
    await loadDashboard();
    await loadBookingData();
    await loadAdminData();
  } catch (error) {
    feedbackEl.textContent = error.message;
    feedbackEl.style.color = "#fb7185";
  }
});

datasetSelectEl.addEventListener("change", () => {
  renderDatasetTable(datasetSelectEl.value);
});

loadDashboard();
loadBookingData();
loadAdminData();
