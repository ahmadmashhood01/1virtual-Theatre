const cName = document.getElementById("cName");
const cEmail = document.getElementById("cEmail");
const cRewards = document.getElementById("cRewards");
const cFeedback = document.getElementById("cFeedback");
const form = document.getElementById("customerForm");
const customersBody = document.getElementById("customersBody");
const customerCount = document.getElementById("customerCount");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  cFeedback.textContent = "";
  const res = await fetch("/api/customers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: cName.value,
      email: cEmail.value,
      rewardsMember: cRewards.checked,
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    cFeedback.textContent = data.error || "Failed to save.";
    cFeedback.style.color = "#fb7185";
    return;
  }
  cFeedback.textContent = `Saved as ${data.customerId}.`;
  cFeedback.style.color = "#4ade80";
  cName.value = "";
  cEmail.value = "";
  cRewards.checked = false;
  loadCustomers();
});

async function loadCustomers() {
  const res = await fetch("/api/customers");
  if (!res.ok) {
    return;
  }
  const rows = await res.json();
  customersBody.innerHTML = "";
  customerCount.textContent = String(rows.length);
  rows.forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.customer_id}</td>
      <td>${r.firstname} ${r.lastname}</td>
      <td>${r.email}</td>
      <td>${r.rewards_member ? "Yes" : "No"}</td>
    `;
    customersBody.appendChild(tr);
  });
}

loadCustomers();
