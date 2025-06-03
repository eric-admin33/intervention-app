// frontend/reglage.js

async function loadComptes() {
  const res = await fetch('/api/comptes');
  const users = await res.json();
  const list = document.getElementById("userList");
  list.innerHTML = "";
  users.forEach(u => {
    const row = document.createElement("div");
    row.className = "user-row";
    row.innerHTML = `
      <b>${u.username}</b>
      <span class="user-role">${u.role}</span>
      <div class="user-actions">
        <button onclick="promptPwChange('${u.username}')">Modifier mot de passe</button>
        ${u.role !== 'admin' ? `<button onclick="deleteUser('${u.id}')">Supprimer</button>` : ''}
      </div>
    `;
    list.appendChild(row);
  });
}

window.promptPwChange = function(username) {
  const newPw = prompt(`Nouveau mot de passe pour ${username}:`);
  if (newPw && newPw.length >= 4) {
    fetch('/api/change-password', {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, newPassword: newPw })
    }).then(r => r.json()).then(res => {
      if (res.status === "ok") alert("Mot de passe modifié.");
      else alert("Erreur.");
      loadComptes();
    });
  } else if (newPw) {
    alert("Mot de passe trop court.");
  }
};

window.deleteUser = function(id) {
  if (confirm("Supprimer ce compte ?")) {
    fetch(`/api/comptes/${id}`, { method: "DELETE" })
      .then(r => r.json()).then(() => loadComptes());
  }
};

document.getElementById("addUserForm").addEventListener("submit", e => {
  e.preventDefault();
  const username = document.getElementById("newUsername").value.trim();
  const password = document.getElementById("newPassword").value;
  const role = document.getElementById("newRole").value;
  if (!username || !password || !role) return alert("Champs manquants");
  fetch('/api/comptes', {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, role })
  }).then(r => {
    if (r.ok) {
      loadComptes();
      e.target.reset();
    } else {
      alert("Erreur ou doublon !");
    }
  });
});
// frontend/footer.js
(function(){
  const style = document.createElement('style');
  style.innerHTML = `
    .site-footer {
      text-align: center;
      color: #7c8ead;
      font-size: 1em;
      margin: 40px 0 10px 0;
      padding-bottom: 12px;
      letter-spacing: 0.02em;
    }
    .site-footer a { color: #3f91e5; text-decoration: underline; }
    .site-footer a:hover { color: #214177; }
  `;
  document.head.appendChild(style);

  const footer = document.createElement('footer');
  footer.className = 'site-footer';
  footer.innerHTML = `
    &copy; 2025 Conception : Eric.G pour le Lycée Camille-Jullian, Bordeaux.<br>
    Tous droits réservés. &nbsp;|&nbsp; 
    Contact : <a href="mailto:atelier.kju@gmail.com">atelier.kju@gmail.com</a>
    <br><br>
  `;
  const mainWrap = document.querySelector('.main-wrap');
  if(mainWrap) {
    mainWrap.insertAdjacentElement('afterend', footer);
  } else {
    document.body.appendChild(footer);
  }
})();

// Initialisation
loadComptes();
