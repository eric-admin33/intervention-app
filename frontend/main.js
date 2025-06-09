document.addEventListener("DOMContentLoaded", () => {
  showSection('fiches');
  loadFiches();

  // Bulles d’aide “BD”
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('mouseover', e => {
      const tooltip = document.createElement('div');
      tooltip.className = 'bd-tooltip';
      tooltip.textContent = btn.title;
      document.body.appendChild(tooltip);
      const rect = btn.getBoundingClientRect();
      tooltip.style.left = (rect.left + window.scrollX) + "px";
      tooltip.style.top = (rect.bottom + window.scrollY + 8) + "px";
      btn._tooltip = tooltip;
    });
    btn.addEventListener('mouseout', e => {
      if (btn._tooltip) btn._tooltip.remove();
    });
  });
});
function exportExcel() {
  window.open("/api/export-fiches", "_blank");
}

function showSection(section) {
  document.querySelectorAll("main > section").forEach(s => s.style.display = "none");
  document.getElementById(section + "-section").style.display = "block";
  if (section === "fiches") loadFiches();
  if (section === "archives") loadArchives();
  if (section === "comptes") loadComptes();
}

function ficheRow(fiche) {
  return `<div class="fiche" style="border-bottom:1px solid #ffe69e; margin-bottom:1em; padding-bottom:1em;">
    <b>${fiche.titre}</b> — <span>${fiche.description}</span>
    <div>
      <button onclick="editFiche(${fiche.id})" title="Éditer cette fiche">✏️</button>
      <button onclick="archiveFiche(${fiche.id})" title="Archiver cette fiche">🗃️</button>
      <button onclick="imprimerFiche(${fiche.id})" title="Imprimer cette fiche">🖨️</button>
      <button onclick="deleteFiche(${fiche.id})" title="Supprimer cette fiche">🗑️</button>
    </div>
  </div>`;
}

function loadFiches() {
  fetch("/api/fiches?archive=0").then(r => r.json()).then(fiches => {
    let html = `<button onclick="imprimerToutesFiches()" title="Imprimer plusieurs fiches sur une feuille">🖨️ Imprimer tout</button>
    <button onclick="exportExcel()" title="Exporter vers Excel (A4 lisible)">📊 Export Excel</button>`;
    for (const fiche of fiches) html += ficheRow(fiche);
    document.getElementById('fiches-section').innerHTML = html;
  });
}

function loadArchives() {
  fetch("/api/fiches?archive=1").then(r => r.json()).then(fiches => {
    let html = `<h2>Archives</h2>`;
    for (const fiche of fiches) html += ficheRow(fiche);
    document.getElementById('archives-section').innerHTML = html;
  });
}

function archiveFiche(id) {
  fetch(`/api/fiches/${id}/archive`, { method: 'POST' })
    .then(r => r.json()).then(() => loadFiches());
}

function imprimerTout() {
  window.print();
}

// Impression de la sélection :
function imprimerSelection() {
  // Cacher les fiches non cochées
  document.querySelectorAll('.fiche-blanche').forEach(div => {
    const checkbox = div.querySelector('.fiche-select');
    if (checkbox && !checkbox.checked) {
      div.style.display = 'none';
    }
  });
  window.print();
  // Remettre tout après impression
  setTimeout(() => {
    document.querySelectorAll('.fiche-blanche').forEach(div => {
      div.style.display = '';
    });
  }, 1000);
}
function imprimerToutesFiches() {
  // Impression multi-fiches par page (simple pour la démo)
  window.print();
}

function exportExcel() {
  alert("Fonction d’export Excel à intégrer (je te fournis le script si besoin) !");
}

function deleteFiche(id) {
  if(confirm("Supprimer cette fiche ?")) {
    fetch(`/api/fiches/${id}`, { method: 'DELETE' })
      .then(r => r.json()).then(() => loadFiches());
  }
}

function loadComptes() {
  fetch("/api/comptes").then(r => r.json()).then(comptes => {
    let html = `<h2>Comptes</h2><ul>`;
    for(const c of comptes) html += `<li>${c.username} [${c.role}]</li>`;
    html += "</ul>";
    document.getElementById('comptes-section').innerHTML = html;
  });
}
// Fonction pour ouvrir la modale et pré-remplir avec les données de la fiche
function editerlafiche(id) {
  // Récupérer la fiche depuis le JS (à adapter si tu utilises fetch/api)
  let fiche = fiches.find(f => f.id == id);
  if (!fiche) return alert("Fiche introuvable !");
  document.getElementById('edit-id').value = fiche.id;
  document.getElementById('edit-titre').value = fiche.titre;
  document.getElementById('edit-desc').value = fiche.description;
  document.getElementById('edit-etat').value = fiche.etat;
  document.getElementById('modal-edit-fiche').style.display = "flex";
}

// Fermer la fenêtre modale
function fermerModaleEdition() {
  document.getElementById('modal-edit-fiche').style.display = "none";
}

// Gestion du formulaire d’édition
document.addEventListener("DOMContentLoaded", function() {
  const form = document.getElementById('form-edit-fiche');
  if (!form) return;
  form.onsubmit = function(e) {
    e.preventDefault();
    let id = document.getElementById('edit-id').value;
    let titre = document.getElementById('edit-titre').value;
    let desc = document.getElementById('edit-desc').value;
    let etat = document.getElementById('edit-etat').value;

    // Ici, tu peux envoyer les changements au serveur (AJAX/fetch)
    // Exemple avec une variable JS locale (adapter si tu veux un vrai backend) :
    let fiche = fiches.find(f => f.id == id);
    if (fiche) {
      fiche.titre = titre;
      fiche.description = desc;
      fiche.etat = etat;
    }
    fermerModaleEdition();
    // Recharge la liste pour voir les changements :
    if (typeof loadFiches === "function") loadFiches();
  }
});
