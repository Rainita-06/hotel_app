// =======================
// Complaint Summary Loader complaint.html
// =======================
document.addEventListener("DOMContentLoaded", function () {
  const container = document.getElementById("complaint-summary");
  if (!container) return;

  fetch("/api/complaint-summary/")
    .then((response) => response.json())
    .then((data) => {
      container.innerHTML = "";

      const statusLabels = {
        NEW: "New",
        ACCEPTED: "Accepted",
        ON_HOLD: "On Hold",
        CLOSED: "Closed",
      };

      Object.keys(statusLabels).forEach((status) => {
        let count = data[status] || 0;
        let card = document.createElement("div");
        card.className = "p-3 bg-light border rounded text-center shadow-sm";

        card.innerHTML = `
          <h4 class="mb-0">${count}</h4>
          <small class="text-muted">${statusLabels[status]}</small>
        `;

        container.appendChild(card);
      });
    })
    .catch((err) => console.error("Error loading summary:", err));
});


document.addEventListener("DOMContentLoaded", function () {
    // Initialize all toasts on the page
    var toastElList = [].slice.call(document.querySelectorAll('.toast'));
    var toastList = toastElList.map(function (toastEl) {
        var toast = new bootstrap.Toast(toastEl, { delay: 3000 });
        toast.show();
        return toast;
    });
});
