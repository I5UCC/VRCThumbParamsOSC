# -*- mode: python -*-

block_cipher = None

added_files = [
         ( 'bindings', 'bindings' ),
         ( 'config.json', '.' ),
		 ( 'openvr', 'openvr' ),
         ( 'Run Debug Mode.bat', '.' ),
         ]
a = Analysis(['ThumbParamsOSC.py'],
             pathex=['F:\GitRepos\VRCThumbParamsOSC'],
             binaries=[],
             datas = added_files,
             hiddenimports=['ctypes', 'colorama'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='ThumbParamsOSC',
          debug=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='ThumbParamsOSC')
