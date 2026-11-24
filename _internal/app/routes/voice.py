from __future__ import annotations
import os
import tempfile
from flask import Blueprint, request, jsonify
from app.auth import login_required
from app.config import GROQ_API_KEY, GROQ_MODELLO_WHISPER, GROQ_ABILITATO

bp = Blueprint('voice', __name__, url_prefix='/api')


# ============================================================
# TRASCRIZIONE VOCALE - Groq Whisper
# ============================================================
@bp.route('/trascrivi', methods=['POST'])
@login_required
def api_trascrivi():
    if not GROQ_ABILITATO:
        return jsonify({
            'success': False,
            'error': 'GROQ_API_KEY non configurata nel .env'
        }), 500

    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'Campo "audio" mancante.'}), 400

    f = request.files['audio']
    if not f or f.filename == '':
        return jsonify({'success': False, 'error': 'File audio vuoto.'}), 400

    # Salva su file temporaneo
    ext = os.path.splitext(f.filename)[1] or '.webm'
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=ext)
    os.close(tmp_fd)

    try:
        f.save(tmp_path)

        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        with open(tmp_path, 'rb') as audio_file:
            risposta = client.audio.transcriptions.create(
                file=(f.filename, audio_file.read()),
                model=GROQ_MODELLO_WHISPER,
                language='it',
                response_format='json',
            )

        testo = (getattr(risposta, 'text', '') or '').strip()
        if not testo:
            return jsonify({'success': False, 'error': 'Nessuna parola riconosciuta.'}), 200

        # Applica correttore fonetico (zero token)
        testo_corretto = correggi_trascrizione(testo)

        return jsonify({
            'success': True,
            'trascrizione': testo_corretto,
            'trascrizione_originale': testo if testo != testo_corretto else None,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Errore Groq: {e}'}), 500

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ============================================================
# CORRETTORE ORTOGRAFICO
# ============================================================
from app.grammar import correggi_testo
from app.vocabolario import correggi_trascrizione

@bp.route('/correggi', methods=['POST'])
@login_required
def api_correggi():
    dati = request.get_json(silent=True) or {}
    testo = (dati.get('testo') or '').strip()

    if not testo:
        return jsonify({'success': False, 'error': 'Testo vuoto'}), 400

    if len(testo) > 2000:
        return jsonify({'success': False, 'error': 'Testo troppo lungo (max 2000 caratteri)'}), 400

    try:
        corretto = correggi_testo(testo)
        return jsonify({'success': True, 'originale': testo, 'corretto': corretto})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500