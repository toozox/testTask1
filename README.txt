Qt5Designer запускается командой 'pyqt5-tools designer'

Python модули интерфейса генерируются с помощью скрипта genPyFromUi.sh,
в конце таких файлов обязательно должно быть *Ui.py

В проекте используется python 3.7.9

При сборке под linux и при использовании pyenv, для сборки с помощью pyinstaller нужно
переустановить python следующим образом

    pyenv uninstall 3.7.9
    CONFIGURE_OPTS=--enable-shared pyenv install 3.7.9 -f

