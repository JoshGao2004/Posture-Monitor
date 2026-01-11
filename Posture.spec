# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Collect MediaPipe data files (binary assets)
mediapipe_datas = collect_data_files('mediapipe')

a = Analysis(
    ['Posture.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('Presets', 'Presets'),
        ('Sounds', 'Sounds'),
    ] + mediapipe_datas,  # Add MediaPipe data files
    hiddenimports=[
        'cv2',
        'mediapipe',
        'numpy',
        'pygame',
        'winotify',
        'tkinter',
        'PIL._tkinter_finder',
        'mediapipe.python',
        'mediapipe.python.solutions',
        'mediapipe.python.solutions.face_mesh',
        'mediapipe.python.solutions.pose',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Posture',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if you want to see console output for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # You can add an icon file path here if you have one
)
