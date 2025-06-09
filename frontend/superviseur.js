// frontend/superviseur.js

async function loadFiches() {
  const res = await fetch('/api/demandes');
  let fiches = await res.json();

  // Filtres dynamiques
  const showArchive = document.getElementById("filtreArchive").checked;
  const showNonResolu = document.getElementById("filtreNonResolu").checked;
  const showFini = document.getElementById("filtreFini").checked;
  const showAttente = document.getElementById("filtreAttente").checked;

  fiches = fiches.filter(f => {
    if (f.archive && !showArchive) return false;
    if ((f.statut === "non résolu" || f.statut === "non resolu") && !showNonResolu) return false;
    if (f.statut === "fini" && !showFini) return false;
    if ((!f.statut || f.statut === "en attente") && !showAttente) return false;
    return true;
  });

  const fichesDiv = document.getElementById("fiches");
  fichesDiv.innerHTML = "";
  if (fiches.length === 0) {
    fichesDiv.innerHTML = "<em>Aucune fiche selon le filtre sélectionné.</em>";
    return;
  }
fiches.forEach(f => {
  const row = document.createElement("div");
  row.className = "fiche-row";
  row.innerHTML = `
    <span class="fiche-titre">${f.titre}</span>
    <span>${f.description}</span>
    <span>Status : ${f.statut || "en attente"}</span>
    <div class="fiche-actions">
      <a href="fiche.html?id=${f.id}">Voir la fiche</a>
      <span>Archivé : ${f.archive ? "Oui" : "Non"}</span>
      <div class="fiche-actions">
        ${!f.archive ? `
        <button onclick="marquerFini(${f.id})">Fini</button>
        <button onclick="marquerNonResolu(${f.id})">Non résolu</button>
        <button onclick="archiverFiche(${f.id})">Archiver</button>
        ` : ""}
      <!-- ...autres boutons... -->
	 </div>
    `;
    fichesDiv.appendChild(row);
	
  });
}

async function marquerFini(id) {
  await fetch(`/api/demandes/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ statut: "fini" })
  });
  loadFiches();
}

async function marquerNonResolu(id) {
  await fetch(`/api/demandes/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ statut: "non résolu" })
  });
  loadFiches();
}

async function archiverFiche(id) {
  if (confirm("Archiver cette fiche ?")) {
    await fetch(`/api/demandes/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ archive: true })
    });
    loadFiches();
  }
}

// EXPORT EXCEL
function exportExcel() {
  window.open("/api/export-fiches", "_blank");
}

// Gestion des filtres
document.getElementById("filtreArchive").addEventListener("change", loadFiches);
document.getElementById("filtreNonResolu").addEventListener("change", loadFiches);
document.getElementById("filtreFini").addEventListener("change", loadFiches);
document.getElementById("filtreAttente").addEventListener("change", loadFiches);

loadFiches();
