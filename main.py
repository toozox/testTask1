from PyQt5 import QtWidgets
from sys import exit
from mainWindowUi import Ui_MainWindow
import numpy

# Описываем номера столбцов, чтобы в коде проще было ориентироваться
# и легко изменять их значения в случае необходимости
COL_SUM_RES = 0  # столбец, где выводится сумма значений COL_SUM столбца
COL_SUM = 2  # столбец для суммы значений
COL_COMBO_BOX = 1  # столбец, где данные вводятся через выпадающий список
COL_COLOR_BACK = 2  # столбец, где ячейки подкрашиваются
COL_CALCULATED = 3  # столбец, где данные пересчитываются, на основе данных из COL_COLOR_BACK столбца


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        # инициализация окна
        super(MainWindow, self).__init__()
        self.setupUi(self)

        # тип данных сделал целый, в задании это чётко не обговаривалось,
        # поэтому решил тут немного самовольничать :)
        self.array = numpy.empty((0, 0), dtype='int16')
        self.initTable()

    # начальная инициализация таблицы
    def initTable(self):
        colCount = 4
        rowCount = 0
        self.tableWidget.setColumnCount(colCount)
        self.tableWidget.setRowCount(rowCount)

        # названия столбцов
        headerLabels = ['', '', '', '']
        headerLabels[COL_SUM_RES] = 'Сумма'
        headerLabels[COL_COMBO_BOX] = 'Вып.сп.'
        headerLabels[COL_COLOR_BACK] = 'Цвет'
        headerLabels[COL_CALCULATED] = 'Вычисл.'
        self.tableWidget.setHorizontalHeaderLabels(headerLabels)

        # инициализация значений и ограничений в счётчиках кол-ва столбцов и строк
        self.countOfRowsSpinBox.setValue(rowCount)
        self.countOfColsSpinBox.setValue(colCount)
        self.countOfRowsSpinBox.setMinimum(rowCount)
        self.countOfColsSpinBox.setMinimum(colCount)

        # добавление строки, чтобы сразу было видно, что да как примерно
        self.addRow()

    # добавить строку в талицу и numpy массив
    def addRow(self):
        pass


def main():
    app = QtWidgets.QApplication([])
    w = MainWindow()
    w.show()
    exit(app.exec())


if __name__ == "__main__":
    main()
