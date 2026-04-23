const totalFilmsEl = document.getElementById("totalFilms");
const activeShowingsEl = document.getElementById("activeShowings");
const openTheatresEl = document.getElementById("openTheatres");
const totalRevenueEl = document.getElementById("totalRevenue");
const showingsContainerEl = document.getElementById("showingsContainer");
const ordersBodyEl = document.getElementById("ordersBody");

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
  showings.forEach((showing) => {
    const card = document.createElement("article");
    card.className = "showing-card";
    card.innerHTML = `
      <h4>${showing.film_title}</h4>
      <p>Theatre ${showing.film_theatre_number} | ${formatDate(showing.film_showing_datetime)}</p>
      <p>Available seats: ${showing.film_available_seats}</p>
    `;
    showingsContainerEl.appendChild(card);
  });
}

function renderOrders(orders) {
  ordersBodyEl.innerHTML = "";
  orders.forEach((order) => {
    const row = document.createElement("tr");
    const total = order.total != null ? order.total : 0;
    row.innerHTML = `
      <td><a class="order-link" href="/receipt/${order.order_number}">#${order.order_number}</a></td>
      <td>${order.customer_name}</td>
      <td>${order.ticket_count}</td>
      <td>$${total}</td>
      <td>${formatDate(order.created_at)}</td>
    `;
    ordersBodyEl.appendChild(row);
  });
}

async function loadDashboard() {
  const res = await fetch("/api/dashboard");
  if (!res.ok) {
    return;
  }
  const data = await res.json();
  renderStats(data.summary);
  renderShowings(data.showings);
  renderOrders(data.recentOrders);
}

loadDashboard();
