"""Route per gestione foto evento."""
from __future__ import annotations
import os
import re
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
from app import storage
from app.config import DATA_DIR
from app.auth import login_required
from app.utils import _intero

bp = Blueprint('foto', __name__, url_prefix='/api/foto')

# Estensioni consentite
EXT_CONSENTITE = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.heif', '.mp4', '.mov', '.webm', '.avi', '.mkv', '.m4v'}
DIM_MAX_FILE = 200 * 1024 * 1024  # 50 MB (video)


def _cartella_foto():
    """Ritorna (e crea) la cartella dove salvare le foto."""
    base = str(DATA_DIR / 'uploads' / 'eventi')
    if not os.path.exists(base):
        os.makedirs(base, exist_ok=True)
    return base


def _estrai_estensione(filename):
    """Estrae l'estensione in minuscolo, validando."""
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext not in EXT_CONSENTITE:
        return None
    return ext


def _nome_sicuro(nome):
    """Genera un nome file sicuro con UUID."""
    ext = _estrai_estensione(nome)
    if not ext:
        return None
    # base = 'evento_<uuid>.<ext>'
    return f"evento_{uuid.uuid4().hex[:16]}{ext}"


# ============================================================
# UPLOAD
# ============================================================
@bp.route('/upload', methods=['POST'])
@login_required
def api_upload():
    """Carica una o piu' foto per un evento."""
    evento_id = request.form.get('evento_id')
    if not evento_id:
        return jsonify({'success': False, 'error': 'evento_id mancante'}), 400
    evento_id = _intero(evento_id)

    if 'foto' not in request.files:
        return jsonify({'success': False, 'error': 'Nessun file ricevuto (campo "foto")'}), 400

    files = request.files.getlist('foto')
    if not files:
        return jsonify({'success': False, 'error': 'Nessun file da caricare'}), 400

    cartella = _cartella_foto()
    caricate = []
    errori = []

    for f in files:
        if not f or not f.filename:
            continue
        nome_sicuro = _nome_sicuro(f.filename)
        if not nome_sicuro:
            errori.append(f'{f.filename}: formato non supportato')
            continue

        # Controllo dimensione
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0)
        if size > DIM_MAX_FILE:
            errori.append(f'{f.filename}: file troppo grande ({size // 1024 // 1024} MB, max 200 MB)')
            continue

        percorso = os.path.join(cartella, nome_sicuro)
        try:
            f.save(percorso)
            caricate.append(nome_sicuro)
        except Exception as e:
            errori.append(f'{f.filename}: errore salvataggio ({e})')

    if not caricate and errori:
        return jsonify({
            'success': False,
            'error': 'Nessuna foto caricata. ' + '; '.join(errori[:3]),
            'errori': errori
        }), 400

    # Aggiorna l'evento con i percorsi delle foto
    trovato = False
    for e in storage.get_dati().get('eventi', []):
        if e.get('id') == evento_id:
            e.setdefault('foto', [])
            e['foto'].extend(caricate)
            trovato = True
            break

    if not trovato:
        # Rimuovi i file orfani
        for nome in caricate:
            try:
                os.remove(os.path.join(cartella, nome))
            except Exception:
                pass
        return jsonify({'success': False, 'error': 'Evento non trovato'}), 404

    storage.salva()

    return jsonify({
        'success': True,
        'caricate': caricate,
        'errori': errori,
        'totale_foto': len(caricate),
    })


# ============================================================
# DELETE
# ============================================================
@bp.route('/elimina', methods=['POST'])
@login_required
def api_elimina():
    """Elimina una foto da un evento."""
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False, 'error': 'JSON non valido'}), 400

    evento_id = _intero(body.get('evento_id'))
    nome_file = (body.get('filename') or '').strip()

    if not evento_id or not nome_file:
        return jsonify({'success': False, 'error': 'evento_id e filename richiesti'}), 400

    # Rimuovi dall'evento
    trovato = False
    for e in storage.get_dati().get('eventi', []):
        if e.get('id') == evento_id:
            foto = e.get('foto', [])
            if nome_file in foto:
                foto.remove(nome_file)
                e['foto'] = foto
                trovato = True
            break

    if not trovato:
        return jsonify({'success': False, 'error': 'Foto non trovata nell\'evento'}), 404

    # Rimuovi dal filesystem
    cartella = _cartella_foto()
    percorso = os.path.join(cartella, nome_file)
    try:
        if os.path.exists(percorso):
            os.remove(percorso)
    except Exception as e:
        # Il file potrebbe essere gia' stato rimosso
        pass

    storage.salva()

    return jsonify({'success': True})


# ============================================================
# SERVE I FILE
# ============================================================
@bp.route('/file/<path:filename>', methods=['GET'])
def api_serve(filename):
    """Serve un file immagine."""
    cartella = _cartella_foto()
    # Sicurezza: previeni path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({'success': False, 'error': 'Nome file non valido'}), 400

    percorso = os.path.join(cartella, filename)
    if not os.path.exists(percorso):
        return jsonify({'success': False, 'error': 'File non trovato'}), 404

    return send_from_directory(cartella, filename)
# ============================================================
# DIDASCALIA + TAG PER MEDIA
# ============================================================
@bp.route('/aggiorna', methods=['POST'])
@login_required
def api_aggiorna_media():
    """Aggiorna didascalia e tag di un media (foto o video).
    Supporta sia stringhe che oggetti nel DB."""
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False}), 400

    evento_id = _intero(body.get('evento_id'))
    filename = body.get('filename')
    didascalia = (body.get('didascalia') or '').strip()
    tag = body.get('tag') or []

    if isinstance(tag, str):
        tag = [t.strip() for t in tag.split(',') if t.strip()]

    for e in storage.get_dati().get('eventi', []):
        if e.get('id') != evento_id:
            continue

        # Cerca in foto
        foto_list = e.get('foto', [])
        for i, media in enumerate(foto_list):
            if isinstance(media, dict) and media.get('file') == filename:
                media['didascalia'] = didascalia
                media['tag'] = tag
                storage.salva()
                return jsonify({'success': True})
            elif isinstance(media, str) and media == filename:
                # Converti stringa in oggetto
                foto_list[i] = {'file': filename, 'didascalia': didascalia, 'tag': tag}
                storage.salva()
                return jsonify({'success': True})

        # Cerca in video
        video_list = e.get('video', [])
        for i, media in enumerate(video_list):
            if isinstance(media, dict) and media.get('file') == filename:
                media['didascalia'] = didascalia
                media['tag'] = tag
                storage.salva()
                return jsonify({'success': True})
            elif isinstance(media, str) and media == filename:
                video_list[i] = {'file': filename, 'didascalia': didascalia, 'tag': tag}
                storage.salva()
                return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'Media non trovato'}), 404

@bp.route('/galleria', methods=['GET'])
@login_required
def api_galleria():
    """Ritorna tutti i media di tutti gli eventi, con filtri."""
    tag_filtro = (request.args.get('tag') or '').lower().strip()
    tipo_filtro = request.args.get('tipo', '')  # 'foto', 'video', ''

    eventi = storage.get_dati().get('eventi', [])
    risultato = []

    for e in eventi:
        for media in (e.get('foto') or []):
            if isinstance(media, str):
                media = {'file': media, 'didascalia': '', 'tag': []}
            if isinstance(media, dict) and media.get('file'):
                if tipo_filtro and tipo_filtro != 'foto': continue
                if tag_filtro and tag_filtro not in [t.lower() for t in media.get('tag', [])]: continue
                risultato.append({
                    'evento_id': e.get('id'),
                    'evento': e.get('iniziativa'),
                    'data': e.get('data'),
                    'file': media.get('file'),
                    'didascalia': media.get('didascalia', ''),
                    'tag': media.get('tag', []),
                    'tipo': 'foto',
                })

        for media in (e.get('video') or []):
            if isinstance(media, dict):
                if tipo_filtro and tipo_filtro != 'video': continue
                if tag_filtro and tag_filtro not in [t.lower() for t in media.get('tag', [])]: continue
                risultato.append({
                    'evento_id': e.get('id'),
                    'evento': e.get('iniziativa'),
                    'data': e.get('data'),
                    'file': media.get('file'),
                    'didascalia': media.get('didascalia', ''),
                    'tag': media.get('tag', []),
                    'tipo': 'video',
                })

    risultato.sort(key=lambda x: x.get('data') or '', reverse=True)
    return jsonify({'success': True, 'media': risultato, 'totale': len(risultato)})
