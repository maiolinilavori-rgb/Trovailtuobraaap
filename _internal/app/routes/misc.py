from __future__ import annotations
from app import storage
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data

bp = Blueprint('misc', __name__, url_prefix='')


"""
Route per misc.
ATTENZIONE: gli handler qui sotto usano `@app.route` direttamente.
Devi avvolgerli in `def register(app):` oppure importare `app` da `app/__init__.py`.
Vedi REPORT.md.
"""

from flask import request, jsonify, render_template_string
from datetime import datetime

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if not AUTH_ABILITATO:
        return redirect(url_for('misc.index'))

    if request.method == 'POST':
        u = (request.form.get('utente') or '').strip()
        p = (request.form.get('password') or '').strip()
        if u == UTENTE_DEFAULT and p == PASSWORD_DEFAULT:
            session['memorandia_logged'] = True
            session['braaap_logged'] = True  # compat legacy
            return redirect(url_for('misc.index'))
        return LOGIN_HTML.replace('{{ERRORE}}',
            '<div class="errore">❌ Utente o password sbagliati</div>')

    return LOGIN_HTML.replace('{{ERRORE}}', '')


@bp.route('/logout')
def logout():
    session.pop('memorandia_logged', None)
    session.pop('braaap_logged', None)  # compat legacy
    return redirect(url_for('misc.login'))


@bp.route('/')
@login_required
def index():
    from flask import render_template
    return render_template('index.html', dati=storage.get_dati())

@bp.route('/api/soglie', methods=['GET', 'POST'])
@login_required
def api_soglie():
    dati = storage.get_dati()
    default_soglie = {'braccialetti': 50, 'medaglie': 30, 'adesivi': 30, 'coppe': 3}
    soglie = dati.setdefault('soglie_scorte', dict(default_soglie))
    if request.method == 'GET':
        return jsonify(soglie)
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False, 'error': 'JSON non valido'}), 400
    for k in ('braccialetti', 'medaglie', 'adesivi', 'coppe'):
        if k in body and body[k] is not None:
            soglie[k] = int(body[k])
    storage.salva()
    return jsonify({'success': True, 'soglie': soglie})


@bp.route('/favicon.ico')
def favicon():
    return ('', 204)



from app.config import AUTH_ABILITATO, UTENTE_DEFAULT, PASSWORD_DEFAULT

# Alias di lettura per il dizionario globale
dati = storage.get_dati()

LOGIN_HTML = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Trova il tuo Braaap - Login</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; }
body {
  font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
  background: #0f1419;
  min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

/* Sfondo decorativo: pattern onde + gradiente */
body::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 15% 20%, rgba(2,136,209,0.35), transparent 45%),
    radial-gradient(circle at 85% 80%, rgba(255,87,34,0.25), transparent 45%),
    linear-gradient(135deg, #0f1419 0%, #1a232e 50%, #0f1419 100%);
  z-index: 0;
}

/* Pattern di linee in movimento */
body::after {
  content: '';
  position: absolute;
  inset: -50%;
  background-image:
    repeating-linear-gradient(45deg, transparent, transparent 40px, rgba(255,255,255,0.02) 40px, rgba(255,255,255,0.02) 80px);
  animation: slide 30s linear infinite;
  z-index: 0;
  pointer-events: none;
}
@keyframes slide {
  0% { transform: translate(0, 0); }
  100% { transform: translate(80px, 80px); }
}

/* Contenitore principale */
.wrap {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
}

/* Logo BRAAAP in cima */
.logo {
  text-align: center;
  margin-bottom: 28px;
  animation: fadeDown 0.8s ease-out;
}
.logo-svg {
  width: 90px;
  height: 90px;
  margin: 0 auto 12px;
  display: block;
  filter: drop-shadow(0 0 25px rgba(2,136,209,0.6));
  animation: float 3s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
.logo h1 {
  font-size: 42px;
  font-weight: 900;
  letter-spacing: 6px;
  background: linear-gradient(135deg, #0288D1 0%, #4FC3F7 50%, #FF5722 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-transform: uppercase;
  margin-bottom: 4px;
}
.logo .tagline {
  color: #90A4AE;
  font-size: 12px;
  letter-spacing: 3px;
  text-transform: uppercase;
}

/* Card login */
.box {
  background: rgba(255,255,255,0.96);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 36px 32px;
  box-shadow:
    0 30px 80px rgba(0,0,0,0.6),
    0 0 0 1px rgba(255,255,255,0.1),
    inset 0 1px 0 rgba(255,255,255,0.9);
  animation: fadeUp 0.6s ease-out;
  position: relative;
  overflow: hidden;
}
.box::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 4px;
  background: linear-gradient(90deg, #0288D1, #4FC3F7, #FF5722);
}

@keyframes fadeDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.box h2 {
  color: #1a232e;
  font-size: 20px;
  margin-bottom: 6px;
  text-align: center;
  font-weight: 700;
}
.box .sotto {
  color: #607078;
  text-align: center;
  font-size: 13px;
  margin-bottom: 26px;
}

label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 6px;
  color: #37474F;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.input-wrap {
  position: relative;
  margin-bottom: 16px;
}
.input-wrap .icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 16px;
  opacity: 0.5;
  pointer-events: none;
  transition: opacity 0.2s;
}
input {
  width: 100%;
  padding: 13px 14px 13px 42px;
  border: 2px solid #e0e6eb;
  border-radius: 10px;
  font-size: 15px;
  font-family: inherit;
  background: #f8fafb;
  transition: all 0.2s;
  color: #1a232e;
}
input:focus {
  outline: none;
  border-color: #0288D1;
  background: white;
  box-shadow: 0 0 0 4px rgba(2,136,209,0.12);
}
.input-wrap:focus-within .icon { opacity: 1; }

button {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #0288D1 0%, #0277BD 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 1px;
  text-transform: uppercase;
  box-shadow: 0 4px 14px rgba(2,136,209,0.35);
  margin-top: 8px;
  position: relative;
  overflow: hidden;
}
button:hover {
  background: linear-gradient(135deg, #0277BD 0%, #01579B 100%);
  box-shadow: 0 6px 20px rgba(2,136,209,0.5);
  transform: translateY(-1px);
}
button:active { transform: translateY(0); }
button::after {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  transition: left 0.5s;
}
button:hover::after { left: 100%; }

.errore {
  background: linear-gradient(135deg, #FEF2F2, #FEE2E2);
  color: #DC2626;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 16px;
  text-align: center;
  font-weight: 600;
  border-left: 4px solid #DC2626;
  animation: shake 0.4s;
}
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-6px); }
  75% { transform: translateX(6px); }
}

.hint {
  font-size: 11px;
  color: #607078;
  text-align: center;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e0e6eb;
  line-height: 1.6;
}
.hint strong { color: #37474F; }

/* Footer */
.footer {
  text-align: center;
  color: rgba(255,255,255,0.4);
  font-size: 11px;
  margin-top: 24px;
  letter-spacing: 1px;
  animation: fadeUp 0.8s ease-out 0.2s both;
}

@media (max-width: 480px) {
  .logo h1 { font-size: 32px; letter-spacing: 4px; }
  .logo-svg { width: 70px; height: 70px; }
  .box { padding: 28px 22px; }
}
</style>
</head>
<body>
  <div class="wrap">
    <div class="logo">
      <!-- Logo SVG: moto stilizzata -->
      <svg class="logo-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#4FC3F7;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#0288D1;stop-opacity:1" />
          </linearGradient>
        </defs>
        <!-- Ruota posteriore -->
        <circle cx="25" cy="68" r="14" fill="none" stroke="url(#grad1)" stroke-width="4"/>
        <circle cx="25" cy="68" r="4" fill="#4FC3F7"/>
        <!-- Ruota anteriore -->
        <circle cx="75" cy="68" r="14" fill="none" stroke="url(#grad1)" stroke-width="4"/>
        <circle cx="75" cy="68" r="4" fill="#4FC3F7"/>
        <!-- Corpo moto -->
        <path d="M 25 68 L 40 45 L 60 45 L 75 68" stroke="url(#grad1)" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M 40 45 L 45 30 L 58 30 L 60 45" stroke="url(#grad1)" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        <!-- Manubrio -->
        <line x1="45" y1="30" x2="38" y2="22" stroke="#4FC3F7" stroke-width="3.5" stroke-linecap="round"/>
        <line x1="58" y1="30" x2="65" y2="22" stroke="#4FC3F7" stroke-width="3.5" stroke-linecap="round"/>
        <!-- Velocità -->
        <line x1="65" y1="22" x2="78" y2="22" stroke="#FF5722" stroke-width="3" stroke-linecap="round"/>
      </svg>
      <h1>Trova il tuo Braaap</h1>
      <div class="tagline">Il tuo archivio universale</div>
    </div>

    <div class="box">
      <h2>Accedi</h2>
      <div class="sotto">Inserisci le credenziali per continuare</div>
      {{ERRORE}}
      <form method="POST">
        <label>Utente</label>
        <div class="input-wrap">
          <span class="icon">&#128100;</span>
          <input type="text" name="utente" autofocus required value="admin" autocomplete="username">
        </div>
        <label>Password</label>
        <div class="input-wrap">
          <span class="icon">&#128274;</span>
          <input type="password" name="password" required autocomplete="current-password">
        </div>
        <button type="submit">Accedi &rarr;</button>
      </form>
      <div class="hint">
        Credenziali di default: <strong>admin</strong> / <strong>braaap2026</strong>
      </div>
    </div>

    <div class="footer">TROVA IL TUO BRAAAP &middot; 2026</div>
  </div>
</body>
</html>"""
