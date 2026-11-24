from __future__ import annotations
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data

def _sincronizza_referente(scuola, azione='upsert'):
    """Sincronizza il referente della scuola con la rubrica."""
    from datetime import datetime
    ref = (scuola.get('referente') or '').strip()
    if not ref:
        return
    contatti = storage.get_dati().setdefault('rubrica', [])
    # Cerca contatto con lo stesso nome E collegato a questa scuola
    esistente = None
    for c in contatti:
        if (c.get('nome') or '').lower().strip() == ref.lower() and c.get('scuola_id') == scuola.get('id'):
            esistente = c
            break
    if esistente:
        # Aggiorna telefono/email
        esistente['telefono'] = scuola.get('telefono', '')
        esistente['email'] = scuola.get('email', '')
        esistente['note'] = 'Referente di ' + scuola.get('nome', '')
    else:
        # Crea nuovo contatto
        from app.utils import _nuovo_id
        contatti.append({
            'id': _nuovo_id(),
            'nome': ref,
            'telefono': scuola.get('telefono', ''),
            'email': scuola.get('email', ''),
            'scuola_id': scuola.get('id'),
            'ruolo': 'Referente',
            'note': 'Referente di ' + scuola.get('nome', ''),
            'fonte': 'Sync scuola',
        })

bp = Blueprint('scuole', __name__, url_prefix='/api/scuole')


"""
Route per scuole.
ATTENZIONE: gli handler qui sotto usano `@app.route` direttamente.
Devi avvolgerli in `def register(app):` oppure importare `app` da `app/__init__.py`.
Vedi REPORT.md.
"""

from flask import request, jsonify, render_template_string
from datetime import datetime

@bp.route('', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_scuole():
    if request.method == 'GET':
        return jsonify(storage.get_dati()['scuole'])
    if request.method == 'POST':
        try:
            nuova = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        nome = (nuova.get('nome') or '').strip().upper()
        if not nome:
            return jsonify({'success': False}), 400
        for s in storage.get_dati()['scuole']:
            if s['nome'].upper() == nome:
                return jsonify({'success': True, 'id': s['id']})
        nuova['nome'] = nome
        nuova['id'] = _nuovo_id()
        storage.get_dati()['scuole'].append(nuova)
        storage.salva()
        return jsonify({'success': True, 'id': nuova['id']})
    if request.method == 'PUT':
        try:
            m = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        for i, s in enumerate(storage.get_dati()['scuole']):
            if s.get('id') == m.get('id'):
                storage.get_dati()['scuole'][i] = m
                storage.salva()
                return jsonify({'success': True})
        return jsonify({'success': False}), 404
    if request.method == 'DELETE':
        id_del = request.args.get('id', type=int)
        for e in storage.get_dati()['eventi']:
            if e.get('scuola_id') == id_del:
                e['scuola_id'] = None
        storage.get_dati()['scuole'] = [s for s in storage.get_dati()['scuole'] if s.get('id') != id_del]
        storage.salva()
        return jsonify({'success': True})



@bp.route('/scuole/sposta-altro', methods=['POST'])
@login_required
def api_scuola_to_altro():
    b = request.get_json(silent=True) or {}
    sid = str(b.get('scuola_id') or '')
    d = storage.get_dati()
    scuole = d.get('scuole', [])
    idx = next((i for i, s in enumerate(scuole) if str(s.get('id')) == sid), None)
    if idx is None:
        return jsonify({'success': False, 'error': 'Scheda non trovata'}), 404
    sc = scuole.pop(idx)
    nome = (sc.get('nome') or '').strip()
    spostati = 0
    for ev in d.get('eventi', []):
        if str(ev.get('scuola_id') or '') == sid:
            ev['scuola_id'] = None
            if not ev.get('luogo'):
                ev['luogo'] = nome
            spostati += 1
    storage.salva()
    return jsonify({'success': True, 'nome': nome, 'eventi_spostati': spostati})


@bp.route('/altro/sposta-scuola', methods=['POST'])
@login_required
def api_altro_to_scuola():
    b = request.get_json(silent=True) or {}
    eid = str(b.get('evento_id') or '')
    d = storage.get_dati()
    ev = next((e for e in d.get('eventi', []) if str(e.get('id')) == eid), None)
    if not ev:
        return jsonify({'success': False, 'error': 'Evento non trovato'}), 404
    nome = (b.get('nome_scuola') or ev.get('luogo') or ev.get('iniziativa') or 'Nuova Scuola').strip()
    scuole = d.setdefault('scuole', [])
    sc = next((s for s in scuole if (s.get('nome') or '').strip().lower() == nome.lower()), None)
    if not sc:
        sc = {'id': _nuovo_id(), 'nome': nome, 'tipo': 'Primaria / IC', 'referente': '', 'telefono': '', 'email': '', 'note': 'Creata da evento ALTRO'}
        scuole.append(sc)
    ev['scuola_id'] = sc['id']
    storage.salva()
    return jsonify({'success': True, 'scuola': sc['nome']})
