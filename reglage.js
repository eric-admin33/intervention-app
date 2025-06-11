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
      <label><input type="checkbox" disabled ${u.isSystem ? "checked" : ""}> système</label>
      <div class="user-actions">
        <button onclick="promptPwChange('${u.username}')">Changer mot de passe</button>
        ${u.isSystem ? "" : `<button onclick="deleteUser('${u.id}')">Supprimer</button>`}
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

// Ouverture d'une popup classique
function ouvrirPopup(nom) {
  fetch(`popups/${nom}.html`)
    .then(r => r.text())
    .then(html => {
      const div = document.getElementById("popup");
      div.innerHTML = html + '<br><button onclick="fermerPopup()">Fermer</button>';
      div.style.display = "block";
      if (nom === 'creer') postInitCreerPopup();
    });
}

// Initialisation spécifique du popup création de compte
function postInitCreerPopup() {
  const nomField = document.getElementById('nom');
  const prenomField = document.getElementById('prenom');
  const usernameField = document.getElementById('username');
  const form = document.getElementById('formCreerCompte');
  if (!nomField || !prenomField || !usernameField || !form) return;

  function genererLogin() {
    const nom = nomField.value.trim().toLowerCase();
    const prenom = prenomField.value.trim().toLowerCase();
    let login = '';
    if (nom && prenom) {
      login = nom + '.' + prenom.charAt(0);
    }
    usernameField.value = login;
  }
  nomField.addEventListener('input', genererLogin);
  prenomField.addEventListener('input', genererLogin);
  genererLogin();

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    if (!data.username) {
      alert("Login généré vide. Remplissez nom et prénom.");
      return;
    }
    if (data.password !== data.confirmPassword) {
      alert("Les mots de passe ne correspondent pas.");
      return;
    }
    const roles = Array.from(form.role.selectedOptions).map(o => o.value).join(',');
    const body = {
      username: data.username,
      password: data.password,
      role: roles,
      canEditName: data.canEditName ? 1 : 0,
      canEditDate: data.canEditDate ? 1 : 0,
      isSystem: data.isSystem ? 1 : 0
    };

    try {
      const res = await fetch('/api/comptes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const msg = await res.json().catch(() => ({}));
      if (res.ok && msg.ok) {
        alert("Compte créé !");
        fermerPopup();
        loadComptes();
      } else {
        alert(msg.error || `Erreur lors de la création du compte (code ${res.status})`);
        if ((msg.error || "").toLowerCase().includes("session") || res.status === 401) {
          window.location.href = "index.html";
        }
      }
    } catch (err) {
      console.log("Erreur JS :", err);
      alert("Erreur technique, serveur inaccessible !");
    }
  });
}

// Fermer le popup
function fermerPopup() {
  document.getElementById("popup").style.display = "none";
}

// Sauvegarde & retour accueil
function sauvegarderEtRetour() {
  alert("Modifications sauvegardées.");
  window.location.href = "index.html";
}

// Connexion admin et gestion du mot de passe
function ouvrirConnexionAdmin() {
  const div = document.getElementById("popupAdmin");
  div.innerHTML = `
  <h2>Connexion admin</h2>
  <input type="password" id="adminPw" placeholder="Mot de passe admin" style="width:90%;max-width:270px;"><br>
  <label>Durée de session :
    <select id="adminSessionTime">
      <option value="30">30 sec</option>
      <option value="60" selected>60 sec</option>
      <option value="90">90 sec</option>
    </select>
  </label>
  <button onclick="verifierAdmin()">Connexion</button>
`;
  div.style.display = "block";
}

function verifierAdmin() {
  const pw = document.getElementById("adminPw").value;
  const time = parseInt(document.getElementById("adminSessionTime").value);
  fetch("/api/login-admin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: "admin", password: pw, session_time: time })
  })
    .then(r => r.json())
    .then(res => {
      if (res.ok) {
        document.getElementById("popupAdmin").innerHTML = `
          <h3>Changer le mot de passe admin</h3>
          <input type="password" id="newAdminPw" placeholder="Nouveau mot de passe"><br>
          <button onclick="changerAdminPw()">Changer</button>
        `;
        setTimeout(() => {
          document.getElementById("popupAdmin").style.display = "none";
          alert("Session admin expirée !");
        }, time * 1000);
      } else {
        alert("Mot de passe incorrect !");
      }
    });
}

function changerAdminPw() {
  const newPw = document.getElementById("newAdminPw").value;
  if (newPw.length < 4) {
    alert("Mot de passe trop court !");
    return;
  }
  fetch("/api/change-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: "admin", newPassword: newPw })
  })
    .then(r => r.json())
    .then(res => {
      if (res.ok) alert("Mot de passe changé !");
      else alert("Erreur.");
      document.getElementById("popupAdmin").style.display = "none";
    });
}

// Changement de mot de passe pour les autres comptes
function promptPwChange(username) {
  const newPw = prompt("Nouveau mot de passe pour " + username);
  if (newPw && newPw.length >= 4) {
    fetch("/api/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, newPassword: newPw })
    }).then(r => r.json()).then(res => {
      if (res.ok) alert("Mot de passe modifié.");
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
function togglePw(btn, inputId) {
  const input = document.getElementById(inputId);
  const eyeOpen = btn.querySelector('.eye-open');
  const eyeClosed = btn.querySelector('.eye-closed');
  if (input.type === "password") {
    input.type = "text";
    eyeOpen.style.display = "none";
    eyeClosed.style.display = "block";
  } else {
    input.type = "password";
    eyeOpen.style.display = "block";
    eyeClosed.style.display = "none";
  }
}
// Appel initial
loadComptes();
