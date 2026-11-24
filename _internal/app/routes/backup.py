"""Route per il backup manuale."""
from __future__ import annotations
import os
import shutil
import time
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file
from app.auth import login_required
from app import storage

bp = Blueprint('backup', __name__, url_prefix='/api/backup')


def _cartella_backup():
    """Ritorna (e crea) la cartella dei backup."""
    from app.config import BACKUP_DIR
    base = str(BACKUP_DIR)
    if not os.path.exists(base):
        os.makedirs(base, exist_ok=True)
    return base


def _percorso_dati():
    """Ritorna il percorso del file dati principale."""
    from app.config import DATA_FILE
    return str(DATA_FILE)


@bp.route('/ora', methods=['POST'])
@login_required
def api_backup_ora():
    """Crea un backup manuale del file dati.
    Lo salva nella cartella di sistema e ritorna il contenuto
    per permettere al frontend di farne una copia aggiuntiva.
    """
    try:
        storage.salva()

        percorso_dati = _percorso_dati()
        if not os.path.exists(percorso_dati):
            return jsonify({
                'success': False,
                'error': 'File dati non trovato. Salva prima un dato qualsiasi.'
            }), 400

        cartella = _cartella_backup()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_file = f'braaap_data_backup_{timestamp}.json'
        destinazione = os.path.join(cartella, nome_file)

        # Copia il file nella cartella di sistema
        shutil.copy2(percorso_dati, destinazione)

        # Leggi il contenuto per restituirlo al frontend
        with open(destinazione, 'r', encoding='utf-8') as f:
            contenuto = f.read()

        size_kb = round(os.path.getsize(destinazione) / 1024, 2)

        return jsonify({
            'success': True,
            'messaggio': 'Backup creato con successo',
            'file': nome_file,
            'percorso': destinazione,
            'dimensione_kb': size_kb,
            'contenuto': contenuto
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Errore durante il backup: {str(e)}'
        }), 500

@bp.route('/lista', methods=['GET'])
@login_required
def api_backup_lista():
    cartella = _cartella_backup()
    files = []
    for nome in sorted(os.listdir(cartella), reverse=True):
        if nome.endswith('.json'):
            full = os.path.join(cartella, nome)
            st = os.stat(full)
            files.append({
                'nome': nome,
                'dimensione': st.st_size,
                'dimensione_kb': round(st.st_size / 1024, 2),
                'data': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime)),
            })
    return jsonify({'success': True, 'backups': files, 'cartella': cartella})


@bp.route('/stato-cloud', methods=['GET'])
@login_required
def api_backup_stato_cloud():
    from app.config import BACKUP_CLOUD_DIR, BACKUP_CLOUD_ABILITATO
    esiste = os.path.exists(BACKUP_CLOUD_DIR)
    return jsonify({
        'success': True,
        'abilitato': bool(BACKUP_CLOUD_ABILITATO),
        'attivo': bool(BACKUP_CLOUD_ABILITATO and esiste),
        'cartella': BACKUP_CLOUD_DIR,
    })


@bp.route('/pacchetto-completo', methods=['GET'])
@login_required
def api_backup_pacchetto_completo():
    """Genera e scarica un unico ZIP portatile con programma + database + foto/video + launcher."""
    import zipfile, tempfile
    from flask import send_file, after_this_request
    from app.config import DATA_DIR, APP_DIR, IS_FROZEN

    storage.salva()
    tmp_dir = tempfile.mkdtemp(prefix="braaap_pkg_")
    zip_name = f"BRAAAP_COMPLETO_{time.strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = os.path.join(tmp_dir, zip_name)

    @after_this_request
    def _cleanup(response):
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass
        return response

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        # 1) Launcher portatile Windows
        bat = '@echo off\r\ntitle BRAAAP - Versione Portatile Autonoma\r\nset "BRAAAP_DATA_DIR=%~dp0dati"\r\nstart "" "%~dp0Braaap.exe"\r\n'
        zf.writestr("BRAAAP_PORTATILE/AVVIA_BRAAAP_PORTATILE.bat", bat)

        # 2) Eseguibile compilato (da APP_DIR se gia frozen, altrimenti da dist/Braaap)
        exe_src = APP_DIR if IS_FROZEN else (APP_DIR / "dist" / "Braaap")
        if exe_src.exists() and (exe_src / "Braaap.exe").exists():
            for root, dirs, files in os.walk(exe_src):
                if os.path.basename(root) in ("dati", "logs", "backups"):
                    continue
                for fn in files:
                    full = os.path.join(root, fn)
                    rel = os.path.relpath(full, exe_src)
                    zf.write(full, os.path.join("BRAAAP_PORTATILE", rel))

        # 3) Tutti i dati reali (braaap_data.json, foto, video, logo, backups)
        for root, dirs, files in os.walk(DATA_DIR):
            for fn in files:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, DATA_DIR)
                zf.write(full, os.path.join("BRAAAP_PORTATILE", "dati", rel))

    return send_file(zip_path, as_attachment=True, download_name=zip_name)
