@echo off

cd %~dp0
rmdir /S /Q src\build
rmdir /S /Q build
rmdir /S /Q src\Thumbparams_Configurator\Thumbparams_Configurator\bin
rmdir /S /Q src\ThumbParamsOSC\bin

cd src

REM Build Thumbparams_Configurator
cd Thumbparams_Configurator
dotnet publish -r win-x64 -c Release
cd ..

REM Build ThumbParamsOSC (the main C# application, which replaces the Python build)
cd ThumbParamsOSC
dotnet publish -r win-x64 -c Release --self-contained true -p:PublishSingleFile=true -o ..\build\ThumbparamsOSC
cd ..

REM Copy Configurator.exe into the build output directory
powershell -c "copy Thumbparams_Configurator\Thumbparams_Configurator\bin\Release\net4.8.1-windows\win-x64\publish\Thumbparams_Configurator.exe build\ThumbparamsOSC\Configurator.exe"
powershell -c "copy Thumbparams_Configurator\Thumbparams_Configurator\bin\Release\net4.8.1-windows\win-x64\publish\Newtonsoft.Json.dll build\ThumbparamsOSC\Newtonsoft.Json.dll"
REM The copy above may be a no-op if the Configurator already ships without a separate Newtonsoft.Json.dll;
REM ThumbParamsOSC bundles its own copy via its publish output.

REM Copy supporting files (config, manifest, icon, VERSION, bindings)
powershell -c "copy config.json build\ThumbparamsOSC\config.json"
powershell -c "copy app.vrmanifest build\ThumbparamsOSC\app.vrmanifest"
powershell -c "copy icon.ico build\ThumbparamsOSC\icon.ico"
powershell -c "copy VERSION build\ThumbparamsOSC\VERSION"
robocopy bindings build\ThumbparamsOSC\bindings /E /NFL /NDL /NJH /NJS /nc /ns /np

cd %~dp0
robocopy src\build build /MOVE /E /NFL /NDL /NJH /NJS /nc /ns /np
cd build
7z a ThumbparamsOSC.zip ThumbparamsOSC