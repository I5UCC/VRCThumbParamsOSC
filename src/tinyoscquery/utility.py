import socket

def get_open_tcp_port():
    '''
    Returns a valid, open, TCP port.

        Returns:
            port (int): A TCP port that is able to be bound to
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port

def get_open_udp_port():
    '''
    Returns a valid, open, UDP port.

        Returns:
            port (int): A UDP port that is able to be bound to
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port

def check_if_tcp_port_open(port: int):
    '''
    Checks if a TCP port is open.

        Args:
            port (int): The port to check

        Returns:
            open (bool): True if the port is open, False if it is not
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("", port))
        s.close()
        return True
    except OSError:
        return False
    
def check_if_udp_port_open(port: int):
    '''
    Checks if a UDP port is open.

        Args:
            port (int): The port to check

        Returns:
            open (bool): True if the port is open, False if it is not
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.bind(("", port))
        s.close()
        return True
    except OSError:
        return False