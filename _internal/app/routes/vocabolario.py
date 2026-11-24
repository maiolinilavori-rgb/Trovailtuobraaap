"""Route per il vocabolario dinamico."""
from __future__ import annotations
from flask import Blueprint, request, jsonify
from app.auth import login_required
from app.vocabolario import impara, cerca, lista_completa, dimentica, lista_varianti

bp = Blueprint('vocabolario', __name__, url_prefix='/api/vocabolario')


@bp.route('/lista', methods=['GET'])
@login_required
def api_lista():
    return jsonify(lista_completa())


@bp.route('/impara', methods=['POST'])
@login_required
def api_impara():
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False, 'error': 'JSON non valido'}), 400

    parola = (body.get('parola') or '').strip()
    significato = (body.get('significato') or '').strip()

    if not parola or not significato:
        return jsonify({'success': False, 'error': 'Parola e significato richiesti'}), 400

    return jsonify(impara(parola, significato))


@bp.route('/cerca/<parola>', methods=['GET'])
@login_required
def api_cerca(parola):
    return jsonify(cerca(parola))


@bp.route('/dimentica/<parola>', methods=['DELETE'])
@login_required
def api_dimentica(parola):
    return jsonify(dimentica(parola))

@bp.route('/varianti', methods=['GET'])
@login_required
def api_varianti():
    """Ritorna le varianti fonetiche apprese."""
    return jsonify(lista_varianti())