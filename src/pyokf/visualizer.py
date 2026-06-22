"""OKF bundle HTML visualizer — generates a self-contained single-file viewer."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyokf.models import OKFConcept


def _concept_to_dict(c: "OKFConcept") -> dict:
    ts = ""
    if c.timestamp:
        try:
            ts = c.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            ts = str(c.timestamp)
    return {
        "type": c.type.value,
        "title": c.title,
        "description": c.description,
        "resource": c.resource,
        "tags": c.tags,
        "timestamp": ts,
        "content": c.content,
        "output_path": c.output_path,
    }


def generate_html(concepts: list) -> str:
    """Generate a self-contained HTML viewer for an OKF bundle.

    Returns a complete HTML string with embedded CSS, JS, and data.
    No external dependencies — works offline, open directly in any browser.
    """
    data = sorted(
        [_concept_to_dict(c) for c in concepts],
        key=lambda c: c["title"],
    )
    # Replace </ to prevent </script> from breaking the embedded JSON block
    data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    n = len(data)
    s = "s" if n != 1 else ""

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f"<title>OKF Viewer — {n} concept{s}</title>\n"
        "<style>\n" + _CSS + "\n</style>\n"
        "</head>\n"
        "<body>\n"
        '<div id="app">\n'
        '  <header id="hdr">\n'
        '    <div class="hl">\n'
        '      <span class="logo">OKF</span>\n'
        f'      <span class="sub">{n} concept{s}</span>\n'
        "    </div>\n"
        '    <div class="hc">'
        '<input id="search" type="search" placeholder="Search concepts…"'
        ' autocomplete="off" spellcheck="false">'
        "</div>\n"
        '    <div class="hr" id="filters"></div>\n'
        "  </header>\n"
        '  <div class="layout">\n'
        '    <aside id="sidebar"><ul id="list"></ul></aside>\n'
        '    <main id="detail"><p class="empty">← Select a concept</p></main>\n'
        "  </div>\n"
        "</div>\n"
        "<script>\n(function(){\n"
        "const DATA=" + data_json + ";\n"
        + _JS
        + "\n})();\n</script>\n"
        "</body>\n"
        "</html>\n"
    )


# ---------------------------------------------------------------------------
# Embedded CSS
# ---------------------------------------------------------------------------

_CSS = """\
:root{
  --mod:#3b82f6;--cls:#10b981;--api:#f59e0b;--fn:#6b7280;
  --bg:#fff;--sbg:#f8fafc;--border:#e2e8f0;
  --text:#1e293b;--muted:#64748b;--active-bg:#eff6ff;--active-bd:#3b82f6;
  --r:6px;--hh:52px;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  font-size:14px;color:var(--text);background:var(--bg);height:100vh;overflow:hidden}
#app{display:flex;flex-direction:column;height:100vh}

/* ── Header ── */
header#hdr{display:flex;align-items:center;gap:12px;padding:0 16px;
  height:var(--hh);border-bottom:1px solid var(--border);background:var(--bg);flex-shrink:0}
.hl{display:flex;align-items:center;gap:8px;flex-shrink:0}
.logo{font-weight:700;font-size:15px;letter-spacing:-.3px}
.sub{font-size:12px;color:var(--muted);background:#f1f5f9;padding:2px 8px;border-radius:99px}
.hc{flex:1;max-width:340px}
#search{width:100%;padding:6px 12px;border:1px solid var(--border);border-radius:var(--r);
  font-size:13px;outline:none;background:var(--sbg);color:var(--text)}
#search:focus{border-color:var(--active-bd);background:#fff}
.hr{display:flex;gap:6px;align-items:center;margin-left:auto;flex-shrink:0;flex-wrap:wrap}

/* ── Filter buttons ── */
.fb{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;
  border:1px solid var(--border);border-radius:99px;font-size:12px;font-weight:500;
  cursor:pointer;background:var(--sbg);color:var(--muted);transition:all .12s}
.fb:hover{background:#e2e8f0}
.fb.on{color:#fff;border-color:transparent}
.fb .dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.fb .cnt{opacity:.7;font-size:11px}

/* ── Layout ── */
.layout{display:flex;flex:1;overflow:hidden}

/* ── Sidebar ── */
aside#sidebar{width:272px;flex-shrink:0;border-right:1px solid var(--border);
  background:var(--sbg);overflow-y:auto}
#list{list-style:none;padding:6px 0}
.ci{display:flex;align-items:flex-start;gap:9px;padding:8px 14px;
  cursor:pointer;border-left:3px solid transparent;transition:background .1s}
.ci:hover{background:#f1f5f9}
.ci.on{background:var(--active-bg);border-left-color:var(--active-bd)}
.ci-dot{flex-shrink:0;margin-top:4px;width:8px;height:8px;border-radius:50%}
.ci-body{overflow:hidden;min-width:0}
.ci-title{font-size:13px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ci-desc{font-size:11px;color:var(--muted);margin-top:2px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.nores{padding:20px 14px;color:var(--muted);font-size:13px}

/* ── Detail panel ── */
main#detail{flex:1;overflow-y:auto;padding:30px 40px;max-width:900px}
.empty{color:var(--muted);padding-top:48px}

.dh{margin-bottom:22px}
.dt{font-size:22px;font-weight:700;margin-bottom:10px;word-break:break-word}
.dm{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-bottom:10px}
.badge{display:inline-block;padding:2px 9px;border-radius:99px;
  font-size:11px;font-weight:600;letter-spacing:.3px;color:#fff}
.tag{display:inline-block;padding:2px 8px;border-radius:99px;
  font-size:11px;background:#f1f5f9;color:var(--muted)}
.dd{font-size:14px;color:var(--muted);line-height:1.5;margin-bottom:16px}
hr.dhr{border:none;border-top:1px solid var(--border);margin-bottom:20px}

/* ── Markdown ── */
.md{font-size:14px;line-height:1.75;color:var(--text)}
.md h1{font-size:20px;font-weight:700;margin:0 0 12px}
.md h2{font-size:15px;font-weight:600;margin:22px 0 8px;padding-bottom:5px;
  border-bottom:1px solid var(--border)}
.md h3{font-size:13.5px;font-weight:600;margin:16px 0 5px;color:#334155}
.md p{margin:7px 0}
.md ul{margin:7px 0 7px 20px}
.md li{margin:3px 0}
.md code{background:#f1f5f9;padding:1px 5px;border-radius:3px;
  font-family:'SFMono-Regular',Consolas,monospace;font-size:12.5px;color:#0f172a}
.md pre{background:#0f172a;color:#e2e8f0;padding:14px 16px;border-radius:var(--r);
  overflow-x:auto;margin:10px 0;font-size:13px;line-height:1.5}
.md pre code{background:none;padding:0;color:inherit}
.md hr{border:none;border-top:1px solid var(--border);margin:14px 0}
.md a{color:#3b82f6;text-decoration:none}
.md a:hover{text-decoration:underline}
.md strong{font-weight:600}

/* ── Footer ── */
.df{margin-top:28px;padding-top:14px;border-top:1px solid var(--border);
  font-size:12px;color:var(--muted);display:flex;gap:20px;flex-wrap:wrap}
.df code{font-family:monospace}

@media(max-width:640px){
  aside#sidebar{width:190px}
  main#detail{padding:16px 18px}
  .hr{display:none}
}
"""

# ---------------------------------------------------------------------------
# Embedded JavaScript (no external dependencies)
# ---------------------------------------------------------------------------

_JS = """\
var S={type:null,q:'',idx:-1};
var TYPES=['module','class','api','function'];
var C={module:'#3b82f6',class:'#10b981',api:'#f59e0b','function':'#6b7280'};

function esc(s){
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

/* Inline markdown: bold, inline-code, links */
function inl(t){
  return t
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\\*\\*(.*?)\\*\\*/g,'<strong>$1</strong>')
    .replace(/`([^`]+)`/g,'<code>$1</code>')
    .replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g,'<a href="$2">$1</a>');
}

/* Block markdown renderer */
function renderMd(md){
  if(!md)return'';
  var lines=md.split('\\n'),out='',
      inCode=false,codeBuf=[],
      inList=false,listBuf=[];

  function flushList(){
    if(inList){
      out+='<ul>'+listBuf.map(function(i){return'<li>'+i+'</li>';}).join('')+'</ul>';
      inList=false;listBuf=[];
    }
  }

  lines.forEach(function(line){
    /* Fenced code block */
    if(line.startsWith('```')){
      if(inCode){
        out+='<pre><code>'+esc(codeBuf.join('\\n'))+'</code></pre>';
        inCode=false;codeBuf=[];
      }else{flushList();inCode=true;}
      return;
    }
    if(inCode){codeBuf.push(line);return;}

    if(/^### /.test(line))     {flushList();out+='<h3>'+inl(line.slice(4))+'</h3>';}
    else if(/^## /.test(line)) {flushList();out+='<h2>'+inl(line.slice(3))+'</h2>';}
    else if(/^# /.test(line))  {flushList();out+='<h1>'+inl(line.slice(2))+'</h1>';}
    else if(/^[*-] /.test(line)){inList=true;listBuf.push(inl(line.slice(2)));}
    else if(line.trim()==='---'){flushList();out+='<hr>';}
    else if(line.trim()==='')  {flushList();}
    else                       {flushList();out+='<p>'+inl(line)+'</p>';}
  });

  flushList();
  if(inCode)out+='<pre><code>'+esc(codeBuf.join('\\n'))+'</code></pre>';
  return out;
}

/* Type counts */
function counts(){
  var m={};
  DATA.forEach(function(c){m[c.type]=(m[c.type]||0)+1;});
  return m;
}

/* Filter */
function filtered(){
  return DATA.filter(function(c){
    if(S.type&&c.type!==S.type)return false;
    if(S.q){
      var q=S.q.toLowerCase();
      return c.title.toLowerCase().indexOf(q)>=0
        ||c.description.toLowerCase().indexOf(q)>=0
        ||(c.tags||[]).some(function(t){return t.toLowerCase().indexOf(q)>=0;});
    }
    return true;
  });
}

/* Render type-filter buttons */
function renderFilters(){
  var m=counts();
  document.getElementById('filters').innerHTML=
    TYPES.filter(function(t){return m[t];}).map(function(t){
      var on=S.type===t,col=C[t]||'#888';
      var bg=on?'background:'+col+';border-color:'+col+';':''
      return'<button class="fb'+(on?' on':'')+'" style="'+bg+'" onclick="setType(\''+t+'\')">'
        +'<span class="dot" style="background:'+(on?'rgba(255,255,255,.65)':col)+'"></span>'
        +esc(t)+' <span class="cnt">'+m[t]+'</span>'
        +'</button>';
    }).join('');
}

/* Render sidebar list */
function renderList(){
  var items=filtered(),el=document.getElementById('list');
  if(!items.length){el.innerHTML='<li class="nores">No concepts match</li>';return;}
  el.innerHTML=items.map(function(c){
    var idx=DATA.indexOf(c),col=C[c.type]||'#888',on=idx===S.idx?' on':'';
    return'<li class="ci'+on+'" onclick="show('+idx+')">'
      +'<span class="ci-dot" style="background:'+col+'"></span>'
      +'<div class="ci-body">'
      +'<div class="ci-title">'+esc(c.title)+'</div>'
      +'<div class="ci-desc">'+esc(c.description)+'</div>'
      +'</div></li>';
  }).join('');
}

/* Render concept detail */
function show(idx){
  S.idx=idx;
  var c=DATA[idx],col=C[c.type]||'#888';
  var tags=(c.tags||[]).map(function(t){return'<span class="tag">'+esc(t)+'</span>';}).join(' ');
  document.getElementById('detail').innerHTML=
    '<div class="dh">'
    +'<div class="dt">'+esc(c.title)+'</div>'
    +'<div class="dm"><span class="badge" style="background:'+col+'">'+esc(c.type)+'</span>'+tags+'</div>'
    +'<div class="dd">'+esc(c.description)+'</div>'
    +'<hr class="dhr">'
    +'</div>'
    +'<div class="md">'+renderMd(c.content)+'</div>'
    +'<div class="df">'
    +'<span>Source: <code>'+esc(c.resource)+'</code></span>'
    +'<span>'+esc(c.timestamp)+'</span>'
    +'</div>';
  renderList();
}

/* Toggle type filter */
function setType(t){
  S.type=(S.type===t)?null:t;
  renderFilters();renderList();
}

/* Init */
document.getElementById('search').addEventListener('input',function(e){
  S.q=e.target.value;renderList();
});
renderFilters();
renderList();
if(DATA.length)show(0);
"""
