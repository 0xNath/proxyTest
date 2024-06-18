import http.server
import requests

requests.packages.urllib3.util.connection.HAS_IPV6 = False

DEBUG = False


class proxyfi(http.server.BaseHTTPRequestHandler):
    remoteHost = str
    remoteProtocol = "https"
    remotePort = 443
    proxy = dict

    def replaceSelfToRemote(self, input: dict) -> dict:
        buffer = []
        finalBuffer = {}

        for item, value in input.items():
            if item == "Host":
                buffer.append((item, f"{self.remoteHost}"))
            elif item == "Upgrade-Insecure-Requests":
                ...
            else:
                buffer.append((item, value))

        finalBuffer.update(buffer)

        return finalBuffer

    def replaceRemoteToSelf(self, input: dict) -> dict:
        buffer = []
        finalBuffer = {}

        for item, value in input.items():
            if item == "Upgrade-Insecure-Requests":
                ...
            elif item == "Transfer-Encoding":
                ...
            else:
                buffer.append((item, value))

        finalBuffer.update(buffer)

        return dict(finalBuffer)

    def response(self):
        clientHeader = self.replaceSelfToRemote(self.headers)

        if DEBUG:
            print(
                "client request :",
                self.remoteProtocol + "://" + self.remoteHost + self.path,
            )
            print("client header :", clientHeader)
            print()

        s = requests.Session()

        request = requests.Request(
            method=self.command,
            url=self.remoteProtocol + "://" + self.remoteHost + self.path,
            headers=clientHeader,
        )

        if self.command == "POST":
            request.data = self.rfile.read(int(self.headers.get("Content-Length")))

        preppedRequest = s.prepare_request(request)

        if DEBUG:
            print("Requesting server...")
            print()

        response = s.send(preppedRequest, proxies=self.proxy)

        if DEBUG:
            print("server status code :", response.status_code)
            print("server header :", response.headers)
            print()
            # print("server content :", response.content)

        self.send_response(response.status_code)

        if self.command == "POST":
            for cookie in s.cookies:
                self.send_header(
                    "Set-Cookie",
                    f"{cookie.name}={cookie.value}; Path={cookie.path}",
                )

        if "Content-Length" not in response.headers.keys():
            self.send_header("Content-Length", len(response.content))
        for item, value in self.replaceRemoteToSelf(response.headers).items():
            self.send_header(item, value)

        self.end_headers()

        if self.command != "HEAD":
            self.wfile.write(response.content)

    def do_GET(self):
        self.response()

    def do_POST(self):
        self.response()

    def do_HEAD(self):
        self.response()

    def log_request(self, code="-", size="-"): ...


if __name__ == "__main__":
    handler = proxyfi

    handler.sys_version = ""
    handler.server_version = ""

    handler.remoteProtocol = "https"
    handler.remoteHost = ""
    handler.remotePort = "443"
    handler.proxy = {}

    try:
        server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 8080), RequestHandlerClass=handler
        )

        print(
            f"Serving {handler.remoteProtocol}://{handler.remoteHost} at http://{server.server_address[0]}:{server.server_address[1]}..."
        )

        server.serve_forever()
    except KeyboardInterrupt:
        print("Keyboard interrupt signal received, shutting down the web server")
        server.socket.close()
