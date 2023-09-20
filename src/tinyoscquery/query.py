import time
from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf
import requests

from .shared.node import OSCQueryNode, OSC_Type_String_to_Python_Type, OSCAccess, OSCHostInfo

class OSCQueryListener(ServiceListener):

    def __init__(self) -> None:
        self.osc_services = {}
        self.oscjson_services = {}

        super().__init__()

    def remove_service(self, zc: 'Zeroconf', type_: str, name: str) -> None:
        if name in self.osc_services:
            del self.osc_services[name]

        if name in self.oscjson_services:
            del self.oscjson_services[name]

    def add_service(self, zc: 'Zeroconf', type_: str, name: str) -> None:
        if type_ == '_osc._udp.local.':
            self.osc_services[name] = zc.get_service_info(type_, name)
        elif type_ == '_oscjson._tcp.local.':
            self.oscjson_services[name] = zc.get_service_info(type_, name)

    def update_service(self, zc: 'Zeroconf', type_: str, name: str) -> None:
        if type_ == '_osc._udp.local.':
            self.osc_services[name] = zc.get_service_info(type_, name)
        elif type_ == '_oscjson._tcp.local.':
            self.oscjson_services[name] = zc.get_service_info(type_, name)


class OSCQueryBrowser(object):
    def __init__(self) -> None:
        self.listener = OSCQueryListener()
        self.zc = Zeroconf()
        self.browser = ServiceBrowser(self.zc, ["_oscjson._tcp.local.", "_osc._udp.local."], self.listener)

    def get_discovered_osc(self):
        return [oscsvc[1] for oscsvc in self.listener.osc_services.items()]

    def get_discovered_oscquery(self):
        return [oscjssvc[1] for oscjssvc in self.listener.oscjson_services.items()]

    def find_service_by_name(self, name):
        for svc in self.get_discovered_oscquery():
            client = OSCQueryClient(svc)
            if name in client.get_host_info().name:
                return svc

        return None

    def find_nodes_by_endpoint_address(self, address) -> list[tuple[ServiceInfo, OSCHostInfo, OSCQueryNode]]:
        svcs = []
        for svc in self.get_discovered_oscquery():
            client = OSCQueryClient(svc)
            hi = client.get_host_info()
            if hi is None:
                continue
            node = client.query_node(address)
            if node is not None:
                svcs.append((svc, hi, node))

        return svcs


class OSCQueryClient(object):
    def __init__(self, service_info) -> None:
        if not isinstance(service_info, ServiceInfo):
            raise Exception("service_info isn't a ServiceInfo class!")

        if service_info.type != "_oscjson._tcp.local.":
            raise Exception("service_info does not represent an OSCQuery service!")

        self.service_info = service_info
        self.last_json = None

    def _get_query_root(self):
        return f"http://{self._get_ip_str()}:{self.service_info.port}"

    def _get_ip_str(self):
        ip_str = '.'.join([str(int(num)) for num in self.service_info.addresses[0]])
        return ip_str

    def query_node(self, node="/"):
        url = self._get_query_root() + node
        r = None
        try:
            r = requests.get(url)
        except Exception as ex:
            print("Error querying node...", ex)
        if r is None:
            return None

        if r.status_code == 404:
            return None
        
        if r.status_code != 200:
            raise Exception("Node query error: (HTTP", r.status_code, ") ", r.content)

        self.last_json = r.json()

        return self._make_node_from_json(self.last_json)


    def get_host_info(self):
        url = self._get_query_root() + "/HOST_INFO"
        r = None
        try:
            r = requests.get(url)
        except Exception as ex:
            #print("Error querying HOST_INFO...", ex)
            pass
        if r is None:
            return None

        if r.status_code != 200:
            raise Exception("Node query error: (HTTP", r.status_code, ") ", r.content)

        json = r.json()
        hi = OSCHostInfo(json["NAME"], json['EXTENSIONS'])
        if 'OSC_IP' in json:
            hi.osc_ip = json["OSC_IP"]
        else:
            hi.osc_ip = self._get_ip_str()

        if 'OSC_PORT' in json:
            hi.osc_port = json['OSC_PORT']
        else:
            hi.osc_port = self.service_info.port

        if 'OSC_TRANSPORT' in json:
            hi.osc_transport = json['OSC_TRANSPORT']
        else:
            hi.osc_transport = "UDP"

        return hi

    def _make_node_from_json(self, json):
        newNode = OSCQueryNode()

        if "CONTENTS" in json:
            subNodes = []
            for subNode in json["CONTENTS"]:
                subNodes.append(self._make_node_from_json(json["CONTENTS"][subNode]))
            newNode.contents = subNodes

        # This *should* be required but some implementations don't have it...
        if "FULL_PATH" in json:
            newNode.full_path = json["FULL_PATH"]

        if "TYPE" in json:
            newNode.type_ = OSC_Type_String_to_Python_Type(json["TYPE"])

        if "DESCRIPTION" in json:
            newNode.description = json["DESCRIPTION"]

        if "ACCESS" in json:
            newNode.access = OSCAccess(json["ACCESS"])

        if "VALUE" in json:
            newNode.value = []
            # This should always be an array... throw an exception here?
            if not isinstance(json['VALUE'], list):
                raise Exception("OSCQuery JSON Value is not List / Array? Out-of-spec?")
            
            for idx, v in enumerate(json["VALUE"]):
                # According to the spec, if there is not yet a value, the return will be an empty JSON object
                if isinstance(v, dict) and not v:
                    # FIXME does this apply to all values in the value array always...? I assume it does here
                    newNode.value = []
                    break
                else:
                    newNode.value.append(newNode.type_[idx](v))


        return newNode




if __name__ == "__main__":
    browser = OSCQueryBrowser()
    time.sleep(2) # Wait for discovery

    for service_info in browser.get_discovered_oscquery():
        client = OSCQueryClient(service_info)

        # Find host info
        host_info = client.get_host_info()
        print(f"Found OSC Host: {host_info.name} with ip {host_info.osc_ip}:{host_info.osc_port}")

        # Query a node and print its value
        node = client.query_node("/test/node")
        print(f"Node is a {node.type_} with value {node.value}")

        
        