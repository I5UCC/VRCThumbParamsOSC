import json
import sys
import os
import time
import traceback
import ctypes
import argparse
import logging
from osc import OSC
from ovr import OVR
from zeroconf._exceptions import NonUniqueNameException


def get_absolute_path(relative_path) -> str:
    """
    Gets absolute path relative to the executable.
    Parameters:
        relative_path (str): Relative path
    Returns:
        str: Absolute path
    """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def cls() -> None:
    """
    Clears Console.
    Returns:
        None
    """
    os.system('cls' if os.name == 'nt' else 'clear')


def print_debugoutput() -> None:
    """
    Prints the debugoutput string.
    Returns:
        None
    """
    def get_debug_string(parameter, value, floating="", always = False) -> str:
        if isinstance(value, float):
            value = f"{value:.4f}"

        tmp = ""
        if floating != "" and float(floating) > 0:
            tmp = f"Floating: {floating}s"
        tmp2 = ""
        if always:
            tmp2 = "-Always send-"
        return f"{parameter.ljust(23, ' ')}\t{str(value).ljust(10, ' ')}\t{tmp}\t{tmp2}\n"

    _debugoutput = ""
    cls()

    if config["ControllerType"]["enabled"]:
        _debugoutput += get_debug_string("ControllerType", config["ControllerType"]["last_value"], "", config["ControllerType"]["always"])
    if config["LeftThumb"]["enabled"]:
        _debugoutput += get_debug_string("LeftThumb", config["LeftThumb"]["last_value"], "", config["LeftThumb"]["always"])
    if config["RightThumb"]["enabled"]:
        _debugoutput += get_debug_string("RightThumb", config["RightThumb"]["last_value"], "", config["RightThumb"]["always"])
    if config["LeftABButtons"]["enabled"]:
        _debugoutput += get_debug_string("LeftABButtons", config["LeftABButtons"]["last_value"], "", config["LeftABButtons"]["always"])
    if config["RightABButtons"]["enabled"]:
        _debugoutput += get_debug_string("RightABButtons", config["RightABButtons"]["last_value"], "", config["RightABButtons"]["always"])

    for action in config["actions"]:
        if action["enabled"]:
            if action["type"] == "vector2":
                _debugoutput += get_debug_string(action["osc_parameter"][0], action["last_value"][0], action["floating"][0], action["always"][0])
                _debugoutput += get_debug_string(action["osc_parameter"][1], action["last_value"][1], action["floating"][1], action["always"][1])
                if len(action["osc_parameter"]) > 2:
                    _debugoutput += get_debug_string(action["osc_parameter"][2], action["last_value"][2], action["floating"][2], action["always"][2])
            else:
                _debugoutput += get_debug_string(action["osc_parameter"], action["last_value"], action["floating"], action["always"])

    print(_debugoutput)


def resend_parameters(avatar_id) -> None:
    """
    Resends all parameters to the new avatar.
    Parameters:
        avatar_id (str): Avatar ID
    Returns:
        None
    """
    global osc

    if osc.curr_avatar == avatar_id:
        return

    logging.info(f"Resending parameters to {avatar_id}")
    osc.curr_avatar = avatar_id

    if config["ControllerType"]["enabled"]:
        osc.send_parameter("ControllerType", config["ControllerType"]["last_value"])
    if config["LeftThumb"]["enabled"]:
        osc.send_parameter("LeftThumb", config["LeftThumb"]["last_value"])
    if config["RightThumb"]["enabled"]:
        osc.send_parameter("RightThumb", config["RightThumb"]["last_value"])
    if config["LeftABButtons"]["enabled"]:
        osc.send_parameter("LeftABButtons", config["LeftABButtons"]["last_value"])
    if config["RightABButtons"]["enabled"]:
        osc.send_parameter("RightABButtons", config["RightABButtons"]["last_value"])

    for action in config["actions"]:
        if action["type"] == "vector2":
            osc.send_parameter(action["osc_parameter"][0], action["last_value"][0])
            osc.send_parameter(action["osc_parameter"][1], action["last_value"][1])
            if len(action["osc_parameter"]) > 2:
                osc.send_parameter(action["osc_parameter"][2], action["last_value"][2])
            continue
        osc.send_parameter(action["osc_parameter"], action["last_value"])


def handle_input() -> None:
    """
    Handles SteamVR input and sends it to VRChat.
    Returns:
        None
    """
    ovr.poll_next_events()
    osc.refresh_time()

    if config["ControllerType"]["enabled"] and (osc.curr_time - config["ControllerType"]["timestamp"] > 10.0 or config["ControllerType"]["always"]):
        _controller_type = ovr.get_controllertype()
        osc.send("ControllerType", _controller_type)

    _strinputs = ""
    for action in config["actions"][:8]: # Touch Actions
        val = ovr.get_value(action)
        _strinputs += "1" if val else "0"
        osc.send(action, val)
    osc.send("LeftThumb", _strinputs[:4].rfind("1") + 1)
    osc.send("RightThumb", _strinputs[4:].rfind("1") + 1)
    osc.send("LeftABButtons", _strinputs[0] == "1" and _strinputs[1] == "1")
    osc.send("RightABButtons", _strinputs[4] == "1" and _strinputs[5] == "1")

    for action in config["actions"][8:]:
        val = ovr.get_value(action)
        osc.send(action, val)

    if args.debug:
        print_debugoutput()


def stop() -> None:
    """
    Stops the program.
    Returns:
        None
    """
    ovr.shutdown()
    osc.shutdown()
    sys.exit()


logging.basicConfig(level=logging.DEBUG if len(sys.argv) > 1 else logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', handlers=[logging.StreamHandler(), logging.FileHandler(get_absolute_path("log.log"))])

# Argument Parser
parser = argparse.ArgumentParser(description='ThumbParamsOSC: Takes button data from SteamVR and sends it to an OSC-Client')
parser.add_argument('-d', '--debug', required=False, action='store_true', help='prints values for debugging')
parser.add_argument('-i', '--ip', required=False, type=str, help="set OSC ip. Default=127.0.0.1")
parser.add_argument('-p', '--port', required=False, type=str, help="set OSC port. Default=9000")
args = parser.parse_args()

if os.name == 'nt':
    ctypes.windll.kernel32.SetConsoleTitleW("ThumbParamsOSC v2.0.0-Beta" + (" (Debug)" if args.debug else ""))

CONFIG_PATH = get_absolute_path('config.json')
MANIFEST_PATH = get_absolute_path("app.vrmanifest")
FIRST_LAUNCH_FILE = get_absolute_path("bindings/first_launch")
config = json.load(open(CONFIG_PATH))
config["IP"] = args.ip if args.ip else config["IP"]
config["Port"] = args.port if args.port else config["Port"]
POLLINGRATE = 1 / float(config['PollingRate'])

try:
    ovr = OVR(config, CONFIG_PATH, MANIFEST_PATH, FIRST_LAUNCH_FILE)
    osc = OSC(config, lambda addr, value: resend_parameters(value))
except OSError as e:
    logging.error("You can only bind to the port 9001 once.")
    logging.error(traceback.format_exc())
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(0, "You can only bind to the port 9001 once.", "AvatarParameterSync - Error", 0)
    stop()
except NonUniqueNameException as e:
    logging.error("NonUniqueNameException, trying again...")
    os.execv(sys.executable, ['python'] + sys.argv)
except Exception as e:
    logging.error("UNEXPECTED ERROR\n")
    logging.error("Please Create an Issue on GitHub with the following information:\n")
    logging.error(traceback.format_exc())
    input("\nPress ENTER to exit")
    stop()

logging.info("ThumbParamsOSC running...")
logging.info(f"IP: {osc.ip}")
logging.info(f"Port: {osc.port}")
logging.info(f"Server Port: {osc.server_port}")
logging.info(f"HTTP Port: {osc.http_port}")
logging.info(f"PollingRate: {POLLINGRATE}s ({config['PollingRate']} Hz)")
logging.info(f"StickMoveTolerance: {osc.stick_tolerance} ({config['StickMoveTolerance']}%)")
logging.info("Open Configurator.exe to change sent Parameters and other Settings.")

# Main Loop
while True:
    try:
        handle_input()
        time.sleep(POLLINGRATE)
    except KeyboardInterrupt:
        cls()
        stop()
    except Exception:
        cls()
        logging.error("UNEXPECTED ERROR\n")
        logging.error("Please Create an Issue on GitHub with the following information:\n")
        logging.error(traceback.format_exc())
        input("\nPress ENTER to exit")
        stop()
