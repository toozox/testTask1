import PyInstaller.__main__
from PyQt5 import uic
import platform

VERSION = "v1.0"
NAME = "TestTask1-" + VERSION + "-" + platform.system().lower()


UI_FILES = ['mainWindow.ui',
            ]

for uiFile in UI_FILES:
    with open(uiFile[:-3]+'Ui.py', 'w', encoding='utf8') as pyFile:
        uic.compileUi(uiFile, pyFile, from_imports=True)

PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--windowed',
    '-n ' + NAME
])
