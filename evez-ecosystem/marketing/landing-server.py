#!/usr/bin/env python3
"""Serve EVEZ landing page with SEO-optimized headers"""
import http.server
import os

PORT = 9996
LANDING = "/home/openclaw/evez-ecosystem/marketing/landing-page.html"

class LandingHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "public, max-age=3600")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
            self.end_headers()
            with open(LANDING, "rb") as f:
                self.wfile.write(f.read())
        elif self.path == "/og-image.png":
            img = "/home/openclaw/evez-ecosystem/marketing/images/og-main.png"
            if os.path.exists(img):
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                with open(img, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
        elif self.path == "/openapi.json":
            spec = "/home/openclaw/evez-ecosystem/evez-provider/openapi.json"
            if os.path.exists(spec):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(spec, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[Landing] {args[0]}")

if __name__ == "__main__":
    print(f"🌐 EVEZ Landing Page → http://localhost:{PORT}")
    server = http.server.HTTPServer(("0.0.0.0", PORT), LandingHandler)
    server.serve_forever()
