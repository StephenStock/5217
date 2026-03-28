const wireTableSearch = (inputSelector, rowSelector) => {
  const searchInput = document.querySelector(inputSelector);
  const rows = document.querySelectorAll(rowSelector);

  if (!searchInput || rows.length === 0) {
    return;
  }

  searchInput.addEventListener("input", (event) => {
    const query = event.target.value.trim().toLowerCase();

    rows.forEach((row) => {
      const matches = row.textContent.toLowerCase().includes(query);
      row.hidden = !matches;
    });
  });
};

wireTableSearch("#memberSearch", "#membersTable tr");
wireTableSearch("#bankSearch", "#bankTable tr");
wireTableSearch("#memberPageSearch", "#memberPageTable tr");

document.querySelectorAll(".bank-category-select[data-autosubmit='true']").forEach((select) => {
  select.addEventListener("change", () => {
    const form = select.closest("form");
    if (!form) {
      return;
    }

    const status = form.closest("tr")?.querySelector(".bank-row-status");
    const previousValue = select.dataset.previousValue || select.defaultValue || "";
    const formData = new FormData(form);

    if (status) {
      status.textContent = "…";
      status.classList.remove("is-success", "is-error");
    }

    fetch(form.action, {
      method: "POST",
      body: formData,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json",
      },
    })
      .then(async (response) => {
        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          throw new Error(payload.message || "Save failed");
        }

        select.dataset.previousValue = select.value;
        if (status) {
          status.textContent = "✓";
          status.classList.add("is-success");
          status.classList.remove("is-error", "is-needed");
          window.setTimeout(() => {
            status.textContent = "";
            status.classList.remove("is-success");
          }, 1200);
        }
      })
      .catch(() => {
        select.value = previousValue;
        if (status) {
          status.textContent = "✕";
          status.classList.add("is-error");
          window.setTimeout(() => {
            status.textContent = "";
            status.classList.remove("is-error");
          }, 1800);
        }
      });
  });
});

document.querySelectorAll(".bank-category-select[data-autosubmit='true']").forEach((select) => {
  select.dataset.previousValue = select.value;
});
