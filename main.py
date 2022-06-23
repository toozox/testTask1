from PyQt5 import QtWidgets
from mainWindowUi import Ui_MainWindow


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)


def main():
    app = QtWidgets.QApplication([])
    w = MainWindow()
    w.show()
    exit(app.exec())


if __name__ == "__main__":
    main()
