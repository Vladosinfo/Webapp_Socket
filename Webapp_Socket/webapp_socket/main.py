from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import BaseServer
from datetime import datetime
from pathlib import Path
import urllib.parse
import mimetypes
import pathlib
import socket
import threading
import json

class HttpHandler(BaseHTTPRequestHandler):

    UDP_IP = '127.0.0.1'
    UDP_PORT = 5000        


    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.response_html('index.html')
        elif pr_url.path == '/contact':
            self.response_html('contact.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.response_static()
            else:    
                self.response_html('error.html', 404)


    def response_html(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())


    def response_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())
            

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        client = threading.Thread(target=self.send_to_socket_server, args=(data,))
        client.start()
        client.join()
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()


    def storage_data(data):
        data_decoded = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_decoded.split('&')]}

        # dir_path = Path("storage")
        # dir_path.mkdir(exist_ok=True)
        # filePath = Path("storage/data.json")
        # filePath.touch(exist_ok=True)

        file_content = ""
        with open("storage/data.json", "r") as rj:
            file_content = json.load(rj)

        date = datetime.now()
        message = {str(date) : data_dict}
        file_content.update(message)

        with open("storage/data.json", "w") as wj:
            json.dump(file_content, wj)


    def socket_server(self, ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server = ip, port
        sock.bind(server)
        send_back = "Got it!".encode()

        try:
            while True:
                data, address = sock.recvfrom(1024)
                self.storage_data(data)
                sock.sendto(send_back, address)

        except KeyboardInterrupt:
            print(f'Server destroyed')
        finally:
            sock.close()


    def send_to_socket_server(self, message):

        def socket_client(ip, port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server = ip, port
            sock.sendto(message, server)
            try:
                response, address = sock.recvfrom(1024)
            except Exception as e:
                print(f"Exception: {e}")
            finally:
                sock.close()
        
        socket_client(self.UDP_IP, self.UDP_PORT)


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)

    socked_server = threading.Thread(target=handler_class.socket_server, args=(handler_class, handler_class.UDP_IP, handler_class.UDP_PORT))
    try:
        socked_server.start()
        http.serve_forever()
        socked_server.join()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    run()
