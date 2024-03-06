import argparse
import ctypes
import json
import logging
import os
import sys
import time
import traceback
import glob
import shutil
from threading import Thread

from zeroconf._exceptions import NonUniqueNameException

from osc import OSC
from ovr import OVR
from xbox_controller import XboxController


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


def print_debugoutput() -> None:
    """
    Prints the debugoutput string.
    Returns:
        None
    """
    index = 0
    _debugoutput = ""
    os.system('cls' if os.name == 'nt' else 'clear')

    def get_debug_string(parameter, value, floating="", always = 0) -> str:
        nonlocal index
        if isinstance(value, float):
            value = f"{value:.4f}"

        if floating != "" and float(floating) > 0:
            floating = f"Floating: {floating}s"
        else:
            floating = ""
        match always:
            case 0:
                always = "SOC"
            case 1:
                always = "SOP"
            case _:
                always = ""
        
        res = f"{parameter.ljust(23, ' ')}\t{str(value).ljust(6, ' ')}\t{floating.ljust(10, ' ')}\t{always}\t" + ("\n" if index % 2 == 0 else "")
        index += 1
        return res

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

    for action in config["xinput_actions"]:
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
        if _controller_type == 0 and xinput.is_plugged:
            _controller_type = 10
        elif _controller_type != 0 and xinput.is_plugged:
            _controller_type += 10
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

    # xinput buttons
    for action in config["xinput_actions"]:
        val = xinput.get_value(action)
        osc.send(action, val)

    if debug:
        print_debugoutput()


def get_server_needed() -> bool:
    """
    Checks if the OSC server is needed.
    """
    if config["ControllerType"]["enabled"] and not config["ControllerType"]["always"]:
        return True
    if config["LeftThumb"]["enabled"] and not config["LeftThumb"]["always"]:
        return True
    if config["RightThumb"]["enabled"] and not config["RightThumb"]["always"]:
        return True
    if config["LeftABButtons"]["enabled"] and not config["LeftABButtons"]["always"]:
        return True
    if config["RightABButtons"]["enabled"] and not config["RightABButtons"]["always"]:
        return True
    for action in config["actions"]:
        if action["type"] != "vector2":
            if not action["always"] and action["enabled"]:
                return True
            continue
        if not action["always"][0] and action["enabled"][0] or not action["always"][1] and action["enabled"][1]:
            return True
        if len(action["always"]) > 2 and not action["always"][2] and action["enabled"][2]:
            return True
    return False


def stop() -> None:
    """
    Stops the program.
    Returns:
        None
    """
    xinput.running = False
    ovr.shutdown()
    osc.shutdown()


logging.basicConfig(level=logging.DEBUG if len(sys.argv) > 1 else logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', handlers=[logging.StreamHandler(), logging.FileHandler(get_absolute_path("log.log"))])

VERSION = open(get_absolute_path("VERSION")).read().strip()

# Argument Parser
parser = argparse.ArgumentParser(description='ThumbParamsOSC: Takes button data from SteamVR and sends it to an OSC-Client')
parser.add_argument('-d', '--debug', required=False, action='store_true', help='prints values for debugging')
parser.add_argument('-i', '--ip', required=False, type=str, help="set OSC ip. Default=127.0.0.1")
parser.add_argument('-p', '--port', required=False, type=str, help="set OSC port. Default=9000")
ip = None
port = None
debug = False
try:
    args = parser.parse_args()
    ip = args.ip
    port = args.port
    debug = args.debug
except Exception as e:
    logging.error("Argument Error, continuing without arguments")
    ip = None
    port = None
    debug = False

if os.name == 'nt':
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(f"ThumbParamsOSC {VERSION}" + (" (Debug)" if debug else ""))
    except Exception:
        pass

CONFIG_PATH = get_absolute_path('config.json')
MANIFEST_PATH = get_absolute_path("app.vrmanifest")
FIRST_LAUNCH_FILE = get_absolute_path("bindings/first_launch")
config: dict = json.load(open(CONFIG_PATH))
config["IP"] = ip if ip else config["IP"]
config["Port"] = port if port else config["Port"]
POLLINGRATE = 1 / float(config['PollingRate'])

try:
    if os.path.isfile(FIRST_LAUNCH_FILE):
        if os.name == "nt":
            ctypes.windll.user32.MessageBoxW(0, "ThumbParamsOSC is now running and has registered as an Overlay on Steam.\nIt will now open automatically with SteamVR\nOpen Configurator.exe to change sent Parameters and other Settings if you havent yet.\n.This is only shown once.", "ThumbparamsOSC", 0)
        logging.info("First Launch, deleting OSC cache. Registering app to run on SteamVR start...")
        cache_path = os.getenv('APPDATA') + '\\..\\LocalLow\\VRChat\\VRChat\\OSC\\usr_*'
        user_folders = glob.glob(cache_path)
        for folder in user_folders:
            shutil.rmtree(folder)
except Exception as e:
    logging.error("Error while deleting OSC cache.")
    logging.error(traceback.format_exc())

try:
    ovr: OVR = OVR(config, CONFIG_PATH, MANIFEST_PATH, FIRST_LAUNCH_FILE)
    osc: OSC = OSC(config, lambda addr, value: resend_parameters(value), get_server_needed())
    xinput = XboxController(polling_rate=config.get("XInputPollingRate", 1000))
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

logging.info(f"ThumbParamsOSC {VERSION} running...")
logging.info(f"IP: {osc.ip}")
logging.info(f"Port: {osc.port}")
logging.info(f"Server Port: {osc.server_port}")
logging.info(f"HTTP Port: {osc.http_port}")
logging.info(f"PollingRate: {POLLINGRATE}s ({config['PollingRate']} Hz)")
logging.info(f"StickMoveTolerance: {osc.stick_tolerance} ({config['StickMoveTolerance']}%)")
logging.info("Open Configurator.exe to change sent Parameters and other Settings.")


def main_loop():
    # Main Loop
    while True:
        handle_input()
        time.sleep(POLLINGRATE)


try:
    thread = Thread(target=xinput.polling_loop, daemon=True)
    thread.start()
    main_loop()
except KeyboardInterrupt:
    pass
except Exception:
    logging.error("UNEXPECTED ERROR\n")
    logging.error("Please Create an Issue on GitHub with the following information:\n")
    logging.error(traceback.format_exc())
    input("\nPress ENTER to exit")
stop()
