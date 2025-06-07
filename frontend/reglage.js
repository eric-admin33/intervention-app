
async function loadComptes() {
  const res = await fetch('/api/comptes');
  const users = await res.json();
  const list = document.getElementById("userList");
  list.innerHTML = "";
  users.forEach(u => {
    if (u.username === 'admin') return;
    const row = document.createElement("div");
    row.className = "user-row";
    row.innerHTML = `
      <b>${u.username}</b>
      <span class="user-role">${u.role}</span>
      <div class="user-options" style="display: flex; flex-wrap: wrap; gap: 1em; font-size: 0.95em;">
        <label>
          <input type="checkbox" ${u.canEditName ? "checked" : ""} data-id="${u.id}" class="priv-edit-name">
          Peut modifier le nom
        </label>
        <label>
          <input type="checkbox" ${u.canEditDate ? "checked" : ""} data-id="${u.id}" class="priv-edit-date">
          Peut modifier la date
        </label>
        <label>
          <input type="checkbox" ${u.isSystem ? "checked" : ""} data-id="${u.id}" class="priv-system" disabled>
          Compte système
        </label>
      </div>
      <div class="user-actions">
        <button onclick="promptPwChange('${u.username}')">Modifier mot de passe</button>
        ${u.isSystem ? '' : `<button onclick="deleteUser('${u.id}')">Supprimer</button>`}
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
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({canEditName, canEditDate})
      });
      loadComptes();
    });
  });
}
