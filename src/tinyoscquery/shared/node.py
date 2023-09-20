from enum import IntEnum
import json
from json import JSONEncoder

class OSCNodeEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, OSCQueryNode):
            obj_dict = {}
            for k, v in vars(o).items():
                if v is None:
                    continue
                if k.lower() == "type_":
                    obj_dict["TYPE"] = Python_Type_List_to_OSC_Type(v)
                if k == "contents":
                    obj_dict["CONTENTS"] = {}
                    for subNode in v:
                        if subNode.full_path is not None:
                            obj_dict["CONTENTS"][subNode.full_path.split("/")[-1]] = subNode
                        else:
                            continue
                else:
                    obj_dict[k.upper()] = v

            # FIXME: I missed something, so here's a hack!

            if "TYPE_" in obj_dict:
                del obj_dict["TYPE_"]
            return obj_dict

        if isinstance(o, type):
            return Python_Type_List_to_OSC_Type([o])

        if isinstance(o, OSCHostInfo):
            obj_dict = {}
            for k, v in vars(o).items():
                if v is None:
                    continue
                obj_dict[k.upper()] = v
            return obj_dict
        
        return json.JSONEncoder.default(self, o)

class OSCAccess(IntEnum):
    NO_VALUE = 0
    READONLY_VALUE = 1
    WRITEONLY_VALUE = 2
    READWRITE_VALUE = 3

class OSCQueryNode():
    def __init__(self, full_path=None, contents=None, type_=None, access=None, description=None, value=None, host_info=None):
        self.contents = contents
        self.full_path = full_path
        self.access = access
        self.type_ = type_
        # Value is always an array!
        self.value = value
        self.description = description
        self.host_info = host_info


    def find_subnode(self, full_path):
        if self.full_path == full_path:
            return self

        foundNode = None
        if self.contents is None:
            return None
        
        for subNode in self.contents:
            foundNode = subNode.find_subnode(full_path)
            if foundNode is not None:
                break

        return foundNode

    def add_child_node(self, child):
        if child == self:
            return

        path_split = child.full_path.rsplit("/",1)
        if len(path_split) < 2:
            raise Exception("Tried to add child node with invalid full path!")

        parent_path = path_split[0]

        if parent_path == '':
            parent_path = "/"

        parent = self.find_subnode(parent_path)

        if parent is None:
            parent = OSCQueryNode(parent_path)
            self.add_child_node(parent)
            
        
        if parent.contents is None:
            parent.contents = []
        parent.contents.append(child)

    
    def to_json(self):
        return json.dumps(self, cls=OSCNodeEncoder)


    def __iter__(self):
            yield self
            if self.contents is not None:
                for subNode in self.contents:
                    yield from subNode

    def __str__(self) -> str:
        return f'<OSCQueryNode @ {self.full_path} (D: "{self.description}" T:{self.type_} V:{self.value})>'

class OSCHostInfo():
    def __init__(self, name, extensions, osc_ip=None, osc_port=None, osc_transport=None, ws_ip=None, ws_port=None) -> None:
        self.name = name
        self.osc_ip = osc_ip
        self.osc_port = osc_port
        self.osc_transport = osc_transport
        self.ws_ip = ws_ip
        self.ws_port = ws_port
        self.extensions = extensions

    def to_json(self) -> str:
        return json.dumps(self, cls=OSCNodeEncoder)

    def __str__(self) -> str:
        return json.dumps(self, cls=OSCNodeEncoder)

def OSC_Type_String_to_Python_Type(typestr):
    types = []
    for typevalue in typestr:
        if typevalue == '':
            continue

        if typevalue == "i":
            types.append(int)
        elif typevalue == "f" or typevalue == "h" or typevalue == "d" or typevalue == "t":
            types.append(float)
        elif typevalue == "T" or typevalue == "F":
            types.append(bool)
        elif typevalue == "s":
            types.append(str)
        else:
            raise Exception(f"Unknown OSC type when converting! {typevalue} -> ???")


    return types


def Python_Type_List_to_OSC_Type(types_):
    output = []
    for type_ in types_:
        if type_ == int:
            output.append("i")
        elif type_ == float:
            output.append("f")
        elif type_ == bool:
            output.append("T")
        elif type_ == str:
            output.append("s")
        else:
            raise Exception(f"Cannot convert {type_} to OSC type!")

    return " ".join(output)


if __name__ == "__main__":
    root = OSCQueryNode("/", description="root node")
    root.add_child_node(OSCQueryNode("/test/node/one"))
    root.add_child_node(OSCQueryNode("/test/node/two"))
    root.add_child_node(OSCQueryNode("/test/othernode/one"))
    root.add_child_node(OSCQueryNode("/test/othernode/three"))

    #print(root)

    for child in root:
        print(child)