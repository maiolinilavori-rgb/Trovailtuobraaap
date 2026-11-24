from __future__ import annotations
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data

bp = Blueprint('note_vocali', __name__, url_prefix='/api/note_vocali')


"""
Route per note_vocali.
ATTENZIONE: gli handler qui sotto usano `@app.route` direttamente.
Devi avvolgerli in `def register(app):` oppure importare `app` da `app/__init__.py`.
Vedi REPORT.md.
"""

from flask import request, jsonify, render_template_string
from datetime import datetime

# Alias di lettura per il dizionario globale
dati = storage.get_dati()

@bp.route('', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_note_vocali():
    dati.setdefault('note_vocali', [])
    if request.method == 'GET':
        # Ritorna solo i metadati (senza il blob audio, che e' troppo grande)
        return jsonify([{
            'id': n.get('id'),
            'data': n.get('data'),
            'durata': n.get('durata'),
            'trascrizione': n.get('trascrizione'),
            'elaborata': n.get('elaborata', False),
        } for n in storage.get_dati()['note_vocali']])

    if request.method == 'POST':
        # Riceve audio + trascrizione
        file = request.files.get('audio')
        trascrizione = request.form.get('trascrizione', '')
        durata = request.form.get('durata', '0')
        if not file:
            return jsonify({'success': False, 'error': 'Nessun audio'}), 400
        contenuto_b64 = base64.b64encode(file.read()).decode('utf-8')
        nota = {
            'id': _nuovo_id(),
            'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'durata': float(durata) if durata else 0,
            'trascrizione': trascrizione,
            'audio_b64': contenuto_b64,
            'mimetype': file.mimetype or 'audio/wav',
            'elaborata': False,
        }
        storage.get_dati()['note_vocali'].append(nota)
        storage.salva()
        return jsonify({'success': True, 'id': nota['id']})

    if request.method == 'DELETE':
        id_del = request.args.get('id', type=int)
        storage.get_dati()['note_vocali'] = [n for n in storage.get_dati()['note_vocali'] if n.get('id') != id_del]
        storage.salva()
        return jsonify({'success': True})


@bp.route('/<int:nota_id>/audio')
@login_required
def api_nota_vocale_audio(nota_id):
    """Ritorna il blob audio di una nota vocale."""
    for n in dati.get('note_vocali', []):
        if n.get('id') == nota_id:
            return jsonify({'success': True, 'audio_b64': n.get('audio_b64'),
                            'mimetype': n.get('mimetype', 'audio/wav')})
    return jsonify({'success': False, 'error': 'Nota non trovata'}), 404


@bp.route('/<int:nota_id>/elabora', methods=['POST'])
@login_required
def api_nota_vocale_elabora(nota_id):
    """Elabora la trascrizione di una nota vocale."""
    nota = next((n for n in dati.get('note_vocali', []) if n.get('id') == nota_id), None)
    if not nota:
        return jsonify({'success': False, 'error': 'Nota non trovata'}), 404
    testo = (nota.get('trascrizione') or '').strip()
    if not testo:
        return jsonify({'success': False, 'error': 'Trascrizione vuota'}), 400
    risultato = interpreta_comando_vocale(testo)
    esito = _esegui_risultato_vocale(risultato, testo)
    nota['elaborata'] = True
    storage.salva()
    return jsonify(esito)

