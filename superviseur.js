let allFiches = [];

function chargerFiches() {
  // Charge toutes les fiches actives
  fetch('/api/demandes?archive=0')
    .then(r => r.json())
    .then(liste => {
      allFiches = liste;
      afficherFiches('toutes');
    });

  // Charge les archives
  fetch('/api/demandes?archive=1')
    .then(r => r.json())
    .then(liste => {
      afficherArchives(liste);
    });
}

// Affiche selon le filtre demandé par le bouton
function afficherFiches(type) {
  let fiches = allFiches;
  if (type === 'enattente') {
    fiches = fiches.filter(f =>
      ['en attente', 'attente', 'attente devis', 'attente entreprise', 'en attente devis', 'en attente entreprise'].includes((f.statut || f.etat || '').toLowerCase())
    );
  } else if (type === 'fini') {
    fiches = fiches.filter(f =>
      ['fini', 'terminé', 'termine', 'refusé', 'refuse'].includes((f.statut || f.etat || '').toLowerCase())
    );
  } else if (type === 'nonresolue') {
    fiches = fiches.filter(f =>
      ['non résolue', 'non resolu', 'non résolu'].includes((f.statut || f.etat || '').toLowerCase())
    );
  }
  const tbody = document.getElementById('ficheTbody');
  tbody.innerHTML = fiches.map(f => `
    <tr>
      <td>${f.id ?? ''}</td>
      <td>${f.titre ?? f.nom ?? ''}</td>
      <td>${f.salle ?? ''}</td>
      <td>${f.batiment ?? ''}</td>
      <td>${f.description ?? f.type_panne ?? ''}</td>
      <td>${f.date ?? ''}</td>
      <td>${f.statut ?? f.etat ?? ''}</td>
      <td>${f.archive ? 'Oui' : 'Non'}</td>
    </tr>
  `).join('') || "<tr><td colspan='8'><i>Aucune fiche</i></td></tr>";
}

function afficherArchives(liste) {
  const tbody = document.getElementById('archiveTbody');
  tbody.innerHTML = (liste || []).map(f => `
    <tr>
      <td>${f.id ?? ''}</td>
      <td>${f.titre ?? f.nom ?? ''}</td>
      <td>${f.salle ?? ''}</td>
      <td>${f.batiment ?? ''}</td>
      <td>${f.description ?? f.type_panne ?? ''}</td>
      <td>${f.date ?? ''}</td>
      <td>${f.statut ?? f.etat ?? ''}</td>
      <td>${f.archive ? 'Oui' : 'Non'}</td>
    </tr>
  `).join('') || "<tr><td colspan='8'><i>Aucune archive</i></td></tr>";
}

// Purge, export, etc. (conserve tes fonctions annexes)
// ...

// Appel initial (chargement automatique au démarrage)
document.addEventListener("DOMContentLoaded", chargerFiches);
