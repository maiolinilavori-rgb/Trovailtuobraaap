"""Route per l'assistente conversazionale."""
from __future__ import annotations
from flask import Blueprint, request, jsonify
from app.auth import login_required
from app.assistente import chatta

bp = Blueprint('assistente', __name__, url_prefix='/api/assistente')


@bp.route('/chat', methods=['POST'])
@login_required
def api_chat():
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False, 'error': 'JSON non valido'}), 400

    messaggi = body.get('messaggi') or []
    if not isinstance(messaggi, list) or not messaggi:
        return jsonify({'success': False, 'error': 'Nessun messaggio'}), 400

    risultato = chatta(messaggi)
    return jsonify(risultato)

# ============================================================
# DASHBOARD - Genera riepiloghi locali (zero token Groq)
# ============================================================
from app.dashboard import (
    dashboard_panoramica, dashboard_magazzino,
    dashboard_task, dashboard_eventi, dashboard_bilancio
)

_DASHBOARD_FUNZIONI = {
    'panoramica': dashboard_panoramica,
    'magazzino': dashboard_magazzino,
    'task': dashboard_task,
    'eventi': dashboard_eventi,
    'bilancio': dashboard_bilancio,
}


@bp.route('/dashboard/<tipo>', methods=['GET'])
@login_required
def api_dashboard(tipo):
    """Ritorna un riepilogo formattato per il tipo richiesto."""
    fn = _DASHBOARD_FUNZIONI.get(tipo)
    if not fn:
        return jsonify({'success': False, 'error': f'Tipo non valido: {tipo}'}), 400

    try:
        testo = fn()
        return jsonify({'success': True, 'tipo': tipo, 'testo': testo})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500