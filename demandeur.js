// frontend/demandeur.js

// Pour la démo, on suppose que le nom d'utilisateur est stocké en session/localStorage
const demandeur = localStorage.getItem("username") || "demandeur";

document.getElementById("demandeForm").addEventListener("submit", async e => {
  e.preventDefault();
  const titre = document.getElementById("titre").value.trim();
  const description = document.getElementById("description").value.trim();
  if (!titre || !description) return alert("Tous les champs sont obligatoires !");
  await fetch("/api/demandes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ titre, description, auteur: demandeur })
  });
  document.getElementById("demandeForm").reset();
  chargerMesDemandes();
});

async function chargerMesDemandes() {
  const res = await fetch('/api/demandes');
  let demandes = await res.json();
  demandes = demandes.filter(d => (d.auteur === demandeur));
  const liste = document.getElementById("mesDemandes");
  if (demandes.length === 0) {
    liste.innerHTML = "<em>Aucune demande envoyée pour le moment.</em>";
    return;
  }
  liste.innerHTML = demandes.map(d => `
    <div class="demande-item">
      <b>${d.titre}</b>
      <div>${d.description}</div>
      <span style="font-size:0.9em;color:#555;">Statut: ${d.statut || "en attente"}</span>
    </div>
  `).join("");
}

chargerMesDemandes();
