from __future__ import annotations
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string, current_app
from datetime import datetime, timedelta
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data
from app.export_helpers import _scrivi_foglio_excel, _dati_per_sezione
import os
import io as io_mod
import csv as csv_mod
import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

bp = Blueprint('esporta', __name__, url_prefix='/api')


"""
Route per esporta.
ATTENZIONE: gli handler qui sotto usano `@app.route` direttamente.
Devi avvolgerli in `def register(app):` oppure importare `app` da `app/__init__.py`.
Vedi REPORT.md.
"""

from flask import request, jsonify, render_template_string
from datetime import datetime

# Alias di lettura per il dizionario globale
dati = storage.get_dati()

@bp.route('/export/backup')
@login_required
def api_export_backup():
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    r = current_app.response_class(json.dumps(dati, indent=2, default=str, ensure_ascii=False),
                           mimetype='application/json')
    r.headers['Content-Disposition'] = f'attachment; filename="braaap_backup_{ts}.json"'
    return r


@bp.route('/esporta/<sezione>.<formato>')
@login_required
def api_esporta(sezione, formato):
    """Esporta una sezione in excel/csv/json. Param opzionale: ?anno=2025"""
    filtro_anno = request.args.get('anno', type=int)
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    nome_file = f'braaap_{sezione}_{ts}'

    if sezione == 'tutto':
        # Excel multi-foglio con tutte le sezioni
        wb = Workbook()
        wb.remove(wb.active)
        for sez in ['eventi','scuole','rubrica','task','magazzino','inventario','entita','liste','portafoglio']:
            intest, righe = _dati_per_sezione(sez, filtro_anno)
            ws = wb.create_sheet(title=sez.capitalize())
            _scrivi_foglio_excel(ws, intest, righe)
        buf = io_mod.BytesIO()
        wb.save(buf)
        buf.seek(0)
        r = current_app.response_class(buf.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        r.headers['Content-Disposition'] = f'attachment; filename="{nome_file}.xlsx"'
        return r

    intest, righe = _dati_per_sezione(sezione, filtro_anno)

    if formato == 'excel':
        wb = Workbook()
        ws = wb.active
        ws.title = sezione.capitalize()
        _scrivi_foglio_excel(ws, intest, righe)
        buf = io_mod.BytesIO()
        wb.save(buf)
        buf.seek(0)
        r = current_app.response_class(buf.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        r.headers['Content-Disposition'] = f'attachment; filename="{nome_file}.xlsx"'
        return r

    if formato == 'csv':
        buf = io_mod.StringIO()
        w = csv_mod.writer(buf, delimiter=';')
        w.writerow(intest)
        for riga in righe:
            w.writerow(riga)
        r = current_app.response_class('\ufeff' + buf.getvalue(), mimetype='text/csv; charset=utf-8')
        r.headers['Content-Disposition'] = f'attachment; filename="{nome_file}.csv"'
        return r

    if formato == 'json':
        payload = {'sezione': sezione, 'esportato_il': datetime.now().isoformat(),
                   'intestazioni': intest,
                   'righe': [dict(zip(intest, r)) for r in righe]}
        r = current_app.response_class(json.dumps(payload, indent=2, ensure_ascii=False, default=str),
                               mimetype='application/json')
        r.headers['Content-Disposition'] = f'attachment; filename="{nome_file}.json"'
        return r

    return jsonify({'success': False, 'error': f'Formato non supportato: {formato}'}), 400

