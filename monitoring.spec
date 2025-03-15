# -*- mode: python ; coding: utf-8 -*-


a = Analysis(['monitoring.py'],
             pathex=['.'],
             binaries=[('python_printer_status/CuCustomWndAPI.dll', 'python_printer_status'),
                       ('python_printer_status/FTPCtrl_x64.dll', 'python_printer_status')],
             datas=[('Icon/hutchisonport_logo.ico', 'Icon'),
                    ('Icon/MenuIcon.ico', 'Icon'),
                    ('python_printer_status/*', 'python_printer_status'),
                    ('Designer/*.ui', 'Designer'),
                    ('sumatra/SumatraPDF.exe', 'sumatra'),
                    ('sumatra/libmupdf.dll', 'sumatra'),
                    ('sumatra/PdfFilter.dll', 'sumatra'),
                    ('sumatra/PdfPreview.dll', 'sumatra'),
                    ('sumatra/SumatraPDF-settings.txt', 'sumatra')],
    hiddenimports=['schedule', 'requests'], 
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Printer_Management_Program_For_Automated_Gate_System',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Icon/hutchisonport_logo.ico'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='monitoring',
)
