"""Local single-browser UI runs the same canonical engine without cloud uploads."""
from http.server import ThreadingHTTPServer
from http.client import HTTPConnection
import json
from pathlib import Path
import sys
from threading import Thread

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from serve_farm_workspace import Handler, PAGE, MAX_CSV  # noqa: E402


def request(conn,method,path,body=None,headers=None):
    conn.request(method,path,body=body,headers=headers or {})
    r=conn.getresponse()
    return r.status,r.read().decode("utf-8")


def test_local_web_app_and_private_memory_only_csv():
    with ThreadingHTTPServer(("127.0.0.1",0),Handler) as server:
        server.sample=(ROOT/"data/templates/farm_workspace_SYNTHETIC.json").read_text(encoding="utf-8")
        t=Thread(target=server.serve_forever,daemon=True)
        t.start()
        try:
            conn=HTTPConnection("127.0.0.1",server.server_port,timeout=25)
            status,html=request(conn,"GET","/")
            assert status==200
            assert "하나의 농장" in html
            assert "농장 계획 JSON" in html
            status,raw=request(conn,"GET","/api/sample")
            assert status==200
            work=json.loads(raw)
            assert work["schema_version"]==1
            csv=(ROOT/"data/templates/field_log_SYNTHETIC.csv").read_text(encoding="utf-8")
            body=json.dumps({"workspace":work,"csv_text":csv},ensure_ascii=False)
            status,out=request(conn,"POST","/api/run",body.encode("utf-8"),
                {"Content-Type":"application/json","X-Farm-Workspace":"1"})
            assert status==200,out[:400]
            result=json.loads(out)
            assert result["report"]["field_log"]["rows"]==9
            assert result["report"]["authoritative_portfolio"]["financing"]["drawn_krw"]==1000000
            assert "하나의 농장 통합 현금원장" in result["html"]
            assert "DEMO_BANK_01" not in out
            assert "DEMO_WORK_01" not in out
            status,forbidden=request(conn,"POST","/api/run",body.encode("utf-8"),
                {"Content-Type":"application/json","X-Farm-Workspace":"1",
                 "Origin":"https://evil.example"})
            assert status==403
            status,wrong=request(conn,"POST","/api/run",body.encode("utf-8"),
                {"Content-Type":"application/json","X-Farm-Workspace":"1",
                 "Host":"localhost:"+str(server.server_port)})
            assert status==403
            status,too_big=request(conn,"POST","/api/run","x"*100,
                {"Content-Type":"application/json","X-Farm-Workspace":"1",
                 "Content-Length":str(MAX_CSV*4)})
            assert status==413
            conn.close()
        finally:
            server.shutdown()
            t.join(timeout=15)


def test_local_browser_does_not_mention_remote_destination():
    assert "127.0.0.1" in PAGE
    assert 'method:"POST"' in PAGE
    assert 'X-Farm-Workspace' in PAGE
    assert "farm-kpi-unified-result.json" in PAGE
