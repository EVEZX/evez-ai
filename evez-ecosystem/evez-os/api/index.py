from http.server import BaseHTTPRequestHandler

HTML = """<!doctype html>
<html lang='en'>
<head>
  <meta charset='UTF-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1.0' />
  <title>EVEZ OS Runtime</title>
  <link rel='stylesheet' href='/styles.css' />
</head>
<body>
  <div id='app'></div>
  <script src='/app.js'></script>
</body>
</html>"""

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML.encode('utf-8'))
