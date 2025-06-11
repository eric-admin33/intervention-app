import os
import sqlite3
import json
import time
from flask import Flask, request, jsonify, session, render_template
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from flask import send_file

# Liste des rôles autorisés
ROLES_AUTORISES = ['demandeur', 'atelier', 'superviseur', 'admin', 'root']

app = Flask(
    __name__,
    static_folder='../frontend',
    static_url_path=''
)
app.secret_key = "un_secret_ultra_long_et_unique_à_toiper"
CORS(app)
app.permanent_session_lifetime = timedelta(minutes=5)
DB_PATH = os.path.join(os.path.dirname(__file__), 'site-maintenance.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE demandes ADD COLUMN archive INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    # Comptes
    c.execute('''
        CREATE TABLE IF NOT EXISTS comptes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            can_edit_name INTEGER DEFAULT 0,
            can_edit_date INTEGER DEFAULT 0,
            is_root INTEGER DEFAULT 0,
            is_system INTEGER DEFAULT 0
        )
    ''')
    # Demandes
    c.execute('''
        CREATE TABLE IF NOT EXISTS demandes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT,
            description TEXT,
            salle TEXT,
            batiment TEXT,
            date TEXT,
            statut TEXT DEFAULT 'en attente',
            date_crea TEXT DEFAULT (datetime('now','localtime')),
            motif_non_resolue TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES comptes(id)
        )
    ''')
    # Admin de base
    c.execute("INSERT OR IGNORE INTO comptes (username, password, role) VALUES (?, ?, ?)",
              ('admin', generate_password_hash('2025'), 'admin'))
    # Root invisible
    c.execute("INSERT OR IGNORE INTO comptes (username, password, role, is_root, is_system) VALUES (?, ?, ?, 1, 1)",
              ('letigredu33', generate_password_hash('LeTigre@@1968'), 'root'))
    conn.commit()
    conn.close()

init_db()

# ----------- API Comptes ---------------
@app.route('/api/comptes', methods=['GET'])
def get_comptes():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, username, role, can_edit_name, can_edit_date, is_system FROM comptes WHERE is_root != 1 AND username != "admin"')
    comptes = [{
        'id': row[0],
        'username': row[1],
        'role': row[2],
        'canEditName': bool(row[3]),
        'canEditDate': bool(row[4]),
        'isSystem': bool(row[5])
    } for row in c.fetchall()]
    conn.close()
    return jsonify(comptes)

@app.route('/api/comptes', methods=['POST'])
def create_compte():
    if 'is_admin' not in session:
        return jsonify({'error': 'Session expirée ou accès interdit. Reconnectez-vous.'}), 401

    data = request.json
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Champs requis manquants'}), 400
    # Accept multi-roles avec virgule (frontend compatible)
    roles = data['role']
    for role in roles.split(','):
        if role not in ROLES_AUTORISES:
            return jsonify({'error': 'Rôle invalide'}), 400

    hashed = generate_password_hash(data['password'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO comptes (username, password, role, can_edit_name, can_edit_date, is_system)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['username'],
            hashed,
            data['role'],
            int(data.get('canEditName', False)),
            int(data.get('canEditDate', False)),
            int(data.get('isSystem', False))
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Ce login existe déjà.'}), 409
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/comptes/<int:compte_id>', methods=['DELETE'])
def delete_compte(compte_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT is_system FROM comptes WHERE id=?', (compte_id,))
    row = c.fetchone()
    if row and row[0] == 1:
        conn.close()
        return jsonify({'error': 'compte système non supprimable'}), 403
    c.execute('DELETE FROM comptes WHERE id=?', (compte_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/change-password', methods=['POST'])
def change_pw():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE comptes SET password=? WHERE username=?',
              (generate_password_hash(data['newPassword']), data['username']))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/comptes/<int:compte_id>', methods=['PUT'])
def update_privs(compte_id):
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE comptes
        SET can_edit_name=?, can_edit_date=?, is_system=?
        WHERE id=?
    ''', (
        int(data.get('canEditName', False)),
        int(data.get('canEditDate', False)),
        int(data.get('isSystem', False)),
        compte_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/login-admin', methods=['POST'])
def login_admin():
    data = request.get_json()
    session_time = int(data.get('session_time', 300))  # Valeur par défaut côté JS : 300 sec = 5 min
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password, role, is_root FROM comptes WHERE username=?", (data['username'],))
    row = c.fetchone()
    conn.close()
    if row and check_password_hash(row[0], data['password']):
        if row[1] == "admin" or row[2] == 1:
            session.permanent = True
            session['is_admin'] = True
            session['expire_admin'] = int(time.time()) + session_time
            session['role'] = row[1] if row[1] else "admin"
            if row[2] == 1:
                session['is_root'] = True
            return jsonify({'ok': True})
    return jsonify({'ok': False}), 401

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password, role, id, is_root, is_system FROM comptes WHERE username=?", (data['username'],))
    row = c.fetchone()
    conn.close()
    if row:
        good = False
        try:
            good = check_password_hash(row[0], data['password'])
        except Exception:
            pass
        if not good:
            good = (row[0] == data['password'])
        if good:
            session['user_id'] = row[2]
            session['role'] = row[1]
            session['is_root'] = bool(row[3])
            session['is_system'] = bool(row[4])
            return jsonify({
                'ok': True,
                'role': row[1],
                'id': row[2]
            })
    return jsonify({'ok': False, 'error': 'identifiant ou mot de passe incorrect'}), 401

@app.route('/api/logout-admin')
def logout_admin():
    session.pop('is_admin', None)
    session.pop('is_root', None)
    session.pop('expire_admin', None)
    return jsonify({'ok': True})

@app.route('/api/check-admin')
def check_admin():
    return jsonify({'ok': session.get('is_admin', False)})

# ----------- API DÉMANDES ---------------
@app.route('/api/demandes', methods=['GET', 'POST', 'DELETE'])
def api_demandes():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        if 'user_id' not in session:
            conn.close()
            return jsonify({'error': 'Non connecté'}), 401
        data = request.json
        titre = data.get('titre', '')
        description = data.get('description', '')
        salle = data.get('salle', '')
        batiment = data.get('batiment', '')
        date = data.get('date', '')
        statut = 'Nouveau'
        user_id = session.get('user_id')
        c.execute(
            'INSERT INTO demandes (titre, description, salle, batiment, date, statut, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (titre, description, salle, batiment, date, statut, user_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'ok': True})

    elif request.method == 'DELETE':
        if not session.get('role') == 'superviseur':
            conn.close()
            return jsonify({'error': 'Accès refusé'}), 403
        c.execute("DELETE FROM demandes")
        conn.commit()
        conn.close()
        return jsonify({'ok': True})

    else:  # GET
        role = session.get('role', '')
        user_id = session.get('user_id')
        statut = request.args.get('statut')
        archive = request.args.get('archive')
        base_query = 'SELECT d.id, d.titre, d.description, d.salle, d.batiment, d.date, d.statut, d.date_crea, c.username, d.archive FROM demandes d LEFT JOIN comptes c ON d.user_id = c.id'
        params = []
        conditions = []

        if role in ("atelier", "superviseur"):
            if statut:
                conditions.append('d.statut=?')
                params.append(statut)
                # NOUVEAU : filtrer sur archive si fourni
            if archive is not None:
                conditions.append('d.archive=?')
                params.append(int(archive))
        else:
            conditions.append('d.user_id=?')
            params.append(user_id)
            if statut:
                conditions.append('d.statut=?')
                params.append(statut)
            if archive is not None:
                conditions.append('d.archive=?')
                params.append(int(archive))

        if conditions:
            base_query += ' WHERE ' + ' AND '.join(conditions)
        c.execute(base_query, params)
        demandes = [{
            'id': row[0],
            'titre': row[1],
            'description': row[2],
            'salle': row[3],
            'batiment': row[4],
            'date': row[5],
            'statut': row[6],
            'date_crea': row[7],
            'user': row[8],
            'archive': row[9]
        } for row in c.fetchall()]
        conn.close()
        return jsonify(demandes)
@app.route('/api/demandes/<int:demande_id>/archive', methods=['POST'])
def archive_demande(demande_id):
    if session.get('role') not in ('superviseur', 'admin', 'root'):
        return jsonify({'error': 'Accès refusé'}), 403
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE demandes SET archive=1 WHERE id=?', (demande_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})  

@app.route('/api/demandes/<int:demande_id>', methods=['PUT'])
def maj_demande(demande_id):
    if 'user_id' not in session and not session.get("is_admin"):
        return jsonify({'error': 'Non connecté'}), 401
    data = request.json
    statut = data.get("statut")
    titre = data.get("nom") or data.get("titre")
    description = data.get("type_panne") or data.get("description")
    motif_non_resolue = data.get("motif_non_resolue", "")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE demandes
        SET statut=?, titre=?, description=?, motif_non_resolue=?
        WHERE id=?
    ''', (statut, titre, description, motif_non_resolue if statut == "Non résolue" else None, demande_id))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/userinfo')
def userinfo():
    if 'user_id' not in session:
        return jsonify({})
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT username, can_edit_name, can_edit_date FROM comptes WHERE id=?', (session['user_id'],))
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify({
            'username': row[0],
            'canEditName': bool(row[1]),
            'canEditDate': bool(row[2])
        })
    return jsonify({})

# ----------- ROUTES HTML ---------------
@app.route('/')
@app.route('/index.html')
def home():
    role = session.get('role', 'accueil')
    return render_template("index.html", role=role)

@app.route('/reglage.html')
def reglage_protected():
    expire = session.get('expire_admin')
    now = int(time.time())
    if not session.get("is_admin") or (expire and now > expire):
        session.pop('is_admin', None)
        session.pop('expire_admin', None)
        return render_template("login_admin.html", role="admin")
    role = session.get('role', 'admin')
    return render_template("reglage.html", role=role)

@app.route('/login_root.html')
def login_root_page():
    role = session.get('role', 'root')
    return render_template('login_root.html', role=role)

@app.route('/admin.html')
def admin_page():
    return render_template('admin.html', role='admin')

@app.route('/atelier_attente.html')
def atelier_attente():
    role = session.get('role', 'atelier')
    return render_template('atelier_attente.html', role=role)

@app.route('/atelier_nouvelle.html')
def atelier_nouvelle():
    role = session.get('role', 'atelier')
    return render_template('atelier_nouvelle.html', role=role)

@app.route('/atelier_encours.html')
def atelier_encours():
    role = session.get('role', 'atelier')
    return render_template('atelier_encours.html', role=role)

@app.route('/atelier_excel.html')
def atelier_excel():
    role = session.get('role', 'atelier')
    return render_template('atelier_excel.html', role=role)

@app.route('/demandeur.html')
def demandeur():
    role = session.get('role', 'demandeur')
    return render_template('demandeur.html', role=role)

@app.route('/superviseur.html')
def superviseur():
    role = session.get('role', 'superviseur')
    return render_template('superviseur.html', role=role)

@app.route('/popups/<popup_name>')
def popup_file(popup_name):
    role = session.get('role', 'demandeur')
    return render_template(f'popups/{popup_name}', role=role)

@app.route('/api/demandes/purge', methods=['POST'])
def purge_demandes():
    if not session.get('role') == 'superviseur':
        return jsonify({'error': 'Accès refusé'}), 403
    data = request.get_json()
    ids = data.get('ids', [])
    if not ids:
        return jsonify({'error': 'Aucune fiche à supprimer'}), 400
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    qmarks = ','.join('?' for _ in ids)
    c.execute(f"DELETE FROM demandes WHERE id IN ({qmarks})", ids)
    conn.commit()
    conn.close()
    return jsonify({'ok': True})
@app.route('/api/export-fiches')
def export_fiches():
    import sqlite3
    import pandas as pd
    import io
    con = sqlite3.connect("site-maintenance.db")
    df = pd.read_sql_query("SELECT * FROM demandes", con)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Fiches')
    output.seek(0)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="fiches.xlsx"
    )
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
