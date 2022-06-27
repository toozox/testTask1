from sys import exit

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal
import numpy
import h5py

from mainWindowUi import Ui_MainWindow

# Описываем номера столбцов, чтобы в коде проще было ориентироваться
# и легко изменять их значения в случае необходимости
COL_SUM_RES = 0  # столбец, где выводится сумма значений COL_SUM столбца
                 # !!! COL_SUM_RES не изменять, в коде не предусмотрена
                 # такая возможность
COL_SUM = 2  # столбец откуда считается сумма значений
COL_COMBO_BOX = 1  # столбец, где данные вводятся через выпадающий список
COL_COLOR_BACK = 2  # столбец, где ячейки подкрашиваются
COL_CALCULATED = 3  # столбец, где данные пересчитываются, на основе данных из COL_COLOR_BACK столбца

# значения индексов для Qt таблицы и numpy массива не совпадают, потому что сумма столбца
# выводится только в Qt таблице и в numpy массиве мы его не храним
# получается, что для numpy массива индексы двинуты на одно значение влево
NP_COL_SUM = COL_SUM - 1  # столбец откуда считается сумма значений
NP_COL_COMBO_BOX = COL_COMBO_BOX - 1  # столбец, где данные вводятся через выпадающий список
NP_COL_COLOR_BACK = COL_COLOR_BACK - 1  # столбец, где ячейки подкрашиваются
NP_COL_CALCULATED = COL_CALCULATED - 1  # столбец, где данные пересчитываются, на основе данных из
                                        # COL_COLOR_BACK столбца

# минимальное и максимальное значение, которое можно выбрать
# в выпадающем списке
MIN_COMBO_BOX_VALUE = 1
MAX_COMBO_BOX_VALUE = 5  # включительно

MIN_COLS = 4  # минимальное количество столбцов, которые могут быть

H5_FILES = "h5 files (*.h5)"
TEXT_FILES = "Text files(*.txt)"
ALLOWED_FILE_FORMATS = [TEXT_FILES, H5_FILES]


# Свой класс выпадающего списка, чтобы была возможность отправлять данные, необходимые
# для изменения numpy массива
class CellComboBox(QtWidgets.QComboBox):
    # Создаём сигнал, если данные изменятся, отправляем значения строки, столбца и само значение
    valueChanged = pyqtSignal(int, int, int)  # (row, column, value)

    def __init__(self, row, column, value):
        super().__init__()
        self.row = row
        self.column = column
        self.values = [str(x) for x in range(MIN_COMBO_BOX_VALUE, MAX_COMBO_BOX_VALUE + 1)]
        self.addItems(self.values)
        self.setCurrentIndex(self.values.index(str(value)))
        self.currentIndexChanged.connect(self.indexChanged)

    def indexChanged(self):
        value = int(self.currentText())
        self.valueChanged.emit(self.row, self.column, value)


# Свой класс счётчика, чтобы была возможность получать сигналы,
# что этот объект больше не в фокусе
class MySpinBox(QtWidgets.QSpinBox):
    # этот сигнал необходим в случае, если
    # пользователь ввёл данные с клавиатуры, но не нажал Enter,
    # тогда необходимо вернуть значения в счётчике на изначальное
    focusOut = pyqtSignal()

    def __init__(self, minValue=0, maxValue=99):
        super(MySpinBox, self).__init__()
        self.setMinimum(minValue)
        self.setMaximum(maxValue)
        # При ручном изменении количества строк срабатывает сигнал valueChanged,
        # например, если значение изначально было 20, при вводе с клавиатуры 10, сначала
        # отправится сигнал со значением 1, потом только со значением 10. После того как
        # ввели 10 и нажать Enter, сигнал отправится ещё раз со значением 10.
        # В обработчике сигнала будет проверка предыдущего значения previousValue и текущего,
        # если они совпадают, произвести изменения в данных.
        self.previousValue = minValue
        self.setValue(minValue)

    def focusOutEvent(self, e):
        self.focusOut.emit()
        super(MySpinBox, self).focusOutEvent(e)

    def setPreviousValue(self, value):
        self.previousValue = value

    def getPreviousValue(self):
        return self.previousValue


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        # инициализация окна
        super(MainWindow, self).__init__()
        self.setupUi(self)

        # меняем виджеты счётчика, чтобы была возможность
        # обрабатывать сигналы переключения фокуса
        myRowCountSpinBox = MySpinBox(0)
        myColumnCountSpinBox = MySpinBox(MIN_COLS)
        self.horizontalLayout.replaceWidget(self.countOfRowsSpinBox, myRowCountSpinBox)
        self.horizontalLayout.replaceWidget(self.countOfColsSpinBox, myColumnCountSpinBox)
        self.countOfRowsSpinBox.deleteLater()
        self.countOfColsSpinBox.deleteLater()
        self.countOfRowsSpinBox = myRowCountSpinBox
        self.countOfColsSpinBox = myColumnCountSpinBox
        # подписываемся на сигналы
        self.countOfRowsSpinBox.focusOut.connect(self.rowsSpinBoxFocusOut)
        self.countOfColsSpinBox.focusOut.connect(self.columnsSpinBoxFocusOut)
        self.countOfRowsSpinBox.valueChanged.connect(self.rowCountChanged)
        self.countOfColsSpinBox.valueChanged.connect(self.columnCountChanged)

        self.saveButton.clicked.connect(self.saveFile)
        self.openButton.clicked.connect(self.openFile)
        self.saveAction.triggered.connect(self.saveFile)
        self.openAction.triggered.connect(self.openFile)

        # обработка сигналов на выделение столбцов
        self.tableWidget.selectionModel().selectionChanged.connect(self.drawGraph)

        # тип данных сделал целый, в задании это чётко не обговаривалось,
        # поэтому решил тут немного самовольничать :)
        self.array = numpy.empty((0, MIN_COLS-1), dtype='uint8')
        self.initTable()

    # начальная инициализация таблицы
    def initTable(self):
        colCount = MIN_COLS
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

        # добавление строки, чтобы сразу было видно, что да как примерно
        self.addRow()
        # изменяем значение в счётчике строк
        self.countOfRowsSpinBox.setValue(1)

    # добавить строку в талицу и numpy массив
    def addRow(self):
        columnCount = self.tableWidget.columnCount()
        randValueOfComboBox = numpy.random.randint(MIN_COMBO_BOX_VALUE, MAX_COMBO_BOX_VALUE+1)

        # генерируем и считаем значения для вставки в итоговый массив
        addValues = list()
        for i in range(columnCount-1):  # columnCount-1, потому что в numpy массиве нет суммы столбца
            if i == NP_COL_COMBO_BOX:
                addValues.append(randValueOfComboBox)
                continue
            if i == NP_COL_CALCULATED:
                addValues.append(0)
                continue
            addValues.append(self.getRandValue())
        # считаем значение для необходимого столбца
        addValues[NP_COL_CALCULATED] = self.getCalculatedValue(addValues[NP_COL_COLOR_BACK])
        # можно конечно передать в numpy.vstack просто список addValues,
        # но тогда тип массива поменяется на тип по-умолчанию
        addValuesNPArray = numpy.array(addValues, dtype=self.array.dtype)
        # вставляем строку в массив
        self.array = numpy.vstack((self.array, addValuesNPArray))
        self.insertIntoTableRow(addValues)

    # добавить столбец в талицу и numpy массив
    def addColumn(self):
        rowCount = self.tableWidget.rowCount()
        # генерация случайных значений для добавления
        addValues = [self.getRandValue() for i in range(rowCount)]
        # сразу получаем перевёрнутый массив для вставки в numpy массив
        addValuesNPArray = numpy.array(addValues, dtype=self.array.dtype)[..., None]
        # вставляем столбец в массив и талбицу Qt
        self.array = numpy.hstack((self.array, addValuesNPArray))
        self.insertIntoTableColumn(addValues)

    # удаление строки в numpy массиве и Qt таблице
    def deleteRows(self, countToDelete=1):
        self.array = self.array[:-countToDelete, :]
        for i in range(countToDelete):
            self.tableWidget.removeRow(self.tableWidget.rowCount()-1)
        self.setSumCol()

    # удаление столбца в numpy массиве и Qt таблице
    def deleteColumns(self, countToDelete=3):
        # проверка, чтобы не удалить нужные колонки
        colCount = self.tableWidget.columnCount()
        # эта проверка на случай, чтобы не удалить необходимые колонки
        if colCount - countToDelete < MIN_COLS:
            countToDelete = colCount - MIN_COLS
        if countToDelete == 0:
            return

        self.array = self.array[:, :-countToDelete]
        for i in range(countToDelete):
            self.tableWidget.removeColumn(self.tableWidget.columnCount()-1)

    # выводим значения в таблицу Qt
    def insertIntoTableRow(self, values):
        row = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row)
        self.tableWidget.scrollToBottom()
        col = 1  # потому что в 0 позиции сумма
        for el in values:
            if col == COL_COMBO_BOX:
                # добавляем в ячейку выпадающий список
                self.tableWidget.setCellWidget(row, COL_COMBO_BOX, self.getComboBox(row, COL_COMBO_BOX, el))
                col += 1
                continue
            # записываем значения в ячейку
            cellinfo = QtWidgets.QTableWidgetItem(str(el))
            self.tableWidget.setItem(row, col, cellinfo)
            if col == COL_COLOR_BACK:
                self.setBackgroundColor(row, col)
            col += 1

        # установка значения суммы колонки
        self.setSumCol()

    # выводим значения в Qt таблицу
    def insertIntoTableColumn(self, values):
        col = self.tableWidget.columnCount()
        self.tableWidget.insertColumn(col)
        row = 0
        for el in values:
            cellinfo = QtWidgets.QTableWidgetItem(str(el))
            self.tableWidget.setItem(row, col, cellinfo)
            row += 1

    # слот для обработки изменений в счётчике строк
    # value - значение, на которое оно поменялось
    def rowCountChanged(self, value):
        previousValue = self.countOfRowsSpinBox.getPreviousValue()
        self.countOfRowsSpinBox.setPreviousValue(value)
        # если нажать Enter, предыдущее значение и текущее совпадают
        if value == previousValue or abs(previousValue-value) == 1:
            rowCount = self.tableWidget.rowCount()
            if value > rowCount:
                # добавляем данные
                countOfAddedRows = value - self.tableWidget.rowCount()
                for i in range(countOfAddedRows):
                    self.addRow()
            elif value < rowCount:
                # удаляем данные
                countOfDeletedRows = abs(value - self.tableWidget.rowCount())
                self.deleteRows(countOfDeletedRows)

    def columnCountChanged(self, value):
        previousValue = self.countOfColsSpinBox.getPreviousValue()
        self.countOfColsSpinBox.setPreviousValue(value)
        # если нажать Enter, предыдущее значение и текущее совпадают
        if value == previousValue or abs(previousValue-value) == 1:
            colCount = self.tableWidget.columnCount()
            if value > colCount:
                # добавляем данные
                countOfAddedCols = value - colCount
                for i in range(countOfAddedCols):
                    self.addColumn()
            elif value < colCount:
                # удаляем данные
                countOfDeletedCols = abs(value - colCount)
                self.deleteColumns(countOfDeletedCols)

    def rowsSpinBoxFocusOut(self):
        self.countOfRowsSpinBox.setValue(self.tableWidget.rowCount())

    def columnsSpinBoxFocusOut(self):
        self.countOfColsSpinBox.setValue(self.tableWidget.columnCount())

    # получить случайное значение для numpy массива
    def getRandValue(self):
        maxVal = numpy.iinfo(self.array.dtype).max
        minVal = numpy.iinfo(self.array.dtype).min
        return numpy.random.randint(minVal, maxVal, dtype=self.array.dtype)

    @staticmethod
    def getCalculatedValue(inputValue):
        return int(inputValue/6)

    def getComboBox(self, row, column, value):
        comboBox = CellComboBox(row, column, value)
        comboBox.valueChanged.connect(self.setNPArrayValue)
        return comboBox

    # изменяем в numpy массиве значения, полученные из таблицы
    def setNPArrayValue(self, row, column, value):
        self.array[row, column-1] = value

    def setBackgroundColor(self, row, col):
        value = int(self.tableWidget.item(row, col).text())
        if value < 0:
            self.tableWidget.item(row, col).setBackground(QtGui.QColor(217, 125, 129))
        elif value > 0:
            self.tableWidget.item(row, col).setBackground(QtGui.QColor(91, 214, 118))

    # вызывается каждый раз, когда добавляется строка
    # сумма не хранится в numpy массиве
    def setSumCol(self):
        sum = numpy.sum(self.array[:, NP_COL_SUM])
        cellinfo = QtWidgets.QTableWidgetItem(str(sum))
        self.tableWidget.setItem(0, COL_SUM_RES, cellinfo)

    def saveFile(self):
        fname = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить файл", "", ";;".join(ALLOWED_FILE_FORMATS))
        # если нажали "Отмена"
        if fname[0] == '':
            return
        if fname[1] == H5_FILES:
            self.saveToH5File(fname[0])
        elif fname[1] == TEXT_FILES:
            self.saveToTextFile(fname[0])

    def saveToH5File(self, fname):
        # дописываем формат файла, если пользователь их не ввёл
        if fname[-3:] != '.h5':
            fname = fname + '.h5'
        with h5py.File(fname, 'w') as hf:
            hf.create_dataset('array', data=self.array)

    def saveToTextFile(self, fname):
        # дописываем формат файла, если пользователь их не ввёл
        if fname[-4:] != '.txt':
            fname = fname + '.txt'
        numpy.savetxt(fname, self.array)

    def openFile(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(self, "Открыть файл", "", ";;".join(ALLOWED_FILE_FORMATS))
        if fname[1] == H5_FILES:
            self.openH5File(fname[0])
        elif fname[1] == TEXT_FILES:
            self.openTextFile(fname[0])

    def openH5File(self, fname):
        with h5py.File(fname, 'r') as hf:
            self.array = hf['array'][:]
        self.loadArrayToTable()

    def openTextFile(self, fname):
        self.array = numpy.loadtxt(fname, dtype=self.array.dtype)
        self.loadArrayToTable()

    def loadArrayToTable(self):
        rowCount = len(self.array[:, 0])
        colCount = len(self.array[0, :]) + 1  # +1 потому что в numpy массиве нет столбца суммы
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(colCount)
        for row in self.array:
            self.insertIntoTableRow(row)
        self.countOfRowsSpinBox.setValue(rowCount)
        self.countOfColsSpinBox.setValue(colCount)

    def drawGraph(self):
        indexes = self.tableWidget.selectionModel().selectedColumns()
        selectedColumns = [i.column() for i in indexes]
        # по условию задания, нужно выделить два столбца и по ним нарисовать график
        # сделал ограничение, чтобы не было возможности рисовать на основе столбца суммы
        if len(selectedColumns) != 2 or 0 in selectedColumns:
            return
        self.plotWidget.clear()
        # получаем массив данных, на основе которых нужно рисовать график,
        plotData = numpy.array([self.array[:, selectedColumns[0]-1], self.array[:, selectedColumns[1]-1]])
        # сортируем эти данные, чтобы график получился более менее приличным
        plotData = plotData[:, plotData[0, :].argsort()]
        self.plotWidget.plot(plotData[0, :], plotData[1, :])


def main():
    app = QtWidgets.QApplication([])
    w = MainWindow()
    w.show()
    exit(app.exec())


if __name__ == "__main__":
    main()
