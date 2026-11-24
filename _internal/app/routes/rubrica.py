from __future__ import annotations
import csv as csv_mod
import io as io_mod
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string, Response
from datetime import datetime, timedelta
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data

bp = Blueprint('rubrica', __name__, url_prefix='/api/rubrica')


"""
Route per rubrica.
ATTENZIONE: gli handler qui sotto usano `@app.route` direttamente.
Devi avvolgerli in `def register(app):` oppure importare `app` da `app/__init__.py`.
Vedi REPORT.md.
"""

from flask import request, jsonify, render_template_string
from datetime import datetime

# Alias di lettura per il dizionario globale
dati = storage.get_dati()

@bp.route('', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_rubrica():
    dati.setdefault('rubrica', [])
    if request.method == 'GET':
        return jsonify(storage.get_dati()['rubrica'])
    if request.method == 'POST':
        try:
            c = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        c['id'] = _nuovo_id()
        storage.get_dati()['rubrica'].append(c)
        storage.salva()
        return jsonify({'success': True, 'id': c['id']})
    if request.method == 'PUT':
        try:
            c = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        for i, x in enumerate(storage.get_dati()['rubrica']):
            if x.get('id') == c.get('id'):
                storage.get_dati()['rubrica'][i] = c
                storage.salva()
                return jsonify({'success': True})
        return jsonify({'success': False}), 404
    if request.method == 'DELETE':
        id_del = request.args.get('id', type=int)
        storage.get_dati()['rubrica'] = [x for x in storage.get_dati()['rubrica'] if x.get('id') != id_del]
        storage.salva()
        return jsonify({'success': True})


@bp.route('/import', methods=['POST'])
@login_required
def api_rubrica_import():
    if 'file' not in request.files:
        return jsonify({'success': False}), 400
    f = request.files['file']
    try:
        contenuto = f.read().decode('utf-8', errors='replace')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    prima_riga = contenuto.split('\n', 1)[0]
    delim = ';' if prima_riga.count(';') >= prima_riga.count(',') else ','
    reader = csv_mod.DictReader(io_mod.StringIO(contenuto), delimiter=delim)
    n = 0
    for row in reader:
        riga = {(k or '').strip().lower(): (v or '').strip() for k, v in row.items()}
        nome = riga.get('nome') or ''
        tel = riga.get('telefono') or riga.get('tel') or ''
        if not nome and not tel:
            continue
        storage.get_dati()['rubrica'].append({
            'id': _nuovo_id(), 'nome': nome, 'telefono': tel,
            'email': riga.get('email') or '', 'scuola': riga.get('scuola') or '',
            'ruolo': riga.get('ruolo') or '', 'note': riga.get('note') or '',
            'fonte': 'import_csv'
        })
        n += 1
    storage.salva()
    return jsonify({'success': True, 'importati': n})


@bp.route('/export')
@login_required
def api_rubrica_export():
    buf = io_mod.StringIO()
    w = csv_mod.writer(buf, delimiter=';')
    w.writerow(['nome', 'telefono', 'email', 'scuola', 'ruolo', 'note'])
    for c in dati.get('rubrica', []):
        w.writerow([c.get('nome',''), c.get('telefono',''), c.get('email',''),
                    c.get('scuola',''), c.get('ruolo',''), c.get('note','')])
    return Response(buf.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename="rubrica.csv"'})