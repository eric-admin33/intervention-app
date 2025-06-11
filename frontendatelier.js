 frontendatelier.js

async function loadFiches() {
  const res = await fetch('apidemandes');
  let fiches = await res.json();
  fiches = fiches.filter(f = !f.archive);  On n'affiche pas les archivées
  const fichesDiv = document.getElementById(fiches);
  fichesDiv.innerHTML = ;
  if (fiches.length === 0) {
    fichesDiv.innerHTML = emAucune fiche à traiter pour le moment.em;
    return;
  }
  fiches.forEach(f = {
    const row = document.createElement(div);
    row.className = fiche-row;
    row.innerHTML = `
      span class=fiche-titre${f.titre}span
      span${f.description}span
      spanStatus  ${f.statut  en attente}span
      div class=fiche-actions
        button onclick=marquerFini(${f.id})Finibutton
        button onclick=marquerNonResolu(${f.id})Non résolubutton
        button onclick=archiverFiche(${f.id})Archiverbutton
      div
    `;
    fichesDiv.appendChild(row);
  });
}

async function marquerFini(id) {
  await fetch(`apidemandes${id}`, {
    method PUT,
    headers { Content-Type applicationjson },
    body JSON.stringify({ statut fini })
  });
  loadFiches();
}

async function marquerNonResolu(id) {
  await fetch(`apidemandes${id}`, {
    method PUT,
    headers { Content-Type applicationjson },
    body JSON.stringify({ statut non résolu })
  });
  loadFiches();
}

async function archiverFiche(id) {
  if (confirm(Archiver cette fiche )) {
    await fetch(`apidemandes${id}`, {
      method PUT,
      headers { Content-Type applicationjson },
      body JSON.stringify({ archive true })
    });
    loadFiches();
  }
}

 EXPORT EXCEL  route déjà présente côté backend !
function exportExcel() {
  window.open(apiexport-fiches, _blank);
}

loadFiches();
