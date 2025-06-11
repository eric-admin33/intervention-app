async function loadTable() {
  const res = await fetch('/api/demandes');
  let fiches = await res.json();
  fiches = fiches.filter(f => !f.archive); // atelier : n’affiche pas les archivées
  const tbody = document.querySelector("#tableFiches tbody");
  tbody.innerHTML = fiches.map(f => `
    <tr>
      <td>${f.id}</td>
      <td>${f.titre}</td>
      <td>${f.description}</td>
      <td>${f.statut || "en attente"}</td>
      <td>${f.archive ? "Oui" : "Non"}</td>
    </tr>
  `).join("");
}
function exportExcel() {
  window.open("/api/export-fiches", "_blank");
}
loadTable();
