from __future__ import annotations
import os
import json
import time
import shutil
import hashlib as _hashlib_bk
import re
from datetime import datetime
from collections import defaultdict
from app.config import (BACKUP_DIR, BACKUP_CLOUD_DIR, BACKUP_CLOUD_ABILITATO,
                        BACKUP_MAX_GIORNALIERI, BACKUP_MAX_SETTIMANALI,
                        BACKUP_MAX_MENSILI, BACKUP_MAX_ORE_MINIME,
                        BACKUP_OGNI_N_SALVATAGGI, DATA_FILE)
from app import storage


def _get_dati():
    return storage.get_dati()


def _timestamp_backup():
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def _copia_backup_in_cloud(path_locale, nome):
    """
    Copia un backup in cloud con retry (3 tentativi).
    Usa shutil.copy2 diretto (senza os.replace che su Windows + OneDrive fallisce).
    Ritorna il path cloud se successo, altrimenti None.
    """
    if not (BACKUP_CLOUD_ABILITATO and BACKUP_CLOUD_DIR):
        return None

    try:
        os.makedirs(BACKUP_CLOUD_DIR, exist_ok=True)
    except Exception as e:
        log.error('Impossibile creare cartella cloud %s: %s', BACKUP_CLOUD_DIR, e)
        return None

    path_cloud = os.path.join(BACKUP_CLOUD_DIR, nome)
    meta_locale = path_locale + '.meta.json'
    meta_cloud = path_cloud + '.meta.json'

    MAX_TENTATIVI = 3
    for tentativo in range(1, MAX_TENTATIVI + 1):
        try:
            shutil.copy2(path_locale, path_cloud)
            log.info('Backup cloud OK (tentativo %d): %s', tentativo, nome)
            if os.path.exists(meta_locale):
                try:
                    shutil.copy2(meta_locale, meta_cloud)
                except Exception as e:
                    log.warning('Meta cloud non copiato: %s', e)
            return path_cloud
        except Exception as e:
            log.warning('Backup cloud - tentativo %d/%d fallito: %s', tentativo, MAX_TENTATIVI, e)
            if tentativo < MAX_TENTATIVI:
                time.sleep(1.0)

    log.error('Backup cloud FALLITO dopo %d tentativi: %s', MAX_TENTATIVI, nome)
    return None

def _crea_backup(motivo='manuale', forza=False):
    """Crea un backup locale + copia cloud (se configurato)."""
    global _backup_state
    try:
        ts = _timestamp_backup()
        nome = f'braaap_{ts}_{motivo}.json'
        path_locale = os.path.join(BACKUP_DIR, nome)

        meta = {
            'data': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'motivo': motivo,
            'eventi': len(dati.get('eventi', [])),
            'scuole': len(dati.get('scuole', [])),
            'rubrica': len(dati.get('rubrica', [])),
            'task': len(dati.get('task', [])),
            'entita': len(dati.get('entita', [])),
            'postit': len(dati.get('postit', [])),
            'liste': len(dati.get('liste', [])),
            'note_vocali': len(dati.get('note_vocali', [])),
        }

        os.makedirs(BACKUP_DIR, exist_ok=True)
        tmp_locale = path_locale + '.tmp'
        with open(tmp_locale, 'w', encoding='utf-8') as f:
            json.dump(dati, f, indent=2, default=str, ensure_ascii=False)
        os.replace(tmp_locale, path_locale)

        with open(path_locale, 'rb') as f:
            meta['checksum'] = _hashlib_bk.sha256(f.read()).hexdigest()
        meta['dimensione'] = os.path.getsize(path_locale)

        try:
            with open(path_locale + '.meta.json', 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.warning('Impossibile scrivere meta per %s: %s', nome, e)

        log.info('Backup locale: %s (%d KB)', nome, meta['dimensione'] // 1024)

        # Copia cloud (con retry, OneDrive-friendly)
        path_cloud = _copia_backup_in_cloud(path_locale, nome)

        _pulisci_backup_gerarchica()
        _backup_state['n_salvataggi'] = 0
        return path_locale, path_cloud, motivo

    except Exception as e:
        log.error('Errore crea_backup: %s', e)
        return None, None, None

def _backup_automatico():
    """Chiamato da salva_dati(): backup ogni N salvataggi."""
    try:
        _backup_state['n_salvataggi'] += 1
        if _backup_state['n_salvataggi'] < BACKUP_OGNI_N_SALVATAGGI:
            return
        _crea_backup(motivo='auto')
    except Exception as e:
        log.error('Errore backup automatico: %s', e)

def _backup_all_avvio():
    """Backup all'avvio se sono passate >= BACKUP_MAX_ORE_MINIME ore."""
    try:
        if not os.path.isdir(BACKUP_DIR):
            _crea_backup(motivo='avvio_iniziale')
            return
        files = [f for f in os.listdir(BACKUP_DIR)
                 if f.startswith('braaap_') and f.endswith('.json') and not f.endswith('.meta.json')]
        if not files:
            _crea_backup(motivo='avvio_iniziale')
            return
        ultimi = sorted(files, reverse=True)
        ultimo_path = os.path.join(BACKUP_DIR, ultimi[0])
        ore_passate = (time.time() - os.path.getmtime(ultimo_path)) / 3600.0
        if ore_passate >= BACKUP_MAX_ORE_MINIME:
            _crea_backup(motivo='avvio')
        else:
            log.info('Backup avvio saltato (ultimo %.1fh fa, soglia %dh)', ore_passate, BACKUP_MAX_ORE_MINIME)
    except Exception as e:
        log.error('Errore backup avvio: %s', e)

def _pulisci_backup_gerarchica():
    """Rotazione: 7 giorni + 4 settimane + 12 mesi."""
    try:
        _pulisci_backup_gerarchica_dir(BACKUP_DIR)
        if BACKUP_CLOUD_ABILITATO and BACKUP_CLOUD_DIR and os.path.isdir(BACKUP_CLOUD_DIR):
            _pulisci_backup_gerarchica_dir(BACKUP_CLOUD_DIR)
    except Exception as e:
        log.error('Errore rotazione backup: %s', e)

def _pulisci_backup_gerarchica_dir(directory):
    if not os.path.isdir(directory):
        return
    files = [f for f in os.listdir(directory)
             if f.startswith('braaap_') and f.endswith('.json') and not f.endswith('.meta.json')]
    if not files:
        return

    from collections import defaultdict
    per_giorno = defaultdict(list)
    per_settimana = defaultdict(list)
    per_mese = defaultdict(list)

    for f in files:
        m = re.match(r'braaap_(\d{8})_(\d{6})_(.+)\.json', f)
        if not m:
            continue
        giorno = m.group(1)
        anno = giorno[:4]
        mese = giorno[4:6]
        try:
            dt = datetime.strptime(giorno, '%Y%m%d')
            settimana = dt.strftime('%Y_%V')
        except Exception:
            settimana = anno + '_00'
        per_giorno[giorno].append(f)
        per_settimana[settimana].append(f)
        per_mese[anno + '_' + mese].append(f)

    def tieni_uno_per_chiave(dizio, max_n):
        chiavi_ordinate = sorted(dizio.keys(), reverse=True)[:max_n]
        tenuti = set()
        for k in chiavi_ordinate:
            lista = sorted(dizio[k])
            tenuti.add(lista[0])
        return tenuti

    tenuti = set()
    tenuti |= tieni_uno_per_chiave(per_giorno, BACKUP_MAX_GIORNALIERI)
    tenuti |= tieni_uno_per_chiave(per_settimana, BACKUP_MAX_SETTIMANALI)
    tenuti |= tieni_uno_per_chiave(per_mese, BACKUP_MAX_MENSILI)

    eliminati = 0
    for f in files:
        if f not in tenuti:
            try:
                os.remove(os.path.join(directory, f))
                meta_f = os.path.join(directory, f + '.meta.json')
                if os.path.exists(meta_f):
                    os.remove(meta_f)
                eliminati += 1
            except Exception:
                pass
    if eliminati > 0:
        log.info('Rotazione backup in %s: rimossi %d file', directory, eliminati)

def _info_backup(path):
    info = {
        'nome': os.path.basename(path),
        'dimensione': os.path.getsize(path) if os.path.exists(path) else 0,
        'data_file': datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S') if os.path.exists(path) else '',
    }
    meta_path = path + '.meta.json'
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                info.update(json.load(f))
        except Exception:
            pass
    if BACKUP_CLOUD_ABILITATO and BACKUP_CLOUD_DIR:
        cloud_path = os.path.join(BACKUP_CLOUD_DIR, info['nome'])
        info['cloud'] = os.path.exists(cloud_path)
    else:
        info['cloud'] = False
    return info

def _verifica_integrita_backup(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            contenuto = f.read()
        json.loads(contenuto)
    except Exception as e:
        return False, f'JSON non valido: {e}'
    meta_path = path + '.meta.json'
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            checksum_atteso = meta.get('checksum')
            if checksum_atteso:
                checksum_reale = _hashlib_bk.sha256(contenuto.encode('utf-8')).hexdigest()
                if checksum_reale != checksum_atteso:
                    return False, 'Checksum non corrisponde'
        except Exception:
            pass
    return True, None

def _ripristina_backup(nome_file):
    path_backup = os.path.join(BACKUP_DIR, nome_file)
    if not os.path.exists(path_backup):
        return False, 'Backup non trovato', None

    ok, errore = _verifica_integrita_backup(path_backup)
    if not ok:
        return False, f'Backup corrotto: {errore}', None

    ts = _timestamp_backup()
    sicurezza = os.path.join(BACKUP_DIR, f'braaap_{ts}_pre_restore.json')
    try:
        shutil.copy2(DATA_FILE, sicurezza)
        log.info('Backup sicurezza pre-restore: %s', sicurezza)
    except Exception as e:
        return False, f'Impossibile creare backup di sicurezza: {e}', None

    try:
        with open(path_backup, 'r', encoding='utf-8') as f:
            contenuto = f.read()
        nuovi_dati = json.loads(contenuto)
        tmp = DATA_FILE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(nuovi_dati, f, indent=2, default=str, ensure_ascii=False)
        os.replace(tmp, DATA_FILE)
        log.info('Backup ripristinato: %s', nome_file)
        return True, f'Ripristinato da {nome_file}', sicurezza
    except Exception as e:
        return False, f'Errore ripristino: {e}', sicurezza
