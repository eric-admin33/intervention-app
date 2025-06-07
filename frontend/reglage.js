async function loadComptes() {
  const res = await fetch('/api/comptes');
  const users = await res.json();
  const list = document.getElementById("userList");
  list.innerHTML = "";
  users.forEach(u => {
    if (u.username === "admin") return;
    const row = document.createElement("div");
    row.className = "user-row";
    row.innerHTML = `
      <b>${u.username}</b> (${u.role})
      <label><input type="checkbox" class="priv-edit-name" data-id="${u.id}" ${u.canEditName ? "checked" : ""}> nom</label>
      <label><input type="checkbox" class="priv-edit-date" data-id="${u.id}" ${u.canEditDate ? "checked" : ""}> date</label>
      <label><input type="checkbox" disabled ${u.is_system ? "checked" : ""}> système</label>
      <div class="user-actions">
        <button onclick="promptPwChange('${u.username}')">Changer mot de passe</button>
        ${u.is_system ? "" : `<button onclick="deleteUser('${u.id}')">Supprimer</button>`}
      </div>
    `;
    list.appendChild(row);
  });

  document.querySelectorAll('.priv-edit-name, .priv-edit-date').forEach(cb => {
    cb.addEventListener('change', async function() {
      const id = this.getAttribute('data-id');
      const row = this.closest('.user-row');
      const canEditName = row.querySelector('.priv-edit-name').checked;
      const canEditDate = row.querySelector('.priv-edit-date').checked;
      await fetch(`/api/comptes/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ canEditName, canEditDate })
      });
      loadComptes();
    });
  });
}

function ouvrirPopup(nom) {
  fetch(`popups/${nom}.html`)
    .then(r => r.text())
    .then(html => {
      const div = document.getElementById("popup");
      div.innerHTML = html + '<br><button onclick="fermerPopup()">Fermer</button>';
      div.style.display = "block";
    });
}

function fermerPopup() {
  document.getElementById("popup").style.display = "none";
}

function sauvegarderEtRetour() {
  alert("Modifications sauvegardées.");
  window.location.href = "index.html";
}

function ouvrirConnexionAdmin() {
  const div = document.getElementById("popupAdmin");
  div.innerHTML = `
    <h2>Connexion admin</h2>
    <input type="password" id="adminPw" placeholder="Mot de passe admin">
    <button onclick="verifierAdmin()">Connexion</button>
  `;
  div.style.display = "block";
  setTimeout(() => {
    div.style.display = "none";
  }, 20000);
}

function verifierAdmin() {
  const pw = document.getElementById("adminPw").value;
  if (pw === "2025") {
    alert("Accès accordé pour 20s.");
    // Affiche options sensibles si besoin
  } else {
    alert("Mot de passe incorrect.");
  }
}

function promptPwChange(username) {
  const newPw = prompt("Nouveau mot de passe pour " + username);
  if (newPw && newPw.length >= 4) {
    fetch("/api/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, newPassword: newPw })
    }).then(r => r.json()).then(res => {
      if (res.status === "ok") alert("Mot de passe modifié.");
      else alert("Erreur.");
      loadComptes();
    });
  } else {
    alert("Mot de passe trop court.");
  }
}

function deleteUser(id) {
  if (confirm("Supprimer ce compte ?")) {
    fetch(`/api/comptes/${id}`, { method: "DELETE" })
      .then(() => loadComptes());
  }
}

loadComptes();
