import pystray
import sys

from PIL import Image, ImageDraw

class TrayIcon:
    def __init__(self, stop_func, icon_path):
        self.icon = Image.open(icon_path)
        self.menu = pystray.Menu(
            pystray.MenuItem("Exit", stop_func)
        )
        self.tray_icon = pystray.Icon("tray_icon", self.icon, "ThumbparamsOSC", self.menu)

    def run(self):
        self.tray_icon.run_detached()

    def stop(self):
        self.tray_icon.stop()

if __name__ == "__main__":
    tray_icon = TrayIcon()
    tray_icon.run()