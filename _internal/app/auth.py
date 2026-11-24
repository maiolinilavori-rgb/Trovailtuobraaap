"""Autenticazione e decoratore login_required."""
from __future__ import annotations
from functools import wraps
from flask import session, redirect, url_for, jsonify, request
from app.config import AUTH_ABILITATO, UTENTE_DEFAULT, PASSWORD_DEFAULT


def _check_auth():
    if not AUTH_ABILITATO:
        return True
    return session.get('memorandia_logged') is True or session.get('braaap_logged') is True


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if _check_auth():
            return f(*args, **kwargs)
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Non autenticato',
                            'auth_required': True}), 401
        return redirect(url_for('misc.login'))
    return decorated
