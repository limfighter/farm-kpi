"""Local-only ONE Farm KPI browser: edit one JSON, analyze, view one report.

No external web server, authentication service, cloud database, or disk uploads.
Bind ONLY loopback; reject foreign Origin/Host and oversized requests. This is
a personal planning UI, not suitable for public LAN/Internet deployment.
"""
import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from farm_strategy.farm_workspace import run_farm_workspace  # noqa: E402
from run_farm_workspace import render_html  # noqa: E402

MAX_BODY = 3_000_000
MAX_CSV = 1_000_000
DEFAULT_SAMPLE = ROOT / "data/templates/farm_workspace_SYNTHETIC.json"


PAGE = r"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Farm KPI | 하나의 농장</title>
<style>
:root{font:15px/1.6 system-ui,-apple-system,sans-serif;color:#264333;background:#f6f8f3}
*{box-sizing:border-box}body{margin:0}header{background:#214733;color:white;padding:22px 30px}
h1{margin:0;font-size:27px}header p{margin:5px 0 0;color:#dce7df}
main{max-width:1330px;margin:20px auto;display:grid;grid-template-columns:minmax(330px,4fr) minmax(0,7fr);gap:15px;padding:0 15px}
section{border-radius:13px;border:1px solid #dce5dc;background:white;padding:17px;min-width:0}
label{display:block;margin:14px 0 6px;font-weight:600}textarea{width:100%;height:360px;padding:13px;
font:12px/1.55 ui-monospace,monospace;border:1px solid #bfcfc1;border-radius:9px;resize:vertical}
button,input::file-selector-button{padding:10px 15px;border-radius:9px;background:#2d5d42;color:white;
border:0;cursor:pointer;font:inherit}button:hover{background:#17412c}
button:disabled{opacity:.55;cursor:not-allowed}
input[type=file]{max-width:100%;font-size:12px}
fieldset{border:1px solid #dfe8dc;border-radius:9px;margin:15px 0}
legend{font-weight:bold}
.note{background:#fff2df;border-left:4px solid #ae8343;padding:12px;margin:13px 0;font-size:13px}
#state{margin:13px 0;white-space:pre-wrap;font-size:13px}#state.error{color:#ac332b}
iframe{width:100%;min-height:78vh;height:850px;border:1px solid #cbdccb;border-radius:12px}
@media(max-width:890px){main{display:block}main section{margin-bottom:15px}iframe{height:690px}}
</style></head><body>
<header><h1>Farm KPI · 통합 농장 계획</h1><p>작물·시설·노동·자원·등급별 정산·대출·위험을 하나의 화면에서 확인</p></header>
<main><section aria-label="농장 입력">
<h2>1. 농장 계획 입력</h2>
<p class="note">현재 표시한 값은 가상의 예제이며 실제 필지 수익/시설·대출 승인 자료가 아닙니다.
이 화면은 내 컴퓨터(127.0.0.1)에서만 처리합니다. 원본 영수증·계좌·농지 주소는 붙여 넣지 마세요.</p>
<label for="workfile">농장 JSON 불러오기</label>
<input type="file" id="workfile" accept=".json,application/json">
<label for="work">공통 농장 계획(JSON)</label>
<textarea id="work" spellcheck="false" aria-label="농장 계획 JSON"></textarea>
<fieldset><legend>선택: 비식별 영농기록</legend>
<label for="log">CSV 파일 — 원본 거래서류 업로드 금지</label>
<input type="file" id="log" accept=".csv,text/csv">
<p>선택하지 않으면 실제 기록은 UNKNOWN으로 표시됩니다. 선택한 파일은 디스크에 복사하거나 서버에 보관하지 않습니다.</p>
</fieldset>
<button id="calculate">전체 농장 다시 계산</button>
<button id="export" disabled>결과 JSON 저장</button>
<div id="state" role="status">예제를 불러오는 중</div>
</section>
<section aria-label="농장 결과">
<h2>2. 하나의 농장 결과</h2>
<iframe id="report" title="농장 합산 현금·시설·운영·위험 결과" sandbox=""></iframe>
</section></main>
<script>
"use strict";
const work=document.getElementById("work"),state=document.getElementById("state");
const report=document.getElementById("report"),btn=document.getElementById("calculate");
const exportBtn=document.getElementById("export");let latest=null;
function say(v,bad=false){state.textContent=v;state.className=bad?"error":"";}
function download(name,contents,media){
  const b=new Blob([contents],{type:media});
  const url=URL.createObjectURL(b),a=document.createElement("a");
  a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
document.getElementById("workfile").addEventListener("change",async e=>{
  const file=e.target.files[0];if(!file)return;
  if(file.size>1500000){say("입력 JSON 파일이 너무 큽니다.",true);return;}
  work.value=await file.text();say("JSON을 읽었습니다. 전체 농장을 다시 계산하세요.");
});
exportBtn.addEventListener("click",()=>{
  if(latest!==null)download("farm-kpi-unified-result.json",
    JSON.stringify(latest,null,2),"application/json;charset=utf-8");
});
btn.addEventListener("click",async()=>{
  let workspace;
  try{workspace=JSON.parse(work.value);}catch(e){say("JSON 문법 오류: "+e.message,true);return;}
  const file=document.getElementById("log").files[0];
  if(file&&file.size>1000000){say("CSV가 1MB를 넘습니다.",true);return;}
  btn.disabled=true;say("로컬 Python 계산기에 입력을 검증하고 있습니다.");
  try{
    const csv_text=file?await file.text():null;
    const resp=await fetch("/api/run",{method:"POST",headers:{"Content-Type":"application/json","X-Farm-Workspace":"1"},
      body:JSON.stringify({workspace,csv_text})});
    const body=await resp.json();
    if(!resp.ok)throw new Error(body.error||"계산 실패");
    latest=body.report;
    report.srcdoc=body.html;
    exportBtn.disabled=false;
    say("계산 완료: 하나의 현금원장 기준. 현장 자료가 검증됐다는 뜻은 아닙니다.");
  }catch(e){latest=null;exportBtn.disabled=true;say("실행 중단: "+e.message,true);}
  finally{btn.disabled=false;}
});
fetch("/api/sample").then(r=>r.json()).then(j=>{work.value=JSON.stringify(j,null,2);say("합성 예제 준비. 계산 버튼을 누르세요.");})
.catch(e=>say("예제를 불러올 수 없습니다: "+e.message,true));
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        # Never log request URLs or potentially sensitive bodies.
        pass

    def _send(self, status, body, content_type="application/json; charset=utf-8"):
        raw=body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(raw)

    def _authorized(self):
        host=self.headers.get("Host","")
        port=self.server.server_address[1]
        if host != f"127.0.0.1:{port}":
            self._send(403,json.dumps({"error":"Local host only"}))
            return False
        origin=self.headers.get("Origin")
        if origin and origin != f"http://127.0.0.1:{port}":
            self._send(403,json.dumps({"error":"Other origins forbidden"}))
            return False
        return True

    def do_GET(self):
        if not self._authorized():
            return
        if self.path == "/":
            self._send(200,PAGE,"text/html; charset=utf-8")
        elif self.path == "/api/sample":
            self._send(200,self.server.sample)
        else:
            self._send(404,json.dumps({"error":"Unknown route"}))

    def do_POST(self):
        if not self._authorized():
            return
        if self.path != "/api/run" or self.headers.get("X-Farm-Workspace")!="1":
            self._send(404,json.dumps({"error":"Invalid endpoint/header"}))
            return
        try:
            length=int(self.headers.get("Content-Length","-1"))
        except ValueError:
            self._send(400,json.dumps({"error":"Invalid request size"}))
            return
        if not 0 < length <= MAX_BODY:
            self._send(413,json.dumps({"error":"Request too large"}))
            return
        if self.headers.get("Content-Type","").split(";")[0]!="application/json":
            self._send(415,json.dumps({"error":"JSON only"}))
            return
        try:
            item=json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(item,dict) or set(item)!={"workspace","csv_text"}:
                raise ValueError("Expected workspace and optional csv_text")
            csv_text=item["csv_text"]
            if csv_text is not None and (not isinstance(csv_text,str) or len(csv_text.encode("utf-8"))>MAX_CSV):
                raise ValueError("CSV requires small UTF-8 text")
            report=run_farm_workspace(item["workspace"],
                field_log=StringIO(csv_text) if csv_text is not None else None)
            body=json.dumps({"report":report,"html":render_html(report)},ensure_ascii=False,allow_nan=False)
            self._send(200,body)
        except (ValueError,TypeError,UnicodeError,KeyError,OverflowError) as exc:
            # Rejected input may include secret text in exception: do not
            # echo the exception contents to the browser or server logs.
            self._send(422,json.dumps({"error":"입력 검증 실패. 필드명, 값/단위, 작물ID 및 원장 일치 여부를 확인하세요."},
                                      ensure_ascii=False))

def serve(port=8765, sample=DEFAULT_SAMPLE):
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError("Port must be 1024..65535")
    config=json.loads(Path(sample).read_text(encoding="utf-8"))
    run_farm_workspace(config)  # validate default before server starts
    host="127.0.0.1"
    with ThreadingHTTPServer((host,port), Handler) as server:
        server.sample=json.dumps(config,ensure_ascii=False)
        print(f"Farm KPI local-only app: http://{host}:{port}/",flush=True)
        print("Only open on your own computer; Ctrl+C to stop.",flush=True)
        server.serve_forever()


def main():
    parser=argparse.ArgumentParser(description="Farm KPI single local browser")
    parser.add_argument("--port",type=int,default=8765)
    parser.add_argument("--input",type=Path,default=DEFAULT_SAMPLE,
                        help="Optional local non-sensitive initial JSON sample")
    a=parser.parse_args()
    serve(port=a.port,sample=a.input)


if __name__=="__main__":
    main()
