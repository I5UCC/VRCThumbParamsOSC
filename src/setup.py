from cx_Freeze import setup, Executable

VERSION = open("VERSION").read().strip()

packages = ["argparse", "async_timeout", "certifi", "charset_normalizer", "idna", "ifaddr", "inputs", "lief", "openvr", "psutil", "pyparsing", "pythonosc", "requests", "urllib3", "zeroconf", "ctypes"]
exclude = ["tkinter", "lib2to3", "test", "unittest", "xmlrpc"]
file_include = ["config.json", "Run Debug Mode.bat", "bindings/", "app.vrmanifest", "VERSION"]
bin_excludes = ["_bz2.pyd", "_decimal.pyd", "_hashlib.pyd", "_lzma.pyd", "_queue.pyd", "_ssl.pyd", "libcrypto-1_1.dll", "libssl-1_1.dll", "ucrtbase.dll", "VCRUNTIME140.dll"]

build_exe_options = {"packages": packages, "excludes": exclude, "include_files": file_include, "bin_excludes": bin_excludes}

setup(
    name="ThumbParamsOSC",
    version=VERSION,
    description="ThumbParamsOSC",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", target_name="ThumbParamsOSC.exe", base=False, icon="icon.ico"), Executable("main.py", target_name="ThumbParamsOSC_NoConsole.exe", base="Win32GUI", icon="icon.ico")],
)
