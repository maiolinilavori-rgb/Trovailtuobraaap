"""Gestione backup automatici, manuali e su cloud."""
from __future__ import annotations
import json
import logging
import os
import shutil
import time
from datetime import datetime
from app.config import (
    DATA_FILE, BACKUP_DIR, BACKUP_CLOUD_DIR, BACKUP_CLOUD_ABILITATO,
    BACKUP_MAX_GIORNALIERI, BACKUP_MAX_SETTIMANALI, BACKUP_MAX_MENSILI,
    BACKUP_MAX_ORE_MINIME, BACKUP_OGNI_N_SALVATAGGI,
)

log = logging.getLogger('braaap.backup')
_backup_state = {'n_salvataggi': 0, 'ultimo_ts': 0.0}

def _get_dati():
    from app import storage
    return storage.get_dati()

def _crea_backup(etichetta='auto', forza_cloud=False):
    if not DATA_FILE.exists():
        return None
    try:
        dati = _get_dati()
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        nome = f'braaap_backup_{ts}_{etichetta}.json'
        dest = BACKUP_DIR / nome
        shutil.copy2(DATA_FILE, dest)
        n_ev = len(dati.get('eventi', []))
        n_sc = len(dati.get('scuole', []))
        n_al = len(dati.get('altro', []))
        meta = {
            'file': nome,
            'timestamp': datetime.now().isoformat(),
            'etichetta': etichetta,
            'dimensione_byte': dest.stat().st_size,
            'eventi': n_ev,
            'scuole': n_sc,
            'altro': n_al,
            'n_salvataggi': _backup_state.get('n_salvataggi', 0),
        }
        with open(BACKUP_DIR / (nome + '.meta.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        if BACKUP_CLOUD_ABILITATO and (forza_cloud or etichetta in ('manuale', 'pre_import', 'pre_ripristino', 'chiusura')):
            try:
                cloud_dir = os.path.expandvars(BACKUP_CLOUD_DIR)
                os.makedirs(cloud_dir, exist_ok=True)
                shutil.copy2(dest, os.path.join(cloud_dir, nome))
            except Exception as ce:
                log.warning(f'Backup cloud non riuscito: {ce}')
        _ruota_backup()
        return meta
    except Exception as e:
        log.error(f'Errore creazione backup: {e}')
        return None

def _ruota_backup():
    try:
        files = sorted(BACKUP_DIR.glob('braaap_backup_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
        files = [f for f in files if not f.name.endswith('.meta.json')]
        if len(files) <= 20:
            return
        giorni_visti, settimane_viste, mesi_visti, da_tenere = set(), set(), set(), set()
        for f in files:
            dt = datetime.fromtimestamp(f.stat().st_mtime)
            g, s, m = dt.strftime('%Y-%m-%d'), dt.strftime('%Y-W%W'), dt.strftime('%Y-%m')
            if len(giorni_visti) < BACKUP_MAX_GIORNALIERI or g in giorni_visti:
                giorni_visti.add(g); da_tenere.add(f); continue
            if len(settimane_viste) < BACKUP_MAX_SETTIMANALI or s in settimane_viste:
                settimane_viste.add(s); da_tenere.add(f); continue
            if len(mesi_visti) < BACKUP_MAX_MENSILI or m in mesi_visti:
                mesi_visti.add(m); da_tenere.add(f); continue
        for f in files:
            if f not in da_tenere:
                try:
                    f.unlink(missing_ok=True)
                    (BACKUP_DIR / (f.name + '.meta.json')).unlink(missing_ok=True)
                except Exception:
                    pass
    except Exception as e:
        log.warning(f'Errore rotazione backup: {e}')

def _backup_automatico():
    _backup_state['n_salvataggi'] += 1
    ora = time.time()
    n_ok = _backup_state['n_salvataggi'] >= BACKUP_OGNI_N_SALVATAGGI
    t_ok = (ora - _backup_state['ultimo_ts']) >= BACKUP_MAX_ORE_MINIME * 3600
    if n_ok or t_ok:
        _backup_state['n_salvataggi'] = 0
        _backup_state['ultimo_ts'] = ora
        _crea_backup(etichetta='auto', forza_cloud=False)

def _lista_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted([f for f in BACKUP_DIR.glob('braaap_backup_*.json') if not f.name.endswith('.meta.json')],
                   key=lambda p: p.stat().st_mtime, reverse=True)
    risultato = []
    for f in files:
        meta_file = BACKUP_DIR / (f.name + '.meta.json')
        meta = {}
        if meta_file.exists():
            try:
                with open(meta_file, 'r', encoding='utf-8') as mf:
                    meta = json.load(mf)
            except Exception:
                pass
        dt = datetime.fromtimestamp(f.stat().st_mtime)
        risultato.append({
            'file': f.name,
            'timestamp': meta.get('timestamp', dt.isoformat()),
            'data_leggibile': dt.strftime('%d/%m/%Y %H:%M:%S'),
            'etichetta': meta.get('etichetta', 'auto'),
            'dimensione_byte': f.stat().st_size,
            'dimensione_kb': round(f.stat().st_size / 1024, 1),
            'eventi': meta.get('eventi', '?'),
            'scuole': meta.get('scuole', '?'),
            'altro': meta.get('altro', '?'),
        })
    return risultato

def _ripristina_backup(nome_file):
    from app import storage
    nome_sicuro = os.path.basename(nome_file or '')
    sorgente = BACKUP_DIR / nome_sicuro
    if not sorgente.exists() or not sorgente.name.startswith('braaap_backup_'):
        return False, 'File backup non trovato'
    try:
        with open(sorgente, 'r', encoding='utf-8') as f:
            nuovi_dati = json.load(f)
        if not isinstance(nuovi_dati, dict) or 'eventi' not in nuovi_dati:
            return False, 'Il file backup non e un JSON Braaap valido'
    except Exception as e:
        return False, f'Backup corrotto: {e}'
    _crea_backup(etichetta='pre_ripristino', forza_cloud=True)
    storage.imposta_dati_completi(nuovi_dati)
    return True, f'Ripristinato {nome_sicuro} ({len(nuovi_dati.get("eventi", []))} eventi)'
