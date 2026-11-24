"""Configurazione centrale Braaap."""
from __future__ import annotations
import os
import sys
from pathlib import Path

IS_FROZEN = getattr(sys, 'frozen', False)
if IS_FROZEN:
    APP_DIR = Path(sys.executable).parent
    BUNDLE_DIR = Path(getattr(sys, '_MEIPASS', APP_DIR))
else:
    APP_DIR = Path(__file__).resolve().parent.parent
    BUNDLE_DIR = APP_DIR

# === MEMORANDIA: nome app + data dir con fallback ===
APP_NAME = 'BRAAAP'
APP_TAGLINE = 'Il tuo archivio universale'

_appdata = Path(os.environ.get('APPDATA', str(APP_DIR)))
_new_dir = _appdata / 'Braaap'
_legacy_dir = _appdata / 'Braaap'

if os.environ.get('BRAAAP_DATA_DIR'):
    DATA_DIR = Path(os.environ['BRAAAP_DATA_DIR'])
elif os.environ.get('BRAAAP_DATA_DIR'):
    DATA_DIR = Path(os.environ['BRAAAP_DATA_DIR'])
elif os.environ.get('BRAAAP_PORTABLE') == '1':
    DATA_DIR = APP_DIR
elif _new_dir.exists():
    DATA_DIR = _new_dir
elif _legacy_dir.exists():
    DATA_DIR = _legacy_dir
else:
    DATA_DIR = _new_dir

DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / 'braaap_data.json'
BACKUP_DIR = DATA_DIR / 'backups'
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
# --- Logging ---
LOG_DIR = DATA_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / 'braaap.log'
LOG_LEVEL = os.environ.get('BRAAAP_LOG_LEVEL', 'INFO').upper()
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 5


AUTH_ABILITATO = os.environ.get('BRAAAP_NO_AUTH') != '1'
UTENTE_DEFAULT = 'admin'
PASSWORD_DEFAULT = os.environ.get('PASSWORD_DEFAULT', 'braaap2026')

SECRET_KEY = os.environ.get('SECRET_KEY', 'braaap-2026-fallback-non-usare-in-produzione')

HOST = os.environ.get('BRAAAP_HOST', '0.0.0.0')
PORT = int(os.environ.get('BRAAAP_PORT', '5000'))

BACKUP_CLOUD_DIR = str(Path(os.environ.get('USERPROFILE', '')) / 'OneDrive' / 'Braaap_Backup')
BACKUP_CLOUD_ABILITATO = True
BACKUP_MAX_GIORNALIERI = 7
BACKUP_MAX_SETTIMANALI = 4
BACKUP_MAX_MENSILI = 12
BACKUP_MAX_ORE_MINIME = 6
BACKUP_OGNI_N_SALVATAGGI = 10

EVENTI_SCALANO_STOCK = False

NOMI_FILE_BRACCIALETTI = [
    'BRACCIALETTI DISTRIBUITI e coppe.xlsx',
    'BRACCIALETTI_DISTRIBUITI_e_coppe.xlsx',
]
NOMI_FILE_CONTATTI = [
    'SCHEDA CONTATTI X INIZIATIVE.xlsx',
    'SCHEDA_CONTATTI_X_INIZIATIVE.xlsx',
]

# --- Groq API ---
try:
    from dotenv import load_dotenv
    load_dotenv(APP_DIR / '.env')
    load_dotenv(BUNDLE_DIR / '.env')
except Exception:
    pass

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '').strip()
GROQ_MODELLO_WHISPER = 'whisper-large-v3-turbo'
GROQ_MODELLO_LLM = 'qwen/qwen3.8-27b'
GROQ_ABILITATO = bool(GROQ_API_KEY)