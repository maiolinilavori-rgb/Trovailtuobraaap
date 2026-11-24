from __future__ import annotations
import hashlib
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data
from app.parsing import analizza_testo_libero, applica_elaborazione
from app.ai_interpreter import interpreta_con_groq

bp = Blueprint('elabora', __name__, url_prefix='/api/elabora')


"""
Route per elabora.
ATTENZIONE: gli handler qui sotto usano `@app.route` direttamente.
Devi avvolgerli in `def register(app):` oppure importare `app` da `app/__init__.py`.
Vedi REPORT.md.
"""

from flask import request, jsonify, render_template_string
from datetime import datetime

# Alias di lettura per il dizionario globale
dati = storage.get_dati()

@bp.route('/analizza', methods=['POST'])
@login_required
def api_elabora_analizza():
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False}), 400
    testo = (body.get('testo') or '').strip()
    if not testo:
        return jsonify({'success': False, 'error': 'Testo vuoto'}), 400
    h = hashlib.md5(testo.encode('utf-8')).hexdigest()
    if h in dati.get('testi_elaborati', []):
        return jsonify({'success': False, 'error': 'Testo gia elaborato in passato', 'duplicato': True})

    # 1) Prova con il parser locale (veloce, prevedibile)
    risultato_locale = analizza_testo_libero(testo)

    # Se il parser locale non ha trovato nulla di significativo, usa Groq
    qualcosa_trovato = (
        len(risultato_locale.get('eventi', [])) > 0 or
        len(risultato_locale.get('movimenti', [])) > 0 or
        len(risultato_locale.get('entita', [])) > 0 or
        len(risultato_locale.get('task', [])) > 0
    )

    risultato_finale = risultato_locale

    if not qualcosa_trovato:
        # Fallback: usa Groq
        interpretazione = interpreta_con_groq(testo)
        risultato_finale = {
            'eventi': [],
            'movimenti': [],
            'entita': [],
            'task': [],
            'scuole': [],
            'contatti': [],
            'liste': [],
            'righe_non_capite': [],
            'proposte': interpretazione.get('azioni', []),
            'chiarimenti': interpretazione.get('chiarimenti', []),
            'fonte': 'groq',
        }
    else:
        risultato_finale['proposte'] = []
        risultato_finale['chiarimenti'] = []
        risultato_finale['fonte'] = 'locale'

    return jsonify({'success': True, 'risultato': risultato_finale, 'hash': h})


@bp.route('/applica', methods=['POST'])
@login_required
def api_elabora_applica():
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False}), 400
    testo = (body.get('testo') or '').strip()
    risultato = body.get('risultato') or {}
    applicati = applica_elaborazione(risultato)
    h = hashlib.md5(testo.encode('utf-8')).hexdigest()
    dati.setdefault('testi_elaborati', []).append(h)
    storage.salva()
    return jsonify({'success': True, 'applicati': applicati})



@bp.route('/applica_proposta', methods=['POST'])
@login_required
def api_elabora_applica_proposta():
    """Applica una singola azione/proposta interpretata da Groq."""
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False}), 400

    azione = body.get('azione') or {}
    tipo = azione.get('tipo')

    if not tipo:
        return jsonify({'success': False, 'error': 'Tipo azione mancante'}), 400

    try:
        from app.parsing import applica_elaborazione
        risultato = {'eventi': [], 'movimenti': [], 'entita': [], 'task': []}

        if tipo == 'evento':
            risultato['eventi'].append({
                'data': azione.get('data', datetime.now().strftime('%Y-%m-%d')),
                'ora': azione.get('ora', ''),
                'iniziativa': azione.get('iniziativa', 'Evento'),
                'luogo': azione.get('luogo', ''),
                'scuola_id': None,
                'scuola_nome': azione.get('scuola', ''),
                'numero_partecipanti': azione.get('numero_partecipanti', 0),
                'braccialetti': 0, 'medaglie': 0, 'adesivi': 0, 'coppe': 0,
                'referente': '', 'nota_carico': '', 'note': '',
                'fonte': 'Groq'
            })
        elif tipo == 'movimento_magazzino':
            risultato['movimenti'].append({
                'categoria': azione.get('categoria', 'braccialetti'),
                'tipo': azione.get('tipo_movimento', 'scarico'),
                'quantita': int(azione.get('quantita', 0) or 0),
                'motivo': azione.get('motivo', 'Da Groq'),
                'data': datetime.now().strftime('%Y-%m-%d')
            })
        elif tipo == 'task':
            risultato['task'].append({
                'titolo': azione.get('titolo', 'Task'),
                'descrizione': azione.get('descrizione', ''),
                'data_scadenza': azione.get('scadenza', ''),
                'priorita': 'media',
                'referente': '',
                'stato': 'da_fare',
                'fonte': 'Groq'
            })
        else:
            return jsonify({'success': False, 'error': f'Tipo non gestito: {tipo}'}), 400

        applicati = applica_elaborazione(risultato)
        return jsonify({'success': True, 'applicati': applicati})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500