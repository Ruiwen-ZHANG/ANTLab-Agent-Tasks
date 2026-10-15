"""B 题对照页面服务：同一请求同时交给【原样机】与【修复版】，并排显示两者结果。
两个 Engine 各自保留实例状态（缓存），可勾选"运行前清空状态"。离线重放，不调用模型，只监听本机。
用法（在仓库根目录）：python 进阶/challenge_b/server_compare.py  然后打开 http://127.0.0.1:8767"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from challenge import Engine as OriginalEngine
from fixed_engine import FixedEngine

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / 'data.json').read_text(encoding='utf-8'))
ENGINES = {'original': OriginalEngine(), 'fixed': FixedEngine()}   # 两套独立实例，状态互不影响

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, value, mime='application/json; charset=utf-8'):
        raw = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(raw))); self.send_header('Cache-Control', 'no-store')
        self.end_headers(); self.wfile.write(raw)

    def do_GET(self):
        if self.path == '/':
            self.reply(200, (ROOT / 'compare.html').read_bytes(), 'text/html; charset=utf-8')
        elif self.path == '/api/cases':
            self.reply(200, DATA)
        else:
            self.reply(404, {'error': 'not_found'})

    def do_POST(self):
        if self.path != '/api/compare':
            return self.reply(404, {'error': 'not_found'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 32768: raise ValueError('invalid_size')
            body = json.loads(self.rfile.read(length))
            case = next(c for c in DATA['cases'] if c['id'] == body['case_id'])
            out = {}
            for name, eng in ENGINES.items():
                if body.get('reset'): eng.cache.clear()           # 勾选后两个 Engine 同时清空
                out[name] = eng.evaluate(case['request'], DATA['corpus'], case['draft'])
            self.reply(200, out)
        except (ValueError, KeyError, StopIteration, TypeError) as e:
            self.reply(400, {'error': str(e) or 'invalid_case'})

if __name__ == '__main__':
    print('B 对照页（离线重放）: http://127.0.0.1:8767', flush=True)
    HTTPServer(('127.0.0.1', 8767), Handler).serve_forever()