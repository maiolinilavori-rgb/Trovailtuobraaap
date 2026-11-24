from __future__ import annotations
import re
import time
import socket
from datetime import datetime


def _nuovo_id():
    return int(datetime.now().timestamp() * 1000) + int(time.time_ns() % 1000)

def _parse_data(valore):
    if isinstance(valore, datetime):
        return valore
    if valore is None:
        return None
    s = str(valore).strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%d.%m.%Y'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    m = re.match(r'^(\d{1,2})[/\-](\d{4})$', s)
    if m:
        try:
            return datetime(int(m.group(2)), int(m.group(1)), 1)
        except ValueError:
            return None
    return None

def _intero(valore, default=0):
    try:
        return int(float(valore))
    except (ValueError, TypeError):
        return default

def _float(valore, default=0.0):
    try:
        return float(valore)
    except (ValueError, TypeError):
        return default

def _escape_html(testo):
    if testo is None:
        return ''
    return (str(testo).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))

def _get_ip_locale():
    """Trova l'IP locale della macchina (per mostrare l'URL al cellulare)."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'
