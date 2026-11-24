"""Inizializzazione dell'applicazione Flask."""
from __future__ import annotations
import logging
import logging.handlers
import sys

from flask import Flask


def _configura_logging():
    """Configura logging su file + console. Idempotente."""
    from .config import LOG_FILE, LOG_LEVEL, LOG_MAX_BYTES, LOG_BACKUP_COUNT

    root = logging.getLogger()
    if getattr(root, '_braaap_configurato', False):
        return

    livello = getattr(logging, LOG_LEVEL, logging.INFO)
    root.setLevel(livello)

    fmt = logging.Formatter(
        '%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8',
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(livello)
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    console_handler.setLevel(livello)
    root.addHandler(console_handler)

    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    def _log_exception(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        root.critical('Eccezione non gestita', exc_info=(exc_type, exc_value, exc_tb))
    sys.excepthook = _log_exception

    root._braaap_configurato = True
    root.info('Logging inizializzato su %s (livello %s)', LOG_FILE, LOG_LEVEL)


def create_app():
    _configura_logging()

    from .config import SECRET_KEY, BUNDLE_DIR
    app = Flask(__name__, template_folder=str(BUNDLE_DIR / "templates"), static_folder=str(BUNDLE_DIR / "static"))
    app.config['SECRET_KEY'] = SECRET_KEY
    # Disabilita cache Jinja2 per sviluppo (forza reload template)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True
    app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

    from .routes import registra_tutte
    registra_tutte(app)

    logging.getLogger(__name__).info('App Flask creata')
    return app