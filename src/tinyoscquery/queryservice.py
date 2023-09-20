from zeroconf import ServiceInfo, Zeroconf
from http.server import SimpleHTTPRequestHandler, HTTPServer
from .shared.node import OSCQueryNode, OSCHostInfo, OSCAccess
import json, threading


class OSCQueryService(object):
    """
    A class providing an OSCQuery service. Automatically sets up a oscjson http server and advertises the oscjson server and osc server on zeroconf.

    Attributes
    ----------
    serverName : str
        Name of your OSC Service
    httpPort : int
        Desired TCP port number for the oscjson HTTP server
    oscPort : int
        Desired UDP port number for the osc server
    """
    
    def __init__(self, serverName, httpPort, oscPort, oscIp="127.0.0.1") -> None:
        self.serverName = serverName
        self.httpPort = httpPort
        self.oscPort = oscPort
        self.oscIp = oscIp

        self.root_node = OSCQueryNode("/", description="root node")
        self.host_info = OSCHostInfo(serverName, {"ACCESS":True,"CLIPMODE":False,"RANGE":True,"TYPE":True,"VALUE":True}, 
            self.oscIp, self.oscPort, "UDP")

        self._zeroconf = Zeroconf()
        self._startOSCQueryService()
        self._advertiseOSCService()
        self.http_server = OSCQueryHTTPServer(self.root_node, self.host_info, ('', self.httpPort), OSCQueryHTTPHandler)
        self.http_thread = threading.Thread(target=self._startHTTPServer)
        self.http_thread.start()

    def stop(self):
        self.http_server.shutdown()

    def add_node(self, node):
        self.root_node.add_child_node(node)

    def advertise_endpoint(self, address, value=None, access=OSCAccess.READWRITE_VALUE):
        new_node = OSCQueryNode(full_path=address, access=access)
        if value is not None:
            if not isinstance(value, list):
                new_node.value = [value]
                new_node.type_ = [type(value)]
            else:
                new_node.value = value
                new_node.type_ = [type(v) for v in value]
        self.add_node(new_node)

    def _startOSCQueryService(self):
        oscqsDesc = {'txtvers': 1}
        oscqsInfo = ServiceInfo("_oscjson._tcp.local.", "%s._oscjson._tcp.local." % self.serverName, self.httpPort, 
        0, 0, oscqsDesc, "%s.oscjson.local." % self.serverName, addresses=["127.0.0.1"])
        self._zeroconf.register_service(oscqsInfo)


    def _startHTTPServer(self):
        self.http_server.serve_forever()

    def _advertiseOSCService(self):
        oscDesc = {'txtvers': 1}
        oscInfo = ServiceInfo("_osc._udp.local.", "%s._osc._udp.local." % self.serverName, self.oscPort, 
        0, 0, oscDesc, "%s.osc.local." % self.serverName, addresses=["127.0.0.1"])

        self._zeroconf.register_service(oscInfo)


class OSCQueryHTTPServer(HTTPServer):
    def __init__(self, root_node, host_info, server_address: tuple[str, int], RequestHandlerClass, bind_and_activate: bool = ...) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.root_node = root_node
        self.host_info = host_info


class OSCQueryHTTPHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if 'HOST_INFO' in self.path:
            self.send_response(200)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            self.wfile.write(bytes(str(self.server.host_info.to_json()), 'utf-8'))
            return
        node = self.server.root_node.find_subnode(self.path)
        if node is None:
            self.send_response(404)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            self.wfile.write(bytes("OSC Path not found", 'utf-8'))
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            self.wfile.write(bytes(str(node.to_json()), 'utf-8'))

    def log_message(self, format, *args):
        pass
            
