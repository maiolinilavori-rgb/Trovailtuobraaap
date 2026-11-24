(function() {
  'use strict';
  function applicaUxFix() {
    // 1. Sposta le card di Export e Backup fuori dalle pagine dentro #page-esporta
    var expPage = document.getElementById('page-esporta');
    if (expPage) {
      var titoliBackup = ['Export completo', 'Statistiche backup', 'Azioni rapide', 'Cartella backup extra', 'Backup disponibili'];
      var spostate = 0;
      document.querySelectorAll('.card').forEach(function(c) {
        if (expPage.contains(c)) return;
        var h = c.querySelector('h3');
        var t = h ? h.textContent : '';
        if (titoliBackup.some(function(k) { return t.indexOf(k) >= 0; })) {
          expPage.appendChild(c);
          spostate++;
        }
      });
      var dash = document.getElementById('page-dashboard');
      if (spostate > 0 && dash && !document.getElementById('miniBarBackupHome')) {
        var bar = document.createElement('div');
        bar.id = 'miniBarBackupHome';
        bar.className = 'card';
        bar.style.cssText = 'display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;padding:12px 16px;background:#f8fafc';
        bar.innerHTML = '<span style="font-size:13px;color:#475569">\ud83d\udcbe <strong>Sicurezza Dati & Backup:</strong> i pannelli completi sono in <em>Strumenti \u2192 Esporta / Backup</em>.</span>' +
          '<span style="display:flex;gap:8px"><button class="btn btn-green" style="padding:6px 12px;font-size:12px" onclick="if(typeof creaBackup===\'function\')creaBackup()">\ud83d\udcbe Crea backup ora</button>' +
          '<button class="btn btn-gray" style="padding:6px 12px;font-size:12px" onclick="mostra(\'esporta\')">\u2699\ufe0f Gestisci Backup & Excel</button></span>';
        dash.appendChild(bar);
      }
    }

    // 2. Compatta l'orologio in Home su una sola riga
    var dashEl = document.getElementById('page-dashboard');
    if (dashEl) {
      var firstCard = dashEl.querySelector('.card');
      if (firstCard && firstCard.textContent.indexOf(':') >= 0 && !firstCard.querySelector('table')) {
        firstCard.style.padding = '10px 20px';
        firstCard.style.display = 'flex';
        firstCard.style.justifyContent = 'space-between';
        firstCard.style.alignItems = 'center';
        firstCard.style.flexWrap = 'wrap';
        firstCard.style.gap = '10px';
        var divs = firstCard.querySelectorAll('div');
        if (divs.length >= 2) {
          divs[0].style.fontSize = '24px';
          divs[0].style.margin = '0';
          divs[1].style.fontSize = '14px';
          divs[1].style.margin = '0';
        }
      }
    }

    // 3. Raggruppa le voci secondarie del menu superiore dentro Strumenti
    if (!document.getElementById('btnMenuStrumenti')) {
      var secondarie = ['galleria','lavagna','liste','elabora','archivio','storico','widget','comandi','esporta','importa','logo'];
      var toMove = [];
      var navContainer = null;
      document.querySelectorAll('a[onclick], button[onclick]').forEach(function(el) {
        if (el.closest('.barra-nav')) return;
        var oc = (el.getAttribute('onclick') || '').toLowerCase();
        if (oc.indexOf('aprimodaleevento') >= 0 && el.getBoundingClientRect().top < 160) {
          el.style.display = 'none';
          return;
        }
        secondarie.forEach(function(k) {
          if (oc.indexOf("mostra('" + k + "')") >= 0 || oc.indexOf('mostra("' + k + '")') >= 0) {
            toMove.push(el);
            if (!navContainer) navContainer = el.parentElement;
          }
        });
      });

      if (toMove.length > 0 && navContainer) {
        var wrap = document.createElement('div');
        wrap.style.cssText = 'position:relative;display:inline-block';
        var btn = document.createElement('button');
        btn.id = 'btnMenuStrumenti';
        btn.type = 'button';
        btn.innerHTML = '\u2699\ufe0f Strumenti ▾';
        btn.style.cssText = 'background:rgba(255,255,255,0.16);color:white;border:1px solid rgba(255,255,255,0.3);padding:6px 12px;border-radius:8px;cursor:pointer;font-size:13px;font-weight:600';
        var drop = document.createElement('div');
        drop.style.cssText = 'display:none;position:absolute;right:0;top:110%;background:#1e293b;border:1px solid #334155;border-radius:10px;padding:6px;min-width:190px;z-index:9999;box-shadow:0 10px 25px rgba(0,0,0,0.4);flex-direction:column;gap:4px';
        toMove.forEach(function(el) {
          el.style.display = 'block';
          el.style.width = '100%';
          el.style.textAlign = 'left';
          el.style.margin = '0';
          el.style.borderRadius = '6px';
          el.addEventListener('click', function() { drop.style.display = 'none'; });
          drop.appendChild(el);
        });
        btn.onclick = function(e) { e.stopPropagation(); drop.style.display = (drop.style.display === 'flex') ? 'none' : 'flex'; };
        document.addEventListener('click', function() { drop.style.display = 'none'; });
        wrap.appendChild(btn);
        wrap.appendChild(drop);
        navContainer.appendChild(wrap);
      }
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', applicaUxFix);
  else applicaUxFix();

  // 4. Evidenzia sempre nel menu la sezione attiva
  function _aggiornaMenuAttivo(page) {
    if (!page) page = 'dashboard';
    var secondarie = ['galleria','lavagna','liste','elabora','archivio','storico','widget','comandi','esporta','importa','logo'];
    var isSec = secondarie.indexOf(page) >= 0;

    document.querySelectorAll('a[onclick*="mostra("], button[onclick*="mostra("]').forEach(function(el) {
      if (el.closest('.barra-nav')) return;
      var oc = (el.getAttribute('onclick') || '').toLowerCase();
      var attivo = (oc.indexOf("mostra('" + page + "')") >= 0 || oc.indexOf('mostra("' + page + '")') >= 0);
      if (attivo) {
        el.style.background = '#2563eb';
        el.style.color = '#ffffff';
        el.style.fontWeight = '700';
        el.style.boxShadow = '0 0 0 2px rgba(255,255,255,0.45)';
      } else {
        el.style.background = '';
        el.style.color = '';
        el.style.fontWeight = '';
        el.style.boxShadow = '';
      }
    });

    var btnStr = document.getElementById('btnMenuStrumenti');
    if (btnStr) {
      if (isSec) {
        btnStr.style.background = '#2563eb';
        btnStr.style.boxShadow = '0 0 0 2px rgba(255,255,255,0.45)';
      } else {
        btnStr.style.background = 'rgba(255,255,255,0.16)';
        btnStr.style.boxShadow = '';
      }
    }
  }

  if (typeof window.mostra === 'function') {
    var _origMostraActive = window.mostra;
    window.mostra = function(page) {
      var res = _origMostraActive.apply(this, arguments);
      _aggiornaMenuAttivo(page);
      return res;
    };
  }
  setTimeout(function() { _aggiornaMenuAttivo('dashboard'); }, 150);


  

  setTimeout(function() {
    var dashEl = document.getElementById('page-dashboard');
    if (dashEl) {
      var fc = dashEl.querySelector('.card');
      if (fc && fc.textContent.indexOf(':') >= 0 && !fc.querySelector('table')) {
        fc.style.cssText += ';display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:12px 20px;gap:4px';
      }
    }
    var btnS = document.getElementById('btnMenuStrumenti');
    var bil = document.querySelector('a[onclick*="bilancio"], button[onclick*="bilancio"]');
    if (btnS && bil && bil.parentElement) {
      var wrap = btnS.parentElement, nav = bil.parentElement;
      bil.insertAdjacentElement('afterend', wrap);
      nav.style.display = 'flex'; nav.style.flexWrap = 'nowrap'; nav.style.alignItems = 'center'; nav.style.gap = '4px';
      Array.from(nav.children).forEach(function(c) {
        if (c !== wrap) { c.style.whiteSpace = 'nowrap'; c.style.padding = '5px 8px'; c.style.fontSize = '12.5px'; }
      });
    }
  }, 150);


  // Spazio di sicurezza in fondo alle pagine per non coprire le ultime righe con i pulsanti flottanti
  var stFloat = document.createElement('style');
  stFloat.textContent = 'body { padding-bottom: 95px !important; } .pagina { padding-bottom: 40px !important; }';
  document.head.appendChild(stFloat);


  // Ponte rapido Scuole <-> ALTRO
  window.spostaScuolaInAltro = async function(sid, nome) {
    if (!confirm('Spostare "' + nome + '" da Scuole ad ALTRO? Gli eventuali eventi collegati passeranno in ALTRO.')) return;
    var r = await fetch('/api/scuole/sposta-altro', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({scuola_id: sid}) });
    var res = await r.json();
    if (res.success && typeof caricaDati === 'function') await caricaDati();
  };
  window.spostaAltroInScuola = async function(eid, luogo) {
    var nome = prompt('Nome della scuola a cui collegare questo evento:', luogo || '');
    if (!nome) return;
    var r = await fetch('/api/altro/sposta-scuola', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({evento_id: eid, nome_scuola: nome}) });
    var res = await r.json();
    if (res.success && typeof caricaDati === 'function') await caricaDati();
  };

  if (typeof window.renderScuole === 'function' && !window._wrapScuoleBridge) {
    window._wrapScuoleBridge = true;
    var _origRS = window.renderScuole;
    window.renderScuole = function() {
      var res = _origRS.apply(this, arguments);
      var g = document.getElementById('grigliaScuole');
      if (g && window.STATO) {
        var search = (document.getElementById('cercaScuole')?.value || '').toLowerCase();
        var lista = STATO.scuole.filter(function(s) { return !search || (s.nome||'').toLowerCase().includes(search) || (s.referente||'').toLowerCase().includes(search); });
        Array.from(g.children).forEach(function(card, idx) {
          var s = lista[idx];
          if (!s || card.querySelector('.btn-to-altro')) return;
          var btn = document.createElement('button');
          btn.type = 'button'; btn.className = 'btn-to-altro btn btn-gray';
          btn.style.cssText = 'margin-top:8px;padding:3px 8px;font-size:11px;display:block';
          btn.textContent = '\u2197 Sposta in ALTRO';
          btn.onclick = function(e) { e.stopPropagation(); spostaScuolaInAltro(s.id, s.nome); };
          card.appendChild(btn);
        });
      }
      return res;
    };
  }

  if (typeof window.renderAltro === 'function' && !window._wrapAltroBridge) {
    window._wrapAltroBridge = true;
    var _origRA = window.renderAltro;
    window.renderAltro = function() {
      var res = _origRA.apply(this, arguments);
      var tb = document.getElementById('altroBody');
      if (tb && window.STATO) {
        var f = STATO.eventi.filter(function(e) { return !e.scuola_id; }).sort(function(a,b) { return (b.data||'').localeCompare(a.data||''); });
        Array.from(tb.querySelectorAll('tr')).forEach(function(tr, idx) {
          var ev = f[idx];
          var lastTd = tr.lastElementChild;
          if (!ev || !lastTd || lastTd.querySelector('.btn-to-scuola')) return;
          var btn = document.createElement('button');
          btn.type = 'button'; btn.className = 'btn-to-scuola';
          btn.style.cssText = 'background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;border-radius:5px;padding:2px 6px;font-size:11px;cursor:pointer;margin-right:4px';
          btn.textContent = '\u2197 Scuola';
          btn.onclick = function(e) { e.stopPropagation(); spostaAltroInScuola(ev.id, ev.luogo || ev.iniziativa); };
          lastTd.insertBefore(btn, lastTd.firstChild);
        });
      }
      return res;
    };
  }

})();
