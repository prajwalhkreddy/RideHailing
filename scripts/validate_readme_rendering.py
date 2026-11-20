"""Bounded Markdown/parser validation; explicitly distinguishes unavailable engines."""
from pathlib import Path
import re,json,html,hashlib,xml.etree.ElementTree as ET
from urllib.parse import unquote,urlsplit
from markdown_it import MarkdownIt
from matplotlib.mathtext import MathTextParser
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'results_v2/publication'
def slug(s):
 s=re.sub(r'<[^>]*>','',s).lower();return re.sub(r'[^\w\- ]','',s).replace(' ','-')
def anchors(text):
 seen={};out=set()
 for line in text.splitlines():
  if re.match(r'^#{1,6} ',line):
   name=slug(re.sub(r'^#+\s+','',line));n=seen.get(name,0);seen[name]=n+1;out.add(name+(f'-{n}' if n else ''))
 return out

def audit():
 text=(R/'README.md').read_text();md=MarkdownIt('commonmark').enable('table');tokens=md.parse(text)
 links=[];errors=[];images=[]
 for t in tokens:
  for c in t.children or []:
   if c.type in ('link_open','image'):
    url=c.attrGet('href') if c.type=='link_open' else c.attrGet('src');u=urlsplit(url)
    if u.scheme or u.netloc:continue
    path=R/unquote(u.path) if u.path else R/'README.md';entry=dict(url=url,exists=path.exists(),kind='directory' if path.is_dir() else 'file')
    if not path.exists():errors.append('Missing '+url)
    elif u.fragment:
     if path.suffix!='.md' or unquote(u.fragment) not in anchors(path.read_text()):errors.append('Missing anchor '+url)
    if path.exists():
     relative=path.relative_to(R);cursor=R
     for part in relative.parts:
      if part not in {x.name for x in cursor.iterdir()}:errors.append('Case mismatch '+url);break
      cursor/=part
     if path.suffix.lower() in ('.parquet','.keras','.docx','.npz'):errors.append('Binary reader link '+url)
     if path.suffix.lower()=='.svg':
      ET.parse(path);images.append(dict(path=str(relative),format='SVG',readable=True))
     elif path.suffix.lower()=='.png':
      with Image.open(path) as im:im.verify()
      with Image.open(path) as im:images.append(dict(path=str(relative),format='PNG',dimensions=list(im.size),readable=True))
    links.append(entry)
 displays=re.findall(r'(?m)^\$\$\n(.*?)\n\$\$$',text,re.S)
 if text.count('$$')!=len(displays)*2:errors.append('Malformed display delimiters')
 stripped=re.sub(r'```.*?```','',text,flags=re.S);stripped=re.sub(r'\$\$.*?\$\$','',stripped,flags=re.S)
 inline=re.findall(r'(?<!\\)\$([^\n$]+)(?<!\\)\$',stripped)
 if len(re.findall(r'(?<!\\)\$',stripped))!=2*len(inline):errors.append('Unbalanced inline math')
 if r'\operatorname' in text:errors.append('Disallowed operatorname macro')
 math_results=[];parser=MathTextParser('path')
 for kind,items in [('display',displays),('inline',inline)]:
  for expr in items:
   try:
    parsed=parser.parse('$'+expr.replace('\n',' ')+'$',dpi=100);math_results.append(dict(kind=kind,expression=expr,width=float(parsed.width),height=float(parsed.height),parsed=True))
   except Exception as e:math_results.append(dict(kind=kind,expression=expr,parsed=False,error=str(e)))
 # Minimal grammar check for the deliberately restricted diagram subset, NOT a Mermaid parser claim.
 diagrams=re.findall(r'```mermaid\n(.*?)```',text,re.S);diagram_errors=[]
 for i,d in enumerate(diagrams,1):
  for line in d.splitlines()[1:]:
   line=line.strip()
   if not line:continue
   if d.startswith('sequenceDiagram'):
    if not (re.fullmatch(r'participant \w+ as .+',line) or re.fullmatch(r'\w+->>\w+: [^;\n]+',line)):diagram_errors.append([i,line])
   elif not re.fullmatch(r'.+(?:-->|-\. .+ \.->).+',line):diagram_errors.append([i,line])
 # Render complete Markdown to HTML with math preserved verbatim, not falsely called MathJax output.
 preview=md.render(text)
 preview='<!doctype html><meta charset="utf-8"><base href="../../"><title>README structural preview</title><style>body{max-width:1040px;margin:2em auto;font:16px sans-serif;line-height:1.6}img{max-width:100%}table{border-collapse:collapse}td,th{border:1px solid #ddd;padding:6px}pre{overflow:auto;white-space:pre-wrap}</style><p>Structural preview only: math and Mermaid engines unavailable. Use GitHub for final rendering.</p>'+preview
 (O/'readme_structural_preview.html').write_text(preview)
 report=dict(status='PASS' if not errors and not diagram_errors else 'FAIL',local_links=len(links),unique_links=len({x['url'] for x in links}),link_errors=errors,links=links,images=images,display_formulas=len(displays),inline_formulas=len(inline),mathtext_diagnostics=math_results,mermaid_blocks=len(diagrams),restricted_grammar_errors=diagram_errors,markdown_parser='markdown-it-py CommonMark plus tables',rendered_tables=sum(t.type=='table_open' for t in tokens),math_engine='Matplotlib MathText supplemental parser; NOT KaTeX/MathJax',mermaid_engine='Unavailable: no Node/Mermaid CLI installed',visual_rendering='UNVERIFIED: full GitHub browser rendering unavailable',commands='Documentation scripts and referenced entry points exist; no training commands executed')
 (O/'readme_render_validation.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
 r=audit();print(json.dumps({k:v for k,v in r.items() if k not in ('links','images','mathtext_diagnostics')},indent=2));print('MathText failures:',[(m['kind'],m['expression']) for m in r['mathtext_diagnostics'] if not m['parsed']])
