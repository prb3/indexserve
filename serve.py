import os,sys,socket,base64,http.server,socketserver,urllib.parse,re
p=int(sys.argv[1]) if len(sys.argv)>1 else 8000
a=sys.argv[2] if len(sys.argv)>2 else None
class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if a and not self.auth():return
        if self.path=='/':
            self.list_directory(os.getcwd())
        else:
            super().do_GET()
    def do_POST(self):
        if a and not self.auth():return
        ctype=self.headers.get('Content-Type','')
        if not ctype.startswith('multipart/form-data'):self.send_error(400);return
        boundary=b'--'+ctype.split('boundary=')[-1].encode()
        length=int(self.headers.get('Content-Length',0))
        body=self.rfile.read(length)
        for part in body.split(boundary):
            if not part.strip() or part==b'--\r\n':continue
            h_end=part.find(b'\r\n\r\n')
            if h_end==-1:continue
            headers=part[:h_end].decode(errors='ignore')
            data=part[h_end+4:-2]
            fname=None
            for line in headers.split('\r\n'):
                if line.startswith('Content-Disposition:'):
                    m=re.search(r'filename="([^"]*)"',line)
                    if m:fname=m.group(1)
                    break
            if fname:
                with open(os.path.basename(fname),'wb') as f:f.write(data)
                self.send_response(303)
                self.send_header('Location', '/')
                self.end_headers()
                return
        self.send_error(400)
    def auth(self):
        h=self.headers.get('Authorization','')
        if not h:return self.send_auth()
        try:
            t,c=h.split(None,1)
            if t.lower()!='basic' or base64.b64decode(c).decode()!=a:
                return self.send_auth()
        except:return self.send_auth()
        return True
    def send_auth(self):
        self.send_response(401);self.send_header('WWW-Authenticate','Basic realm="File"');self.end_headers();self.wfile.write(b'Auth')
        return False
    def list_directory(self,path):
        from io import BytesIO
        try:entries=os.listdir(path)
        except OSError:self.send_error(404);return
        entries.sort(key=lambda x:(not os.path.isdir(os.path.join(path,x)),x.lower()))
        self.send_response(200)
        self.send_header('Content-Type','text/html;charset=utf-8')
        self.end_headers()
        self.wfile.write(b'<!DOCTYPE HTML><html><head><meta charset="utf-8"><title>Directory listing</title></head><body>')
        self.wfile.write(f'<h1>Directory listing for {self.path}</h1><hr><ul>'.encode())
        for name in entries:
            full=os.path.join(path,name)
            display=name+'/' if os.path.isdir(full) else name
            link=urllib.parse.quote(name)+('/' if os.path.isdir(full) else '')
            self.wfile.write(f'<li><a href="{link}">{display}</a></li>'.encode())
        self.wfile.write(b'</ul><hr><form method="post" enctype="multipart/form-data"><input type="file" name="file"><input type="submit" value="Upload"></form></body></html>')
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('8.8.8.8',80));ip=s.getsockname()[0];s.close()
print(f'http://{ip}:{p}  {os.getcwd()}')
socketserver.TCPServer(("",p),H).serve_forever()

