@echo off

cd %~dp0
rmdir /S /Q src/build
rmdir /S /Q build

cd src/Configurator
dotnet publish -r win-x64 -p:PublishSingleFile=true --self-contained false
cd ..
"../venv/Scripts/python.exe" setup.py build
cd build
robocopy exe.win-amd64-3.10 ThumbparamsOSC /MOVE /E /NFL /NDL /NJH /NJS /nc /ns /np
cd ..
powershell -c "copy Configurator\Configurator\bin\Debug\net6.0-windows\win-x64\publish\Configurator.exe build/ThumbparamsOSC/Configurator.exe"
cd %~dp0
robocopy src/build build /MOVE /E /NFL /NDL /NJH /NJS /nc /ns /np
cd build
7z a ThumbparamsOSC.zip ThumbparamsOSC