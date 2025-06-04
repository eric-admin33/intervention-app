import os
import zipfile
from datetime import datetime
import json
import sqlite3
from flask import Flask, request, jsonify, send_file, send_from_directory, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
import xlsxwriter

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = "un_secret_ultra_long_et_unique_à_toiper"  # Change cette clé pour la prod !
CORS(app)

ARCHIVES_DIR = os.path.join(os.path.dirname(__file__), "archives")
if not os.path.exists(ARCHIVES_DIR):
    os.makedirs(ARCHIVES_DIR)

DB_PATH = os.path.join(os.path.dirname(__file__), 'site-maintenance.db')
DATA_FILE = os.path.join(os.path.dirname(__file__), "demandes.json")

# --- INITIALISATION SQLITE & MIGRATION DOUCE ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS comptes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    # Ajoute les colonnes privilèges si absentes
    try:
        c.execute("ALTER TABLE comptes ADD COLUMN can_edit_name INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE comptes ADD COLUMN can_edit_date INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    c.execute('''
        CREATE TABLE IF NOT EXISTS fiches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT,
            description TEXT,
            etat TEXT,
            archive INTEGER DEFAULT 0
        )
    ''')
    c.execute("INSERT OR IGNORE INTO comptes (username, password, role) VALUES (?, ?, ?)",
              ('admin', generate_password_hash('2025'), 'admin'))
    conn.commit()
    conn.close()

init_db()

# ========== COMPTES ==========
@app.route('/api/comptes', methods=['GET'])
def get_comptes():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, username, role, can_edit_name, can_edit_date FROM comptes')
    comptes = [{
        'id': row[0],
        'username': row[1],
        'role': row[2],
        'canEditName': bool(row[3]),
        'canEditDate': bool(row[4])
    } for row in c.fetchall()]
    conn.close()
    return jsonify(comptes)

@app.route('/api/comptes', methods=['POST'])
def add_compte():
    data = request.json
    hashed_pw = generate_password_hash(data['password'])
    can_edit_name = int(data.get('canEditName', False))
    can_edit_date = int(data.get('canEditDate', False))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            'INSERT INTO comptes (username, password, role, can_edit_name, can_edit_date) VALUES (?, ?, ?, ?, ?)',
            (data['username'], hashed_pw, data['role'], can_edit_name, can_edit_date)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Nom d\'utilisateur déjà existant'}), 409
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/comptes/<int:compte_id>', methods=['DELETE'])
def delete_compte(compte_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM comptes WHERE id=?', (compte_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})

@app.route('/api/change-password', methods=['POST'])
def change_password():
    data = request.json
    username = data['username']
    new_password = data['newPassword']
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE comptes SET password=? WHERE username=?', (generate_password_hash(new_password), username))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/verif-login', methods=['POST'])
def verif_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT password, role, can_edit_name, can_edit_date FROM comptes WHERE username=?', (username,))
    row = c.fetchone()
    conn.close()
    if row and check_password_hash(row[0], password):
        session['username'] = username
        session['role'] = row[1]
        session['canEditName'] = bool(row[2])
        session['canEditDate'] = bool(row[3])
        return jsonify({
            'ok': True,
            'role': row[1],
            'canEditName': bool(row[2]),
            'canEditDate': bool(row[3])
            @app.route('/api/comptes/<int:compte_id>', methods=['PUT', 'PATCH'])
def update_compte_privileges(compte_id):
    data = request.json
    can_edit_name = int(data.get('canEditName', False))
    can_edit_date = int(data.get('canEditDate', False))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE comptes SET can_edit_name=?, can_edit_date=? WHERE id=?",
        (can_edit_name, can_edit_date, compte_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'updated'})

        })
    else:
        return jsonify({'ok': False})

# Petite API d'infos session pour le frontend (utile demandeur.html)
@app.route('/api/userinfo')
def api_userinfo():
    return jsonify({
        'username': session.get('username', ''),
        'role': session.get('role', ''),
        'canEditName': session.get('canEditName', False),
        'canEditDate': session.get('canEditDate', False)
    })


# ========== LOGIN & ADMIN PROTECTION ==========
@app.route('/api/login-admin', methods=['POST'])
def login_admin():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password, role FROM comptes WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row and check_password_hash(row[0], password) and row[1] == 'admin':
        session["is_admin"] = True
        return jsonify({"ok": True})
    else:
        return jsonify({"ok": False}), 401

@app.route('/api/check-admin')
def check_admin():
    return jsonify({"ok": bool(session.get("is_admin"))})

@app.route('/api/logout-admin')
def logout_admin():
    session.pop("is_admin", None)
    return jsonify({"ok": True})

@app.route('/reglage.html')
def reglage():
    if not session.get("is_admin"):
        return app.send_static_file("login_admin.html")
    return app.send_static_file("reglage.html")

# ========== EXPORT EXCEL ==========
def load_demandes():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_demandes(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def export_fiches_xlsx(demandes, filename, sheetname):
    output = BytesIO()
    wb = xlsxwriter.Workbook(output)
    ws = wb.add_worksheet(sheetname)

    # Format de l'en-tête
    header_format = wb.add_format({
        'bold': True,
        'bg_color': '#ddeeff',
        'border': 1,
        'font_color': '#143560',
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    })

    # Format des cellules avec retour à la ligne auto
    cell_format = wb.add_format({
        'border': 1,
        'align': 'left',
        'valign': 'top',
        'text_wrap': True
    })

    headers = ['ID', 'Nom', 'Salle', 'Bâtiment', 'Panne', 'Date', 'Statut', 'Archivée']
    for col, h in enumerate(headers):
        ws.write(0, col, h, header_format)
        ws.set_column(col, col, 18)  # Largeur adaptée, modifiable

    # Remplissage des lignes
    for row, d in enumerate(demandes, 1):
        ws.write(row, 0, d.get('id', ''), cell_format)
        ws.write(row, 1, d.get('nom', d.get('titre', '')), cell_format)
        ws.write(row, 2, d.get('salle', ''), cell_format)
        ws.write(row, 3, d.get('batiment', ''), cell_format)
        ws.write(row, 4, d.get('type_panne', d.get('description', '')), cell_format)
        ws.write(row, 5, d.get('date', ''), cell_format)
        ws.write(row, 6, d.get('statut', d.get('etat', '')), cell_format)
        archive = d.get('archive', False)
        ws.write(row, 7, "Oui" if archive else "Non", cell_format)
        ws.set_row(row, 32)  # Hauteur minimale (32 pixels), auto-adaptée si texte long

    wb.close()
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route('/api/export-fiches')
def export_fiches():
    demandes = load_demandes()
    return export_fiches_xlsx(demandes, "fiches.xlsx", "Fiches")

@app.route('/api/export-fiches-avance')
def export_fiches_avance():
    demandes = [d for d in load_demandes() if d.get('statut') == "avancé"]
    return export_fiches_xlsx(demandes, "fiches_avance.xlsx", "Fiches Avancées")

@app.route('/api/export-fiches-non-resolu')
def export_fiches_non_resolu():
    demandes = [d for d in load_demandes() if d.get('statut') in ["non résolu", "non resolu"]]
    return export_fiches_xlsx(demandes, "fiches_non_resolues.xlsx", "Fiches Non Résolues")

@app.route('/api/export-fiches-fini')
def export_fiches_fini():
    demandes = [d for d in load_demandes() if d.get('statut') == "fini"]
    return export_fiches_xlsx(demandes, "fiches_finies.xlsx", "Fiches Finies")

# ========== ROUTES DEMANDES (JSON) ==========
@app.route("/api/demandes", methods=["GET"])
def get_demandes_json():
    return jsonify(load_demandes())

@app.route("/api/demandes", methods=["POST"])
def create_demande():
    data = request.get_json()
    demandes = load_demandes()
    data["id"] = len(demandes) + 1
    data.setdefault("titre", "")
    data.setdefault("description", "")
    data.setdefault("statut", "en attente")
    data.setdefault("auteur", "")
    data.setdefault("archive", False)
    demandes.append(data)
    save_demandes(demandes)
    return jsonify({"status": "ok", "id": data["id"]})

@app.route("/api/demandes/<int:id>", methods=["PUT"])
def update_demande(id):
    data = request.get_json()
    demandes = load_demandes()
    updated = False
    for d in demandes:
        if d["id"] == id:
            d.update(data)
            updated = True
    if updated:
        save_demandes(demandes)
        return jsonify({"status": "updated"})
    else:
        return jsonify({"error": "not found"}), 404

@app.route("/api/demandes/<int:id>", methods=["DELETE"])
def delete_demande(id):
    demandes = load_demandes()
    demandes = [d for d in demandes if d["id"] != id]
    save_demandes(demandes)
    return jsonify({"status": "deleted"})

@app.route("/")
def root():
    return app.send_static_file("index.html")

# ========== ARCHIVAGE FICHE EN ZIP ==========
@app.route('/api/archiver-fiche/<int:fiche_id>', methods=['POST'])
def archiver_fiche(fiche_id):
    demandes = load_demandes()
    fiche = next((d for d in demandes if d.get("id") == fiche_id), None)
    if not fiche:
        return jsonify({"error": "Fiche introuvable"}), 404
    fiche["archive"] = True
    save_demandes(demandes)
    txt = "\n".join([
        f"ID: {fiche.get('id')}",
        f"Nom: {fiche.get('nom', fiche.get('titre', ''))}",
        f"Salle: {fiche.get('salle', '')}",
        f"Bâtiment: {fiche.get('batiment', '')}",
        f"Panne: {fiche.get('type_panne', fiche.get('description', ''))}",
        f"Date: {fiche.get('date', '')}",
        f"Statut: {fiche.get('statut', fiche.get('etat', ''))}",
    ])
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    zipname = f"fiche_{fiche_id}_{now}.zip"
    zip_path = os.path.join(ARCHIVES_DIR, zipname)
    txt_filename = f"fiche_{fiche_id}.txt"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        zipf.writestr(txt_filename, txt)
    return jsonify({"zip": zipname, "url": f"/archives/{zipname}"})

@app.route('/archives/<filename>')
def get_archive(filename):
    return send_from_directory(ARCHIVES_DIR, filename)

@app.route('/archives/', methods=['GET'])
def lister_archives():
    fichiers = [f for f in os.listdir(ARCHIVES_DIR) if f.endswith('.zip')]
    fichiers.sort(reverse=True)
    return jsonify(fichiers)

@app.route('/archives/<filename>', methods=['DELETE'])
def delete_archive(filename):
    path = os.path.join(ARCHIVES_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

# ========== STATIC & MAIN LAUNCH ==========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
