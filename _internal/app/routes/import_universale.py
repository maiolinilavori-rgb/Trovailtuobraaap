# -*- coding: utf-8 -*-
"""Route per l'import universale MEMORANDIA.

Endpoint:
    POST /api/import/<tipo>/preview  -> upload + dry-run
    POST /api/import/<tipo>/apply    -> applica import
    GET  /api/import/<tipo>/template -> scarica CSV esempio

Tipi supportati: eventi, scuole, rubrica, entita, inventario,
                 movimenti, uscite, entrate, task, liste
"""
from __future__ import annotations
from flask import Blueprint, request, jsonify, Response
from app.auth import login_required
from app.import_universale import (
    TIPI_SUPPORTATI, parse_file, mapping_automatico,
    valida, applica, template_csv,
)

bp = Blueprint('import_universale', __name__, url_prefix='/api/import')


def _valida_tipo(tipo):
    """Verifica che il tipo sia supportato. Ritorna (ok, errore)."""
    if tipo not in TIPI_SUPPORTATI:
        supportati = ', '.join(TIPI_SUPPORTATI.keys())
        return False, f'Tipo non supportato: {tipo}. Supportati: {supportati}'
    return True, None


@bp.route('/<tipo>/preview', methods=['POST'])
@login_required
def api_import_preview(tipo):
    """Upload file + dry-run. Ritorna mapping, anteprima, conteggi."""
    ok, err = _valida_tipo(tipo)
    if not ok:
        return jsonify({'success': False, 'error': err}), 400

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Nessun file caricato'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'error': 'Nome file vuoto'}), 400

    try:
        file_bytes = file.read()
        headers, rows = parse_file(file_bytes, file.filename)
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Errore lettura file: {e}'}), 500

    if not headers:
        return jsonify({'success': False, 'error': 'File vuoto o senza intestazioni'}), 400

    try:
        mapping = mapping_automatico(tipo, headers)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Errore mapping: {e}'}), 500

    try:
        risultato = valida(tipo, rows, mapping, strategy='skip')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Errore validazione: {e}'}), 500

    anteprima = [r['record'] for r in risultato['valide'][:5]]

    return jsonify({
        'success': True,
        'tipo': tipo,
        'filename': file.filename,
        'headers': headers,
        'mapping': mapping,
        'totale_righe': risultato['totale'],
        'valide': len(risultato['valide']),
        'errori': risultato['errori'],
        'duplicati': [{'riga': d['riga'], 'record': d['record']} for d in risultato['duplicati']],
        'anteprima': anteprima,
        'righe_valide': risultato['valide'],
    })


@bp.route('/<tipo>/apply', methods=['POST'])
@login_required
def api_import_apply(tipo):
    """Applica l'import. Richiede JSON: {righe_valide, strategy}."""
    ok, err = _valida_tipo(tipo)
    if not ok:
        return jsonify({'success': False, 'error': err}), 400

    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False, 'error': 'JSON non valido'}), 400

    righe_valide = body.get('righe_valide', [])
    strategy = body.get('strategy', 'skip')

    if not righe_valide:
        return jsonify({'success': False, 'error': 'Nessuna riga da importare'}), 400

    if strategy not in ('skip', 'update'):
        return jsonify({'success': False, 'error': f'Strategy non valida: {strategy}'}), 400

    try:
        riepilogo = applica(tipo, righe_valide, strategy=strategy)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Errore import: {e}'}), 500

    return jsonify({
        'success': True,
        'tipo': tipo,
        'riepilogo': riepilogo,
    })


@bp.route('/<tipo>/template', methods=['GET'])
@login_required
def api_import_template(tipo):
    """Scarica CSV di esempio per il tipo."""
    ok, err = _valida_tipo(tipo)
    if not ok:
        return jsonify({'success': False, 'error': err}), 400

    try:
        csv_content = template_csv(tipo)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    return Response(
        csv_content,
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename="template_{tipo}.csv"',
        }
    )