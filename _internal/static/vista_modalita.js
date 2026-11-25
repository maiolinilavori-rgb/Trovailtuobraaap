function applicaEtichetteProfilo(ui){
  if(!ui)return;
  var map=[['📅 Eventi',ui.eventi],['🏫 Scuole',ui.scuole],['📦 Eventi ALTRO',ui.altro],['📦 ALTRO',ui.altro],['📦 Bracc.',ui.bracc],['🏅 Med.',ui.med],['🔖 Ades.',ui.ades],['🏆 Coppe',ui.coppe],['📦 Materiali',ui.mat]];
  var walk=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,null,false),n;
  while((n=walk.nextNode())){
    if(!n.parentElement||/SCRIPT|STYLE|SELECT|OPTION/.test(n.parentElement.tagName))continue;
    var t=n.nodeValue;
    for(var i=0;i<map.length;i++){if(t.indexOf(map[i][0])!==-1)t=t.split(map[i][0]).join(map[i][1]);}
    if(t!==n.nodeValue)n.nodeValue=t;
  }
}
(function() {
  if (window._gestoreVisteCelleInit) return;
  window._gestoreVisteCelleInit = true;
  var css = document.createElement('style');
  css.textContent = [
    '.barra-vista-box{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin:0 0 12px;padding:6px 10px;background:var(--card,#fff);border:1px solid rgba(148,163,184,.28);border-radius:10px}',
    '.barra-vista-grp{display:flex;align-items:center;gap:5px;flex-wrap:wrap}',
    '.btn-mode-sel{padding:5px 11px;border-radius:7px;border:1px solid rgba(148,163,184,.35);background:transparent;color:inherit;font-size:12px;font-weight:600;cursor:pointer}',
    '.btn-mode-sel.attivo{background:#0288D1;color:#fff;border-color:#0288D1}',
    '.pannello-colonne{display:none;margin:0 0 12px;padding:10px 12px;background:var(--card,#fff);border:1px solid #0288D1;border-radius:10px}',
    '.pannello-colonne.aperto{display:block}',
    '.col-resizer{position:absolute;top:0;right:-3px;width:8px;height:100%;cursor:col-resize;user-select:none;z-index:10;border-right:2px solid transparent;transition:border-color .15s}',
    '.col-resizer:hover,.col-resizer.attivo{border-right-color:#0288D1;background:rgba(2,136,209,.12)}',
    'table.tabella-ridimensionabile{table-layout:fixed!important}',
    'table.tabella-ridimensionabile th,table.tabella-ridimensionabile td{position:relative;overflow:hidden;text-overflow:ellipsis}',
    '.vista-compatta [id^="griglia"]>.card>*{position:relative;min-width:0}',
    '.col-chip{display:inline-flex;align-items:center;gap:5px;padding:4px 8px;margin:3px;border-radius:7px;background:rgba(2,136,209,.08);border:1px solid rgba(2,136,209,.25);font-size:12px}',
    '.col-chip button{border:none;background:rgba(0,0,0,.08);border-radius:4px;cursor:pointer;padding:1px 5px;font-size:11px;font-weight:700}',
    '.vista-compatta table{width:100%;border-collapse:collapse;font-size:12.5px}',
    '.vista-compatta table th{background:rgba(2,136,209,.08);padding:6px 8px!important;font-size:11.5px!important;text-transform:uppercase;white-space:nowrap}',
    '.vista-compatta table td{padding:5px 8px!important;border-bottom:1px solid rgba(148,163,184,.2)}',
    '.vista-compatta [id^="griglia"],.vista-compatta [id^="materialiContainer"]{display:flex!important;flex-direction:column!important;gap:4px!important}',
    '.vista-compatta [id^="griglia"]>.card,.vista-compatta [id^="materialiContainer"]>.card{display:grid!important;grid-template-columns:repeat(auto-fit,minmax(140px,1fr))!important;align-items:center!important;gap:8px!important;padding:7px 12px!important;margin:0!important;border-radius:8px!important;font-size:12.5px!important}',
    '.vista-compatta [id^="griglia"]>.card h3{font-size:13.5px!important;margin:0!important}',
    '.vista-standard [id^="griglia"]{grid-template-columns:repeat(auto-fill,minmax(260px,1fr))!important;gap:12px!important}',
    '.vista-dettagli [id^="griglia"]{grid-template-columns:repeat(auto-fill,minmax(340px,1fr))!important;gap:16px!important}',
    '.vista-dettagli [id^="griglia"]>.card{padding:18px!important;font-size:14px!important;line-height:1.5!important}',
    '.vista-dettagli table td,.vista-dettagli table th{padding:10px 12px!important;font-size:13.5px!important}'
  ].join('\n');
  document.head.appendChild(css);
  var PAGINE=['page-inventario','page-eventi','page-scuole','page-magazzino','page-materiali','page-altro','page-rubrica','page-task','page-archivio','page-bilancio','page-liste'];
  function _getCfg(p){try{return JSON.parse(localStorage.getItem('braaap_cols_'+p)||'null');}catch(e){return null;}}
  function _setCfg(p,c){try{localStorage.setItem('braaap_cols_'+p,JSON.stringify(c));}catch(e){}}
  function _getW(p){try{return JSON.parse(localStorage.getItem('braaap_widths_'+p)||'{}');}catch(e){return {};}}
  function _setW(p,w){try{localStorage.setItem('braaap_widths_'+p,JSON.stringify(w));}catch(e){}}
  function _attivaResize(pid){
    var pg=document.getElementById(pid);if(!pg)return;setTimeout(function(){_attivaResize(pid);},20);
    var wmap=_getW(pid),tbl=pg.querySelector('table');
    if(tbl&&tbl.tHead&&tbl.tHead.rows.length){
      tbl.classList.add('tabella-ridimensionabile');
      var ths=Array.from(tbl.tHead.rows.item(0).cells);
      ths.forEach(function(th,i){
        var oi=th.dataset.oi||String(i);
        if(wmap[oi]){th.style.width=wmap[oi]+'px';th.style.minWidth=wmap[oi]+'px';}
        if(th.querySelector('.col-resizer'))return;
        var rz=document.createElement('span');rz.className='col-resizer';rz.title='Trascina per allargare/stringere';
        rz.onmousedown=function(e){
          e.preventDefault();e.stopPropagation();rz.classList.add('attivo');
          var startX=e.clientX,startW=th.getBoundingClientRect().width;
          function onMove(ev){var nw=Math.max(48,Math.round(startW+(ev.clientX-startX)));th.style.width=nw+'px';th.style.minWidth=nw+'px';wmap[oi]=nw;}
          function onUp(){rz.classList.remove('attivo');document.removeEventListener('mousemove',onMove);document.removeEventListener('mouseup',onUp);_setW(pid,wmap);}
          document.addEventListener('mousemove',onMove);document.addEventListener('mouseup',onUp);
        };
        th.appendChild(rz);
      });
      tbl.querySelectorAll('td').forEach(function(td){var txt=(td.textContent||'').trim();if(/^[\d.,\s€+-]+$/.test(txt))td.style.whiteSpace='nowrap';});
      return;
    }
    var gr=pg.querySelector('[id^="griglia"],[id^="materialiContainer"]');
    if(gr&&gr.children.length&&pg.classList.contains('vista-compatta')){
      var cards=Array.from(gr.children),cols=[];
      cards.forEach(function(card){
        Array.from(card.children).forEach(function(cell,i){
          var oi=cell.dataset.oi||String(i);cols[i]=wmap[oi]?wmap[oi]+'px':'minmax(110px,1fr)';
          if(cell.style.display==='none')cols[i]='0px';
          if(cell.querySelector('.col-resizer'))return;
          var rz=document.createElement('span');rz.className='col-resizer';rz.title='Trascina per allargare/stringere';
          rz.onmousedown=function(e){
            e.preventDefault();e.stopPropagation();rz.classList.add('attivo');
            var startX=e.clientX,startW=cell.getBoundingClientRect().width;
            function onMove(ev){
              var nw=Math.max(55,Math.round(startW+(ev.clientX-startX)));wmap[oi]=nw;
              cards.forEach(function(c2){var tpl=Array.from(c2.children).map(function(k,idx){if(k.style.display==='none')return'';var koi=k.dataset.oi||String(idx);return wmap[koi]?wmap[koi]+'px':'minmax(110px,1fr)';}).filter(Boolean).join(' ');c2.style.setProperty('grid-template-columns',tpl,'important');});
            }
            function onUp(){rz.classList.remove('attivo');document.removeEventListener('mousemove',onMove);document.removeEventListener('mouseup',onUp);_setW(pid,wmap);}
            document.addEventListener('mousemove',onMove);document.addEventListener('mouseup',onUp);
          };
          cell.appendChild(rz);
        });
        var tplInit=Array.from(card.children).map(function(k,idx){if(k.style.display==='none')return'';var koi=k.dataset.oi||String(idx);return wmap[koi]?wmap[koi]+'px':'minmax(110px,1fr)';}).filter(Boolean).join(' ');
        if(tplInit)card.style.setProperty('grid-template-columns',tplInit,'important');
      });
    }
  }
  function applicaCelle(pid){
    var pg=document.getElementById(pid);if(!pg)return;setTimeout(function(){_attivaResize(pid);},20);
    var cfg=_getCfg(pid),tbl=pg.querySelector('table');
    if(tbl&&tbl.tHead&&tbl.tHead.rows.length){
      var ths=Array.from(tbl.tHead.rows.item(0).cells);
      ths.forEach(function(th,i){if(!th.dataset.oi){th.dataset.oi=i;th.dataset.on=(th.textContent||('Col '+(i+1))).trim();}});
      if(!cfg||!Array.isArray(cfg.ordine)||cfg.ordine.length!==ths.length)cfg={ordine:ths.map(function(_,i){return i;}),nascoste:[]};
      var rows=[tbl.tHead.rows.item(0)].concat(tbl.tBodies.length?Array.from(tbl.tBodies.item(0).rows):[]);
      rows.forEach(function(tr){
        var cs=Array.from(tr.cells);if(cs.length!==ths.length)return;
        var m={};cs.forEach(function(c,i){if(!c.dataset.oi)c.dataset.oi=i;m[c.dataset.oi]=c;});
        cfg.ordine.forEach(function(oi){var el=m[oi];if(!el)return;el.style.display=cfg.nascoste.indexOf(oi)!==-1?'none':'';tr.appendChild(el);});
      });return;
    }
    var gr=pg.querySelector('[id^="griglia"],[id^="materialiContainer"]');
    if(gr&&gr.children.length&&cfg&&Array.isArray(cfg.ordine)){
      Array.from(gr.children).forEach(function(card){
        var bs=Array.from(card.children),m={};bs.forEach(function(b,i){if(!b.dataset.oi)b.dataset.oi=i;m[b.dataset.oi]=b;});
        cfg.ordine.forEach(function(oi){var el=m[oi];if(!el)return;el.style.display=cfg.nascoste.indexOf(oi)!==-1?'none':'';card.appendChild(el);});
      });
    }
  }
  function renderPan(pid){
    var pg=document.getElementById(pid),pan=pg&&pg.querySelector('.pannello-colonne');if(!pan)return;
    var nomi=[],tbl=pg.querySelector('table');
    if(tbl&&tbl.tHead&&tbl.tHead.rows.length){
      Array.from(tbl.tHead.rows.item(0).cells).forEach(function(th,i){var oi=parseInt(th.dataset.oi||i,10);nomi[oi]=th.dataset.on||('Col '+(oi+1));});
    }else{
      var gr=pg.querySelector('[id^="griglia"],[id^="materialiContainer"]'),pr=gr&&gr.firstElementChild;
      if(pr)Array.from(pr.children).forEach(function(el,i){var oi=parseInt(el.dataset.oi||i,10);var t=(el.textContent||'').trim().replace(/\s+/g,' ').slice(0,18);nomi[oi]='Cella '+(oi+1)+(t?' ('+t+')':'');});
    }
    if(!nomi.length){pan.innerHTML='<small>Nessuna cella configurabile qui.</small>';return;}
    var cfg=_getCfg(pid);if(!cfg||!Array.isArray(cfg.ordine)||cfg.ordine.length!==nomi.length){cfg={ordine:nomi.map(function(_,i){return i;}),nascoste:[]};_setCfg(pid,cfg);}
    var h='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;gap:6px"><strong style="font-size:12px">🎛️ Posizione celle (salvata in automatico)</strong><div style="display:flex;gap:5px"><button type="button" class="btn-mode-sel" data-act="rst">↺ Reset</button><button type="button" class="btn-mode-sel attivo" data-act="ok">✓ Fine</button></div></div><div>';
    cfg.ordine.forEach(function(oi,pos){
      var vis=cfg.nascoste.indexOf(oi)===-1;
      h+='<span class="col-chip"><input type="checkbox" data-oi="'+oi+'" '+(vis?'checked':'')+'> '+nomi.at(oi)+(pos>0?' <button type="button" data-mv="-1" data-p="'+pos+'">◀</button>':'')+(pos<cfg.ordine.length-1?' <button type="button" data-mv="1" data-p="'+pos+'">▶</button>':'')+'</span>';
    });
    pan.innerHTML=h+'</div>';
    pan.querySelectorAll('input').forEach(function(cb){cb.onchange=function(){var oi=parseInt(cb.dataset.oi,10),ix=cfg.nascoste.indexOf(oi);if(cb.checked&&ix!==-1)cfg.nascoste.splice(ix,1);if(!cb.checked&&ix===-1)cfg.nascoste.push(oi);_setCfg(pid,cfg);applicaCelle(pid);};});
    pan.querySelectorAll('button[data-mv]').forEach(function(b){b.onclick=function(){var p=parseInt(b.dataset.p,10),t=p+parseInt(b.dataset.mv,10),x=cfg.ordine.at(p);cfg.ordine.splice(p,1);cfg.ordine.splice(t,0,x);_setCfg(pid,cfg);applicaCelle(pid);renderPan(pid);};});
    pan.querySelector('[data-act="rst"]').onclick=function(){localStorage.removeItem('braaap_cols_'+pid);localStorage.removeItem('braaap_widths_'+pid);location.reload();};
    pan.querySelector('[data-act="ok"]').onclick=function(){pan.classList.remove('aperto');};
  }
  function setVista(pid,m){
    var pg=document.getElementById(pid);if(!pg)return;setTimeout(function(){_attivaResize(pid);},20);
    pg.classList.remove('vista-compatta','vista-standard','vista-dettagli','vista-pag-compatta','vista-pag-estesa','vista-pag-dettagli');
    pg.classList.add('vista-'+m);try{localStorage.setItem('braaap_mode_'+pid,m);}catch(e){}
    pg.querySelectorAll('.btn-mode-sel[data-m]').forEach(function(b){b.classList.toggle('attivo',b.dataset.m===m);});
    applicaCelle(pid);
  }
  document.addEventListener('DOMContentLoaded',function(){
    document.querySelectorAll('.barra-viste').forEach(function(e){(e.parentElement||e).remove();});
    PAGINE.forEach(function(pid){
      var pg=document.getElementById(pid);if(!pg)return;setTimeout(function(){_attivaResize(pid);},20);
      if(!pg.querySelector('.barra-vista-box')){
        var box=document.createElement('div');box.className='barra-vista-box';
        box.innerHTML='<div class="barra-vista-grp"><span style="font-size:11.5px;font-weight:700;opacity:.75;margin-right:4px">Vista:</span><button type="button" class="btn-mode-sel" data-m="compatta">☰ Compatta</button><button type="button" class="btn-mode-sel" data-m="standard">⊞ Standard</button><button type="button" class="btn-mode-sel" data-m="dettagli">📇 Dettagli</button></div><button type="button" class="btn-mode-sel" data-act="cols">⚙️ Celle / Colonne</button>';
        var pan=document.createElement('div');pan.className='pannello-colonne';
        pg.insertBefore(pan,pg.firstChild);pg.insertBefore(box,pan);
        box.querySelectorAll('[data-m]').forEach(function(b){b.onclick=function(){setVista(pid,b.dataset.m);};});
        box.querySelector('[data-act="cols"]').onclick=function(){pan.classList.toggle('aperto');if(pan.classList.contains('aperto'))renderPan(pid);};
      }
      setVista(pid,localStorage.getItem('braaap_mode_'+pid)||'standard');
    });
    setInterval(function(){PAGINE.forEach(function(pid){var pg=document.getElementById(pid);if(pg&&pg.classList.contains('attiva'))applicaCelle(pid);});},700);
  });
})();



  window.esportaIntelligente=function(){
    var annoDef=new Date().getFullYear();
    var anno=prompt('Inserisci l\'anno per il Report Intelligente (Riepilogo KPI, Bilancio, Margini Eventi, Patrimonio):',annoDef);
    if(anno===null)return;
    anno=parseInt(anno,10)||annoDef;
    window.location.href='/api/esporta/intelligente.xlsx?anno='+anno;
  };
  


  

  (function(){
    function addSmartBtn(){
      if(document.getElementById('btnSmartExport'))return;
      var pg=document.getElementById('page-esporta');
      if(!pg)return;
      var box=document.createElement('div');
      box.id='btnSmartExport';
      box.style.cssText='background:linear-gradient(135deg,#16A34A,#15803D);color:#fff;padding:16px 20px;border-radius:12px;margin:0 0 18px 0;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;box-shadow:0 6px 18px rgba(22,163,74,.28)';
      box.innerHTML='<div><div style="font-size:16px;font-weight:800">📊 Report Intelligente (Excel Multi-Foglio)</div><div style="font-size:12px;opacity:.92;margin-top:2px">Genera in 1 clic: Riepilogo Executive KPI, Bilancio Annuale, Margini per Evento e Patrimonio & Scorte</div></div><button type="button" onclick="esportaIntelligente()" style="background:#fff;color:#15803D;border:none;padding:10px 18px;border-radius:9px;font-weight:800;font-size:13px;cursor:pointer;box-shadow:0 2px 6px rgba(0,0,0,.15)">⬇️ Scarica Report Excel</button>';
      var titolo=pg.querySelector('h1,h2,.page-title');
      if(titolo&&titolo.nextSibling)pg.insertBefore(box,titolo.nextSibling);
      else pg.insertBefore(box,pg.firstChild);
    }
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',addSmartBtn);
    else addSmartBtn();
    setTimeout(addSmartBtn,400);
  })();

  window.avviaAutoanalisi=function(){
    var m=document.getElementById('modalCheckSystem');
    if(!m){
      m=document.createElement('div');
      m.id='modalCheckSystem';
      m.style.cssText='position:fixed;inset:0;background:rgba(15,23,42,.68);z-index:99999;display:flex;align-items:center;justify-content:center;padding:16px';
      m.innerHTML='<div style="background:#fff;color:#0f172a;max-width:680px;width:100%;border-radius:14px;padding:22px;box-shadow:0 20px 45px rgba(0,0,0,.35);max-height:88vh;overflow:auto"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px"><h3 style="margin:0;font-size:18px">🛠️ Autoanalisi & Autoriparazione Sistema</h3><button type="button" onclick="document.getElementById(\'modalCheckSystem\').style.display=\'none\'" style="border:none;background:#e2e8f0;border-radius:8px;padding:6px 10px;cursor:pointer;font-weight:700">✕</button></div><div id="checkSystemBody" style="font-size:13px;line-height:1.55">Analisi in corso...</div></div>';
      document.body.appendChild(m);
    }
    m.style.display='flex';
    var body=document.getElementById('checkSystemBody');
    body.innerHTML='⏳ Controllo sintassi Python, integrità database, stock magazzino e analisi log con IA in corso...';
    fetch('/api/check-system/esegui',{method:'POST'}).then(function(r){return r.json();}).then(function(d){
      if(!d.success){body.innerHTML='❌ Errore durante il check.';return;}
      var badge=d.stato_ok?'<span style="background:#DCFCE7;color:#166534;padding:4px 10px;border-radius:999px;font-weight:800">✅ SISTEMA SANO</span>':'<span style="background:#FEE2E2;color:#991B1B;padding:4px 10px;border-radius:999px;font-weight:800">⚠️ ANOMALIA RILEVATA</span>';
      var ripHtml=(d.riparazioni_dati||[]).map(function(x){return '<li>'+x+'</li>';}).join('')||'<li>Nessuna anomalia dati rilevata</li>';
      var errHtml=(d.errori_sintassi||[]).length?'<div style="background:#FEF2E2;border:1px solid #FCA5A5;padding:10px;border-radius:8px;margin-top:10px;color:#991B1B"><b>Errori sintassi:</b><br>'+d.errori_sintassi.join('<br>')+'</div>':'';
      body.innerHTML='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">'+badge+'<span style="font-size:11px;color:#64748b">'+d.timestamp+'</span></div>'
        +'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px">'
        +'<div style="background:#F8FAFC;padding:10px;border-radius:8px;border:1px solid #E2E8F0"><div style="font-size:11px;color:#64748b">File Python</div><b>'+d.file_python_controllati+' OK</b></div>'
        +'<div style="background:#F8FAFC;padding:10px;border-radius:8px;border:1px solid #E2E8F0"><div style="font-size:11px;color:#64748b">Spazio Disco</div><b>'+d.spazio_libero_gb+' GB</b></div>'
        +'<div style="background:#F8FAFC;padding:10px;border-radius:8px;border:1px solid #E2E8F0"><div style="font-size:11px;color:#64748b">Backup Disponibili</div><b>'+d.numero_backup+'</b></div>'
        +'</div>'
        +'<div style="margin-bottom:10px"><b>🔧 Azioni & Autoriparazione Dati:</b><ul style="margin:6px 0 0 18px;padding:0">'+ripHtml+'</ul></div>'
        +errHtml
        +'<div style="background:#EFF6FF;border:1px solid #BFDBFE;padding:12px;border-radius:9px;margin-top:10px"><b>🧠 Diagnosi AI sui Log:</b><div style="margin-top:4px;white-space:pre-wrap">'+d.analisi_ai+'</div></div>'
        +'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:16px;padding-top:12px;border-top:1px solid #E2E8F0">'
        +'<button type="button" onclick="ripristinaBackupEmergenza()" style="background:#F59E0B;color:#fff;border:none;padding:9px 14px;border-radius:8px;font-weight:700;cursor:pointer">⏪ Ripristina Ultimo Backup Sano</button>'
        +'<button type="button" onclick="location.reload()" style="background:#0F172A;color:#fff;border:none;padding:9px 16px;border-radius:8px;font-weight:700;cursor:pointer">🔄 Ricarica Interfaccia</button>'
        +'</div>';
    }).catch(function(e){body.innerHTML='❌ Errore connessione server: '+e;});
  };
  window.ripristinaBackupEmergenza=function(){
    if(!confirm('Vuoi ripristinare l\'ultimo backup sano del database?'))return;
    fetch('/api/check-system/ripristina-ultimo',{method:'POST'}).then(function(r){return r.json();}).then(function(d){
      alert(d.messaggio||d.error||'Operazione completata');
      if(d.success)location.reload();
    });
  };
  (function(){
    function addCheckBtn(){
      var targets=['page-comandi','page-esporta'];
      targets.forEach(function(pid){
        var pg=document.getElementById(pid);
        if(!pg||pg.querySelector('.btn-check-system'))return;
        var b=document.createElement('button');
        b.type='button';
        b.className='btn-check-system';
        b.innerHTML='🛠️ Autoanalisi & Autoriparazione';
        b.style.cssText='background:linear-gradient(135deg,#0F172A,#1E293B);color:#fff;border:1px solid #334155;padding:11px 16px;border-radius:10px;font-weight:700;font-size:13px;cursor:pointer;margin:0 0 16px 0;display:inline-flex;align-items:center;gap:8px;box-shadow:0 4px 12px rgba(15,23,42,.22)';
        b.onclick=window.avviaAutoanalisi;
        var smart=document.getElementById('btnSmartExport');
        if(pid==='page-esporta'&&smart&&smart.nextSibling)pg.insertBefore(b,smart.nextSibling);
        else pg.insertBefore(b,pg.firstChild);
      });
    }
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',addCheckBtn);
    else addCheckBtn();
    setTimeout(addCheckBtn,500);
  })();


(function(){
  function initProfiliNav(){
    var sel=document.getElementById('selProfiloDemo');
    if(!sel||sel.dataset.bound)return;
    sel.dataset.bound='1';
    fetch('/api/profili/lista').then(function(r){return r.json();}).then(function(d){
      if(!d.success)return;applicaEtichetteProfilo(d.ui);setTimeout(function(){applicaEtichetteProfilo(d.ui);},800);
      sel.innerHTML=d.profili.map(function(p){return '<option value="'+p.id+'"'+(p.id===d.attivo?' selected':'')+'>'+p.label+'</option>';}).join('');
    });
    sel.onchange=function(){
      sel.disabled=true;
      fetch('/api/profili/attiva',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profilo:sel.value})}).then(function(r){return r.json();}).then(function(d){
        if(d.success)location.reload();
        else{alert(d.error||'Errore cambio profilo');sel.disabled=false;}
      });
    };
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initProfiliNav);
  else initProfiliNav();
  setTimeout(initProfiliNav,500);
})();