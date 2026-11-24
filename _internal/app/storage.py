"""Gestione dati in memoria e persistenza su JSON (thread-safe + scrittura atomica)."""
from __future__ import annotations
import json
import os
import threading
from datetime import datetime
from app.config import DATA_FILE

_lock = threading.RLock()
_dati = None

def _struttura_default():
    return {
        'eventi': [], 'scuole': [], 'altro': [], 'rubrica': [],
        'task': [], 'postit': [], 'note_calendario': [],
        'liste': [], 'note_vocali': [], 'entrate': [], 'uscite': [],
        'portafoglio': [],
        'stock': {'braccialetti': 0, 'medaglie': 0, 'adesivi': 0, 'coppe': 0},
        'movimenti': {'braccialetti': [], 'medaglie': [], 'adesivi': [], 'coppe': []},
        'entita': [],
        'inventario': [],
        'soglie_scorte': {'braccialetti': 50, 'medaglie': 30, 'adesivi': 30, 'coppe': 3},
        'anno_corrente': datetime.now().year,
    }

def carica_dati():
    global _dati
    with _lock:
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    _dati = json.load(f)
                default = _struttura_default()
                for k, v in default.items():
                    _dati.setdefault(k, v)
                return _dati
            except Exception as e:
                print(f'Errore caricamento dati: {e}')
        _dati = _struttura_default()
        salva_dati(_dati)
        return _dati

def get_dati():
    with _lock:
        if _dati is None:
            return carica_dati()
        return _dati

def imposta_dati_completi(nuovi_dati):
    global _dati
    with _lock:
        default = _struttura_default()
        for k, v in default.items():
            nuovi_dati.setdefault(k, v)
        _dati = nuovi_dati
        salva_dati(_dati, crea_backup=False)

def salva_dati(dati=None, crea_backup=True):
    global _dati
    with _lock:
        if dati is not None:
            _dati = dati
        if _dati is None:
            return
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = DATA_FILE.parent / (DATA_FILE.name + '.tmp')
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(_dati, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_file, DATA_FILE)
        if crea_backup:
            try:
                from app.backup import _backup_automatico
                _backup_automatico()
            except Exception:
                pass

def ricalcola_stock():
    with _lock:
        d = get_dati()
        usati = {'braccialetti': 0, 'medaglie': 0, 'adesivi': 0, 'coppe': 0}
        for ev in d.get('eventi', []):
            m = ev.get('materiale') or {}
            for k in usati:
                try:
                    usati[k] += int(m.get(k) or 0)
                except Exception:
                    pass
        return usati

def prossimo_id(lista):
    if not lista:
        return 1
    return max((x.get('id', 0) for x in lista if isinstance(x, dict)), default=0) + 1

salva = salva_dati

