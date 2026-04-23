const customerSelectEl = document.getElementById("customerSelect");
const showingSelectEl = document.getElementById("showingSelect");
const concessionsContainerEl = document.getElementById("concessionsContainer");
const formEl = document.getElementById("orderForm");
const ticketQtyInputEl = document.getElementById("ticketQtyInput");
const formFeedbackEl = document.getElementById("formFeedback");
const quickFormEl = document.getElementById("quickCustomerForm");
const qcName = document.getElementById("qcName");
const qcEmail = document.getElementById("qcEmail");
const qcRewards = document.getElementById("qcRewards");
const qcFeedbackEl = document.getElementById("qcFeedback");

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function renderBookingData(data) {
  customerSelectEl.innerHTML = `<option value="">Select customer</option>`;
  data.customers.forEach((c) => {
    const o = document.createElement("option");
    o.value = c.customer_id;
    o.textContent = `${c.full_name} (${c.customer_id})`;
    customerSelectEl.appendChild(o);
  });

  showingSelectEl.innerHTML = `<option value="">Select showing</option>`;
  data.showings.forEach((s) => {
    const o = document.createElement("option");
    o.value = s.showing_id;
    o.textContent = `${s.film_title} | Theatre ${s.film_theatre_number} | ${formatDate(s.film_showing_datetime)}`;
    showingSelectEl.appendChild(o);
  });

  concessionsContainerEl.innerHTML = "";
  data.concessions.forEach((item) => {
    const row = document.createElement("label");
    row.className = "concession-item";
    row.innerHTML = `
      <input type="checkbox" data-id="${item.concession_id}" />
      <span>${item.concession_name} (${item.concession_size || "—"}) — $${item.concession_price}</span>
      <input type="number" data-qty="${item.concession_id}" min="1" max="20" value="1" />
    `;
    concessionsContainerEl.appendChild(row);
  });
}

async function loadBookingData() {
  const res = await fetch("/api/booking-data");
  if (!res.ok) {
    return;
  }
  const data = await res.json();
  renderBookingData(data);
}

function collectConcessions() {
  const selected = [];
  concessionsContainerEl.querySelectorAll("input[type='checkbox']").forEach((cb) => {
    if (!cb.checked) {
      return;
    }
    const id = cb.dataset.id;
    const qtyInput = concessionsContainerEl.querySelector(`input[data-qty='${id}']`);
    const qty = Number(qtyInput?.value || 0);
    if (qty > 0) {
      selected.push({ id, qty });
    }
  });
  return selected;
}

formEl.addEventListener("submit", async (e) => {
  e.preventDefault();
  const customerId = customerSelectEl.value;
  const showingId = Number(showingSelectEl.value);
  const ticketQty = Number(ticketQtyInputEl.value);
  const concessions = collectConcessions();
  if (!customerId || !showingId || !ticketQty) {
    formFeedbackEl.textContent = "Customer, showing, and ticket quantity are required.";
    formFeedbackEl.style.color = "#fbbf24";
    return;
  }
  formFeedbackEl.textContent = "";
  const res = await fetch("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ customerId, showingId, ticketQty, concessions }),
  });
  const payload = await res.json();
  if (!res.ok) {
    formFeedbackEl.textContent = payload.error || "Order failed.";
    formFeedbackEl.style.color = "#fb7185";
    return;
  }
  formFeedbackEl.textContent = `Order #${payload.orderNumber} total: $${payload.total}`;
  formFeedbackEl.style.color = "#4ade80";
  if (payload.receiptUrl) {
    window.location.href = payload.receiptUrl;
    return;
  }
  ticketQtyInputEl.value = "1";
  concessionsContainerEl.querySelectorAll("input[type='checkbox']").forEach((el) => {
    el.checked = false;
  });
  loadBookingData();
});

quickFormEl.addEventListener("submit", async (e) => {
  e.preventDefault();
  qcFeedbackEl.textContent = "";
  const res = await fetch("/api/customers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: qcName.value,
      email: qcEmail.value,
      rewardsMember: qcRewards.checked,
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    qcFeedbackEl.textContent = data.error || "Could not add customer.";
    qcFeedbackEl.style.color = data.customerId ? "#fbbf24" : "#fb7185";
    if (data.customerId) {
      qcFeedbackEl.textContent = `${data.error} (ID: ${data.customerId})`;
    }
    return;
  }
  qcFeedbackEl.textContent = `Created ${data.customerId}.`;
  qcFeedbackEl.style.color = "#4ade80";
  qcName.value = "";
  qcEmail.value = "";
  qcRewards.checked = false;
  loadBookingData();
  customerSelectEl.value = data.customerId;
});

loadBookingData();
