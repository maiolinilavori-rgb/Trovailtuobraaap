"""Route per la home page: foto hero personalizzata."""
from __future__ import annotations
import os
import uuid
from flask import Blueprint, request, jsonify, send_from_directory
from app import storage
from app.auth import login_required

bp = Blueprint('home', __name__, url_prefix='/api/home')

EXT_CONSENTITE = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
DIM_MAX_FILE = 10 * 1024 * 1024  # 10 MB


def _cartella_home():
    """Ritorna (e crea) la cartella dove salvare la foto hero."""
    base = str(DATA_DIR / 'uploads' / 'home')
    if not os.path.exists(base):
        os.makedirs(base, exist_ok=True)
    return base


def _estrai_estensione(filename):
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext not in EXT_CONSENTITE:
        return None
    return ext


@bp.route('/foto', methods=['GET'])
@login_required
def api_get_foto():
    """Ritorna il nome del file della foto hero corrente (o null)."""
    d = storage.get_dati()
    filename = d.get('home_foto')
    if filename:
        cartella = _cartella_home()
        percorso = os.path.join(cartella, filename)
        if os.path.exists(percorso):
            return jsonify({'success': True, 'foto': filename})
    return jsonify({'success': True, 'foto': None})


@bp.route('/foto', methods=['POST'])
@login_required
def api_upload_foto():
    """Carica una nuova foto hero (sostituisce quella vecchia)."""
    if 'foto' not in request.files:
        return jsonify({'success': False, 'error': 'Nessun file ricevuto'}), 400

    f = request.files['foto']
    if not f or not f.filename:
        return jsonify({'success': False, 'error': 'File vuoto'}), 400

    ext = _estrai_estensione(f.filename)
    if not ext:
        return jsonify({'success': False, 'error': 'Formato non supportato (usa JPG, PNG, WEBP o SVG)'}), 400

    # Controllo dimensione
    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(0)
    if size > DIM_MAX_FILE:
        return jsonify({'success': False, 'error': f'File troppo grande ({size // 1024 // 1024} MB, max 10 MB)'}), 400

    cartella = _cartella_home()

    # Elimina la foto vecchia
    d = storage.get_dati()
    vecchia = d.get('home_foto')
    if vecchia:
        percorso_vecchio = os.path.join(cartella, vecchia)
        try:
            if os.path.exists(percorso_vecchio):
                os.remove(percorso_vecchio)
        except Exception:
            pass

    # Salva la nuova
    nome = f"home_{uuid.uuid4().hex[:12]}{ext}"
    percorso = os.path.join(cartella, nome)
    try:
        f.save(percorso)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Errore salvataggio: {e}'}), 500

    d['home_foto'] = nome
    storage.salva()

    return jsonify({'success': True, 'foto': nome})


@bp.route('/foto', methods=['DELETE'])
@login_required
def api_delete_foto():
    """Rimuove la foto hero personalizzata (torna al logo SVG)."""
    d = storage.get_dati()
    vecchia = d.get('home_foto')
    if vecchia:
        cartella = _cartella_home()
        percorso = os.path.join(cartella, vecchia)
        try:
            if os.path.exists(percorso):
                os.remove(percorso)
        except Exception:
            pass
        d['home_foto'] = None
        storage.salva()
    return jsonify({'success': True})


@bp.route('/file/<path:filename>', methods=['GET'])
def api_serve(filename):
    """Serve il file della foto hero."""
    cartella = _cartella_home()
    if '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({'success': False, 'error': 'Nome file non valido'}), 400
    percorso = os.path.join(cartella, filename)
    if not os.path.exists(percorso):
        return jsonify({'success': False, 'error': 'File non trovato'}), 404
    return send_from_directory(cartella, filename)
