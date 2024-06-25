import openvr
import openvr.error_code
import os
import logging

FINGERS = {
    "Thumb": openvr.VRFinger_Thumb,
    "Index": openvr.VRFinger_Index,
    "Middle": openvr.VRFinger_Middle,
    "Ring": openvr.VRFinger_Ring,
    "Pinky": openvr.VRFinger_Pinky
}

SPLAYFINGERS = {
    "Index": openvr.VRFingerSplay_Thumb_Index,
    "Middle": openvr.VRFingerSplay_Index_Middle,
    "Ring": openvr.VRFingerSplay_Middle_Ring,
    "Pinky": openvr.VRFingerSplay_Ring_Pinky
}

class OVR:
    def __init__(self, config:dict, config_path: str, manifest_path: str, first_launch_file: str):
        self.application = openvr.init(openvr.VRApplication_Utility)
        logging.info("OpenVR Initialized.")
        openvr.VRInput().setActionManifestPath(config_path)
        openvr.VRApplications().addApplicationManifest(manifest_path)
        logging.info("Application Manifest Added.")
        if os.path.isfile(first_launch_file):
            openvr.VRApplications().setApplicationAutoLaunch("i5ucc.thumbparamsosc", True)
            logging.info("Application set to auto launch.")
            os.remove(first_launch_file)
        self.action_set_handle = openvr.VRInput().getActionSetHandle("/actions/thumbparams")
        self.actionsets = (openvr.VRActiveActionSet_t * 1)()
        self.actionset = self.actionsets[0]
        self.actionset.ulActionSet = self.action_set_handle
        for action in config["actions"]:
            action["handle"] = openvr.VRInput().getActionHandle(action['name'])


    def get_controllertype(self) -> int:
        """
        Gets the type of controller from SteamVR.
        Returns:
            int: Type of controller (0 = Unknown, 1 = Knuckles, 2 = Oculus/Meta Touch)
        """
        for i in range(1, openvr.k_unMaxTrackedDeviceCount):
            device_class = openvr.VRSystem().getTrackedDeviceClass(i)
            if device_class == 2:
                match openvr.VRSystem().getStringTrackedDeviceProperty(i, openvr.Prop_ControllerType_String):
                    case 'knuckles':
                        return 1
                    case 'oculus_touch':
                        return 2
                    case _:
                        return 0
        return 0


    def get_value(self, action: dict) -> bool | float | tuple | openvr.VRSkeletalSummaryData_t | None:
        """
        Gets the value of an action by querying SteamVR.
        Parameters:
            action (dict): Action
        Returns:
            any: Value of the action
        """
        match action['type']:
            case "boolean":
                return bool(openvr.VRInput().getDigitalActionData(action['handle'], openvr.k_ulInvalidInputValueHandle).bState)
            case "vector1":
                return float(openvr.VRInput().getAnalogActionData(action['handle'], openvr.k_ulInvalidInputValueHandle).x)
            case "vector2":
                tmp = openvr.VRInput().getAnalogActionData(action['handle'], openvr.k_ulInvalidInputValueHandle)
                return tmp.x, tmp.y
            case "skeleton":
                try:
                    tmp = openvr.VRInput().getSkeletalSummaryData(action['handle'], openvr.VRSummaryType_FromDevice)
                    return tmp
                except openvr.error_code.InputError_NoData:
                    return None
            case _:
                raise TypeError("Unknown action type: " + action['type'])


    def poll_next_events(self):
        _event = openvr.VREvent_t()
        _has_events = True
        while _has_events:
            _has_events = self.application.pollNextEvent(_event)
        openvr.VRInput().updateActionState(self.actionsets)


    def shutdown(self) -> bool:
        """Shuts down the OVR handler."""

        try:
            openvr.shutdown()
            return True
        except Exception as e:
            print("Error shutting down OVR: " + str(e))
            return False
