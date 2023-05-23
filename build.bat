@echo off

cd %~dp0
rmdir /S /Q src/build
rmdir /S /Q build
rmdir /S /Q src\Configurator\Configurator\bin

cd src/Configurator
dotnet publish -r win-x64
cd ..
"../venv/Scripts/python.exe" setup.py build
cd build
robocopy exe.win-amd64-3.10 ThumbparamsOSC /MOVE /E /NFL /NDL /NJH /NJS /nc /ns /np
cd ..
powershell -c "copy Configurator\Configurator\bin\Debug\net4.8.1-windows\win-x64\publish\Configurator.exe build/ThumbparamsOSC/Configurator.exe"
powershell -c "copy Configurator\Configurator\bin\Debug\net4.8.1-windows\win-x64\publish\Newtonsoft.Json.dll build/ThumbparamsOSC/Newtonsoft.Json.dll"
cd %~dp0
robocopy src/build build /MOVE /E /NFL /NDL /NJH /NJS /nc /ns /np
cd build
7z a ThumbparamsOSC.zip ThumbparamsOSC