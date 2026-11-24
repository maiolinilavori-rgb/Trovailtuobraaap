from __future__ import annotations
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data

bp = Blueprint('utility', __name__, url_prefix='/api')


"""
Route per utility.
ATTENZIONE: gli handler qui sotto usano `@app.route` direttamente.
Devi avvolgerli in `def register(app):` oppure importare `app` da `app/__init__.py`.
Vedi REPORT.md.
"""

from flask import request, jsonify, render_template_string
from datetime import datetime

# Alias di lettura per il dizionario globale
dati = storage.get_dati()

@bp.route('/stato')
@login_required
def api_stato():
    return jsonify({
        'ok': True,
        'giacenza_iniziale_impostata': dati.get('giacenza_iniziale_impostata', False),
        'import_excel_fatto': dati.get('import_excel_fatto', False),
        'eventi': len(dati.get('eventi', [])),
        'scuole': len(dati.get('scuole', [])),
        'rubrica': len(dati.get('rubrica', [])),
        'entita': len(dati.get('entita', [])),
        'task': len(dati.get('task', [])),
        'stock': dati.get('stock', {}),
        'postit': len(dati.get('postit', [])),
        'liste': len(dati.get('liste', [])),
    })


@bp.route('/cambio')
@login_required
def api_cambio():
    global _cambio_cache
    ora = datetime.now()
    if _cambio_cache['dati'] and (ora - _cambio_cache['quando']).total_seconds() < 6 * 3600:
        return jsonify(_cambio_cache['dati'])
    try:
        url = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
        with urllib.request.urlopen(url, timeout=6) as resp:
            contenuto = resp.read()
        root = ET.fromstring(contenuto)
        ns = {'ns': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}
        tassi = {'EUR': 1.0}
        for cube in root.findall('.//ns:Cube[@currency]', ns):
            tassi[cube.attrib['currency']] = float(cube.attrib['rate'])
        risultato = {'success': True, 'base': 'EUR', 'tassi': tassi, 'aggiornato': ora.strftime('%d/%m/%Y')}
        _cambio_cache = {'dati': risultato, 'quando': ora}
        return jsonify(risultato)
    except Exception as e:
        if _cambio_cache['dati']:
            return jsonify(_cambio_cache['dati'])
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/meteo')
@login_required
def api_meteo():
    global _meteo_cache
    citta = request.args.get('citta', '').strip()
    if not citta:
        return jsonify({'success': False})
    cache_key = citta.lower()
    ora = datetime.now()
    if cache_key in _meteo_cache and (ora - _meteo_cache[cache_key]['quando']).total_seconds() < 1800:
        return jsonify(_meteo_cache[cache_key]['dati'])
    try:
        headers = {'User-Agent': 'TrovaIlTuoBraaap/1.0'}
        url_geo = 'https://geocoding-api.open-meteo.com/v1/search?' + urllib.parse.urlencode({
            'name': citta, 'count': 1, 'language': 'it', 'format': 'json'})
        with urllib.request.urlopen(urllib.request.Request(url_geo, headers=headers), timeout=6) as resp:
            geo = json_lib.loads(resp.read())
        if not geo.get('results'):
            return jsonify({'success': False, 'error': 'Località non trovata'})
        l = geo['results'][0]
        url_m = 'https://api.open-meteo.com/v1/forecast?' + urllib.parse.urlencode({
            'latitude': l['latitude'], 'longitude': l['longitude'],
            'current': 'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m',
            'daily': 'temperature_2m_max,temperature_2m_min,weather_code',
            'timezone': 'auto', 'forecast_days': 3})
        with urllib.request.urlopen(urllib.request.Request(url_m, headers=headers), timeout=6) as resp:
            prev = json_lib.loads(resp.read())
        risultato = {'success': True, 'localita': l.get('name', citta),
                     'attuale': prev.get('current', {}), 'prossimi_giorni': prev.get('daily', {})}
        _meteo_cache[cache_key] = {'dati': risultato, 'quando': ora}
        return jsonify(risultato)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/meteo_preferiti', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_meteo_preferiti():
    dati.setdefault('meteo_preferiti', [])
    if request.method == 'POST':
        try:
            citta = (request.get_json(force=True).get('citta') or '').strip()
        except Exception:
            return jsonify({'success': False}), 400
        if citta and citta not in storage.get_dati()['meteo_preferiti']:
            storage.get_dati()['meteo_preferiti'].append(citta)
            storage.salva()
        return jsonify({'success': True})
    if request.method == 'DELETE':
        citta = request.args.get('citta', '')
        storage.get_dati()['meteo_preferiti'] = [c for c in storage.get_dati()['meteo_preferiti'] if c != citta]
        storage.salva()
        return jsonify({'success': True})
    return jsonify(dati.get('meteo_preferiti', []))


@bp.route('/logo', methods=['POST'])
@login_required
def api_logo():
    if 'logo' not in request.files:
        return jsonify({'success': False}), 400
    f = request.files['logo']
    if f.filename == '':
        return jsonify({'success': False}), 400
    storage.get_dati()['logo'] = base64.b64encode(f.read()).decode('utf-8')
    storage.salva()
    return jsonify({'success': True})


@bp.route('/vocabolario', methods=['GET'])
@login_required
def api_vocabolario():
    dati.setdefault('vocabolario', {'categorie': {}, 'tentativi': []})
    return jsonify(storage.get_dati()['vocabolario'])


_cambio_cache = {'dati': None, 'quando': datetime.min}
_meteo_cache = {}
