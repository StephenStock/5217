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
    if (form) {
      form.submit();
    }
  });
});
