// ============================================================
// BRAAAP - Patch bilancio progressivo cumulativo (v2 corretta)
// Ridefinisce caricaBilancioProgressivo con riga TOTALE
// ============================================================
(function() {
  'use strict';

  window.caricaBilancioProgressivo = async function(da, a) {
    var cont = document.getElementById('bilancioContenuto');
    if (!cont) return;
    cont.innerHTML = '<div style="text-align:center;padding:40px;color:#90A4AE">\u23F3 Calcolo totale e progressione...</div>';

    try {
      var qs = [];
      if (da) qs.push('da=' + encodeURIComponent(da));
      if (a) qs.push('a=' + encodeURIComponent(a));
      var url = '/api/bilancio/progressivo' + (qs.length ? '?' + qs.join('&') : '');

      var r = await fetch(url);
      var data = await r.json();
      if (!data.success) {
        cont.innerHTML = '<div style="color:#DC2626">Errore: ' + (data.error || '?') + '</div>';
        return;
      }
      var b = data.dati;
      var lbl = (b.anno_da && b.anno_a)
        ? (String(b.anno_da) === String(b.anno_a) ? String(b.anno_da) : b.anno_da + ' - ' + b.anno_a)
        : 'Tutti gli anni';

      var html = '';
      if (typeof _renderBarraFiltroBilancio === 'function') {
        html += _renderBarraFiltroBilancio(b.anni_disponibili, b.anno_da, b.anno_a);
      }

      // --- 3 box riepilogo ---
      html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px">';
      html += '<div class="storico-stat" style="border-left-color:#16A34A"><div class="num" style="color:#16A34A">\u20AC ' + _fmtNum(b.entrate.totale.toFixed(2)) + '</div><div class="label">Entrate Totali (' + lbl + ')</div></div>';
      html += '<div class="storico-stat" style="border-left-color:#DC2626"><div class="num" style="color:#DC2626">\u20AC ' + _fmtNum(b.uscite.totale.toFixed(2)) + '</div><div class="label">Uscite Totali (' + lbl + ')</div></div>';
      var cMBox = b.margine >= 0 ? '#16A34A' : '#DC2626';
      html += '<div class="storico-stat" style="border-left-color:' + cMBox + '"><div class="num" style="color:' + cMBox + '">' + (b.margine >= 0 ? '+' : '') + '\u20AC ' + _fmtNum(b.margine.toFixed(2)) + '</div><div class="label">Margine Complessivo</div></div>';
      html += '</div>';

      // --- Tabella con riga TOTALE ---
      html += '<div class="storico-chart" style="overflow-x:auto">';
      html += '<h3 style="color:#0288D1;margin-bottom:10px">Andamento Annuale e Progressivo Cumulativo</h3>';

      if (!b.righe || b.righe.length === 0) {
        html += '<div style="color:#90A4AE;padding:12px">Nessun dato nel periodo.</div>';
      } else {
        html += '<table style="width:100%;border-collapse:collapse;font-size:13px"><thead><tr style="background:#f1f5f9;text-align:right">';
        html += '<th style="padding:8px;text-align:left">Anno</th>';
        html += '<th style="padding:8px;color:#16A34A">Entrate</th>';
        html += '<th style="padding:8px;color:#DC2626">Uscite</th>';
        html += '<th style="padding:8px">Margine</th>';
        html += '<th style="padding:8px;background:#ecfdf5;color:#15803d">Entrate Cum.</th>';
        html += '<th style="padding:8px;background:#fef2f2;color:#b91c1c">Uscite Cum.</th>';
        html += '<th style="padding:8px;background:#eff6ff;color:#1d4ed8">Saldo Cum.</th>';
        html += '</tr></thead><tbody>';

        b.righe.forEach(function(rg) {
          var cMRow = rg.margine >= 0 ? '#16A34A' : '#DC2626';
          var cCRow = rg.cum_margine >= 0 ? '#15803d' : '#b91c1c';
          html += '<tr style="border-bottom:1px solid #e2e8f0;text-align:right">';
          html += '<td style="padding:8px;text-align:left;font-weight:700"><a href="#" onclick="caricaBilancioAnno(' + rg.anno + ');return false;" style="color:#0288D1;text-decoration:none">' + rg.anno + ' \u2197</a></td>';
          html += '<td style="padding:8px;color:#16A34A">\u20AC ' + _fmtNum(rg.entrate.toFixed(2)) + '</td>';
          html += '<td style="padding:8px;color:#DC2626">\u20AC ' + _fmtNum(rg.uscite.toFixed(2)) + '</td>';
          html += '<td style="padding:8px;font-weight:700;color:' + cMRow + '">' + (rg.margine >= 0 ? '+' : '') + '\u20AC ' + _fmtNum(rg.margine.toFixed(2)) + '</td>';
          html += '<td style="padding:8px;background:#f0fdf4;font-weight:600;color:#15803d">\u20AC ' + _fmtNum(rg.cum_entrate.toFixed(2)) + '</td>';
          html += '<td style="padding:8px;background:#fef2f2;font-weight:600;color:#b91c1c">\u20AC ' + _fmtNum(rg.cum_uscite.toFixed(2)) + '</td>';
          html += '<td style="padding:8px;background:#eff6ff;font-weight:800;color:' + cCRow + '">' + (rg.cum_margine >= 0 ? '+' : '') + '\u20AC ' + _fmtNum(rg.cum_margine.toFixed(2)) + '</td>';
          html += '</tr>';
        });

        // === RIGA TOTALE ===
        var tEnt = (b.entrate && b.entrate.totale) ? b.entrate.totale : 0;
        var tUsc = (b.uscite && b.uscite.totale) ? b.uscite.totale : 0;
        var tMar = (typeof b.margine === 'number') ? b.margine : 0;

        html += '<tr style="background:#1e293b;color:#f1f5f9;font-weight:800;border-top:3px solid #0f172a;text-align:right">';
        html += '<td style="padding:10px;text-align:left;font-size:14px">TOTALE (' + lbl + ')</td>';
        html += '<td style="padding:10px;color:#86efac">\u20AC ' + _fmtNum(tEnt.toFixed(2)) + '</td>';
        html += '<td style="padding:10px;color:#fca5a5">\u20AC ' + _fmtNum(tUsc.toFixed(2)) + '</td>';
        html += '<td style="padding:10px;color:' + (tMar >= 0 ? '#86efac' : '#fca5a5') + '">' + (tMar >= 0 ? '+' : '') + '\u20AC ' + _fmtNum(tMar.toFixed(2)) + '</td>';
        html += '<td style="padding:10px;background:#1e3a8a;color:#bfdbfe">\u20AC ' + _fmtNum(tEnt.toFixed(2)) + '</td>';
        html += '<td style="padding:10px;background:#7f1d1d;color:#fecaca">\u20AC ' + _fmtNum(tUsc.toFixed(2)) + '</td>';
        html += '<td style="padding:10px;background:' + (tMar >= 0 ? '#14532d' : '#7f1d1d') + ';color:' + (tMar >= 0 ? '#bbf7d0' : '#fecaca') + '">' + (tMar >= 0 ? '+' : '') + '\u20AC ' + _fmtNum(tMar.toFixed(2)) + '</td>';
        html += '</tr>';

        html += '</tbody></table>';
      }

      // --- Ripartizione uscite ---
      html += '</div><div class="storico-chart"><h3 style="color:#475569;margin-bottom:10px">Ripartizione Uscite Totali (' + lbl + ')</h3><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px">';
      html += '<div style="padding:10px;background:#ecfeff;border-radius:8px"><strong>Magazzino:</strong> \u20AC ' + _fmtNum(b.uscite.magazzino.totale.toFixed(2)) + '</div>';
      html += '<div style="padding:10px;background:#f5f3ff;border-radius:8px"><strong>Inventario:</strong> \u20AC ' + _fmtNum(b.uscite.inventario.totale.toFixed(2)) + '</div>';
      html += '<div style="padding:10px;background:#fffbeb;border-radius:8px"><strong>Materiali:</strong> \u20AC ' + _fmtNum(b.uscite.materiali.totale.toFixed(2)) + '</div>';
      html += '<div style="padding:10px;background:#f8fafc;border-radius:8px"><strong>Altro:</strong> \u20AC ' + _fmtNum(b.uscite.altro.totale.toFixed(2)) + '</div>';
      html += '</div></div>';

      cont.innerHTML = html;
    } catch (e) {
      cont.innerHTML = '<div style="color:#DC2626">Errore di rete: ' + e.message + '</div>';
    }
  };

  console.log('[BRAAAP] Patch bilancio progressivo v2 caricata');

  // --- Hook automatico per vista Tutti gli anni + Filtro Cumulativo ---
  var _origCaricaBilancioAnno = window.caricaBilancioAnno;
  window.caricaBilancioAnno = async function(anno) {
    if (!anno || String(anno).toLowerCase() === 'tutti' || String(anno).toLowerCase() === 'all') {
      return await window.caricaBilancioProgressivo('', '');
    }
    if (typeof _origCaricaBilancioAnno === 'function') {
      var res = await _origCaricaBilancioAnno.apply(this, arguments);
      var cont = document.getElementById('bilancioContenuto');
      if (cont && !document.getElementById('bilFiltroDa') && typeof _renderBarraFiltroBilancio === 'function') {
        var anni = (window.STATO && window.STATO.anni_disponibili) ? window.STATO.anni_disponibili : [anno];
        cont.insertAdjacentHTML('afterbegin', _renderBarraFiltroBilancio(anni, anno, anno));
      }
      return res;
    }
  };


  // --- Collegamento automatico al selettore anno in alto e apertura scheda Bilancino ---
  function _aggiornaVistaBilancinoCorrente() {
    var sel = document.getElementById('selAnno') || document.getElementById('annoSelettore') || document.querySelector('select[onchange*="Anno"]');
    var val = sel ? sel.value : (typeof _annoCorrente !== 'undefined' ? _annoCorrente : '');
    window.caricaBilancioAnno(val || 'tutti');
  }

  if (typeof window.mostra === 'function') {
    var _origMostraBil = window.mostra;
    window.mostra = function(page) {
      var res = _origMostraBil.apply(this, arguments);
      if (page === 'bilancio') _aggiornaVistaBilancinoCorrente();
      return res;
    };
  }

  if (typeof window.cambiaAnno === 'function') {
    var _origCambiaAnnoBil = window.cambiaAnno;
    window.cambiaAnno = function() {
      var res = _origCambiaAnnoBil.apply(this, arguments);
      var pg = document.getElementById('page-bilancio');
      if (pg && pg.classList.contains('active')) _aggiornaVistaBilancinoCorrente();
      return res;
    };
  }


  // --- Ricerca Trasversale raggruppata per sezione con badge cliccabili ---
  window.eseguiRicercaBilancino = async function() {
    var q = (document.getElementById('bilCercaInput')?.value || '').trim();
    var box = document.getElementById('bilCercaRisultati');
    var btnClose = document.getElementById('btnPulisciCercaBil');
    if (!q) { pulisciRicercaBilancino(); return; }
    if (btnClose) btnClose.style.display = 'inline-block';
    box.style.display = 'block';
    box.innerHTML = '<div style="color:#64748b;font-size:13px">? Ricerca in tutte le sezioni...</div>';

    var r = await fetch('/api/bilancio/cerca?q=' + encodeURIComponent(q));
    var data = await r.json();
    if (!data.success) { box.innerHTML = '<div style="color:red">Errore ricerca</div>'; return; }

    window._bilSearchRes = data.risultati || {};
    var meta = [
      {k:'scuole', lbl:'← Scuole', col:'#2563eb', page:'scuole'},
      {k:'eventi', lbl:'← Eventi', col:'#0288d1', page:'eventi'},
      {k:'magazzino', lbl:'← Magazzino', col:'#0891b2', page:'magazzino'},
      {k:'materiali', lbl:'← Materiali', col:'#d97706', page:'materiali'},
      {k:'inventario', lbl:'← Inventario', col:'#7c3aed', page:'inventario'},
      {k:'entrate', lbl:'← Entrate', col:'#16a34a', page:null},
      {k:'uscite', lbl:'← Uscite', col:'#dc2626', page:null}
    ];

    if (data.totale_voci === 0) {
      box.innerHTML = '<div style="padding:10px;background:white;border-radius:8px;color:#64748b">Nessuna corrispondenza trovata per <strong>"' + q + '"</strong>.</div>';
      return;
    }

    var firstKey = null;
    var badges = '<div style="font-size:13px;font-weight:700;color:#1e293b;margin-bottom:8px">Ho trovato ' + data.totale_voci + ' corrispondenze ? clicca una sezione per vederle:</div>';
    badges += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px">';
    meta.forEach(function(m) {
      var arr = window._bilSearchRes[m.k] || [];
      if (arr.length > 0) {
        if (!firstKey) firstKey = m.k;
        badges += '<button class="btn" style="background:' + m.col + ';color:white;padding:6px 12px;font-size:12px;border-radius:20px" onclick="mostraSezioneRicercaBil(\'' + m.k + '\')">' + m.lbl + ' (' + arr.length + ')</button>';
      }
    });
    badges += '</div><div id="bilCercaDettaglio"></div>';
    box.innerHTML = badges;
    if (firstKey) mostraSezioneRicercaBil(firstKey);
  };

  window.mostraSezioneRicercaBil = function(key) {
    var det = document.getElementById('bilCercaDettaglio');
    var arr = (window._bilSearchRes && window._bilSearchRes[key]) || [];
    if (!det) return;
    var pageMap = {scuole:'scuole', eventi:'eventi', magazzino:'magazzino', materiali:'materiali', inventario:'inventario'};
    var totImp = arr.reduce(function(s, x) { return s + (Number(x.importo) || 0); }, 0);

    var html = '<div style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:12px">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #f1f5f9">';
    html += '<strong style="text-transform:uppercase;font-size:12px;color:#475569">Dettaglio ' + key + ' (' + arr.length + ')</strong>';
    if (totImp !== 0) html += '<strong style="color:#0f172a;font-size:13px">Subtotale:  ' + _fmtNum(totImp.toFixed(2)) + '</strong>';
    html += '</div>';

    arr.forEach(function(item) {
      var impHtml = item.importo != null ? '<strong> ' + _fmtNum(Number(item.importo).toFixed(2)) + '</strong>' : '';
      var editBtn = '';
      if (item._ref) {
        var vObj = {_ref: item._ref, data: item.data, descrizione: item.titolo, importo: item.importo, quantita: item.quantita, prezzo_unitario: item.prezzo_unitario};
        editBtn = '<button class="btn btn-blue" style="padding:3px 8px;font-size:11px" title="Modifica" onclick="apriModificaVoceBilancino(\'' + encodeURIComponent(JSON.stringify(vObj)) + '\')">←</button>';
      }
      var goBtn = pageMap[key] ? '<button class="btn btn-gray" style="padding:3px 8px;font-size:11px" title="Vai alla scheda" onclick="mostra(\'' + pageMap[key] + '\')">? Apri</button>' : '';
      html += '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #f8fafc;font-size:13px">';
      html += '<span>' + (item.data ? '<strong>' + item.data + '</strong> ? ' : '') + '<strong>' + item.titolo + '</strong>' + (item.dettaglio ? ' <span style="color:#64748b">(' + item.dettaglio + ')</span>' : '') + '</span>';
      html += '<span style="display:flex;align-items:center;gap:6px;white-space:nowrap">' + impHtml + editBtn + goBtn + '</span></div>';
    });
    html += '</div>';
    det.innerHTML = html;
  };

  window.pulisciRicercaBilancino = function() {
    var inp = document.getElementById('bilCercaInput');
    var box = document.getElementById('bilCercaRisultati');
    var btn = document.getElementById('btnPulisciCercaBil');
    if (inp) inp.value = '';
    if (box) { box.style.display = 'none'; box.innerHTML = ''; }
    if (btn) btn.style.display = 'none';
  };

})();