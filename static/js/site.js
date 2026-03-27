const searchInput = document.querySelector("#memberSearch");
const memberRows = document.querySelectorAll("#membersTable tr");

if (searchInput && memberRows.length > 0) {
  searchInput.addEventListener("input", (event) => {
    const query = event.target.value.trim().toLowerCase();

    memberRows.forEach((row) => {
      const matches = row.textContent.toLowerCase().includes(query);
      row.hidden = !matches;
    });
  });
}
