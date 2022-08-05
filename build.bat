@echo off
RMDIR /S /Q build
RMDIR /S /Q dist

pyinstaller --clean -y .\ThumbParamsOSC.spec

DEL /F /Q dist\ThumbParamsOSC\_bz2.pyd
DEL /F /Q dist\ThumbParamsOSC\_decimal.pyd
DEL /F /Q dist\ThumbParamsOSC\_hashlib.pyd
DEL /F /Q dist\ThumbParamsOSC\_lzma.pyd
DEL /F /Q dist\ThumbParamsOSC\_queue.pyd
DEL /F /Q dist\ThumbParamsOSC\_ssl.pyd

DEL /F /Q dist\ThumbParamsOSC\libcrypto-1_1.dll
DEL /F /Q dist\ThumbParamsOSC\libssl-1_1.dll
DEL /F /Q dist\ThumbParamsOSC\ucrtbase.dll
DEL /F /Q dist\ThumbParamsOSC\VCRUNTIME140.dll

DEL /F /Q dist\ThumbParamsOSC\api-*
RMDIR /S /Q dist\ThumbParamsOSC\altgraph-0.17.2.dist-info
RMDIR /S /Q dist\ThumbParamsOSC\pyinstaller-5.1.dist-info

