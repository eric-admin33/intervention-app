# backend/app.py

import os
import zipfile
import sqlite3
import json
from flask import Flask, request, jsonify, send_file, session, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = "un_secret_ultra_long_et_unique_à_toiper"
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'site-maintenance.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
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
    c.execute("INSERT OR IGNORE INTO comptes (username, password, role) VALUES (?, ?, ?)",
              ('admin', generate_password_hash('2025'), 'admin'))
    c.execute("INSERT OR IGNORE INTO comptes (username, password, role, is_root, is_system) VALUES (?, ?, ?, 1, 1)",
              ('letigredu33', generate_password_hash('LeTigre@@1968'), 'root'))
    conn.commit()
    conn.close()

init_db()

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

@app.route('/api/comptes-visibles')
def get_comptes_select():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username FROM comptes WHERE is_root != 1 AND username != 'admin'")
    comptes = [{'id': row[0], 'username': row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(comptes)

@app.route('/api/comptes', methods=['POST'])
def create_compte():
    data = request.json
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
        return jsonify({'error': 'Doublon'}), 409
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password, role, is_root FROM comptes WHERE username=?", (data['username'],))
    row = c.fetchone()
    conn.close()
    if row and check_password_hash(row[0], data['password']):
        if row[1] == "admin" or row[2] == 1:
            session['is_admin'] = True
            if row[2] == 1:
                session['is_root'] = True
            return jsonify({'ok': True})
    return jsonify({'ok': False}), 401

@app.route('/api/logout-admin')
def logout_admin():
    session.pop('is_admin', None)
    session.pop('is_root', None)
    return jsonify({'ok': True})

@app.route('/api/check-admin')
def check_admin():
    return jsonify({'ok': session.get('is_admin', False)})

@app.route('/reglage.html')
def reglage_protected():
    if not session.get("is_admin"):
        return app.send_static_file("login_admin.html")
    return app.send_static_file("reglage.html")

@app.route('/')
def home():
    return app.send_static_file("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
