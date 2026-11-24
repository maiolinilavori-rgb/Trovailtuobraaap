"""Route per gestione anno."""
from __future__ import annotations
from flask import Blueprint, jsonify
from app.auth import login_required
from app.anno import anni_disponibili, storico_anno, totali_globali

bp = Blueprint('anno', __name__, url_prefix='/api/anno')


@bp.route('/lista', methods=['GET'])
@login_required
def api_anni():
    return jsonify({'success': True, 'anni': anni_disponibili()})


@bp.route('/storico/<int:anno>', methods=['GET'])
@login_required
def api_storico(anno):
    try:
        return jsonify({'success': True, 'dati': storico_anno(anno)})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/globali', methods=['GET'])
@login_required
def api_globali():
    return jsonify({'success': True, 'totali': totali_globali()})