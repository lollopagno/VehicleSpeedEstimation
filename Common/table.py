from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout

from Common.utility import log

COLUMN_VEHICLE = "Vehicle"
COLUMN_VELOCITY = "Velocity"
COLUMN_COLOR = "Color"


class Table(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'Vehicle list'
        self.left = 0
        self.top = 0
        self.width = 400
        self.height = 300

        self.layout = QVBoxLayout()
        self.table = QTableWidget()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([COLUMN_VEHICLE, COLUMN_VELOCITY, COLUMN_COLOR])

        # Show widget
        self.show()

    def update_table(self, name_vehicle, velocity):
        log(2, "Update row")

        columns = self.table.columnCount()
        rows = self.table.rowCount()

        for column in range(columns):
            column_text = self.table.horizontalHeaderItem(column).text()

            if column_text == COLUMN_VELOCITY:

                for row in range(rows):
                    cell = self.table.item(row, column).text()

                    if cell == name_vehicle:
                        # TODO Update the velocity
                        # self.table.setItem(row, column, QTableWidgetItem(velocity))
                        pass

    def delete_row(self, name_vehicle):
        log(2, f"Delete row of {name_vehicle}")

        columns = self.table.columnCount()
        rows = self.table.rowCount()

        for column in range(columns):
            column_text = self.table.horizontalHeaderItem(column).text()

            if column_text == COLUMN_VEHICLE:

                for row in range(rows):
                    try:
                        cell = self.table.item(row, column).text()

                        if cell == name_vehicle:
                            self.table.removeRow(row)
                            self.update()
                            break
                    except Exception as e:
                        log(1, f"Error in DELETE ROW TABLE: {e}")

    def add_row(self, item):
        name, _, color, velocity = item
        color_qt = QColor.fromRgb(color[2], color[1], color[0])
        log(2, f"Add row: {name}, {velocity}, {color}")

        current_row = self.table.rowCount()
        item_color = QTableWidgetItem()
        item_color.setBackground(color_qt)

        self.table.insertRow(current_row)
        self.table.setItem(current_row, 0, QTableWidgetItem(name))
        self.table.setItem(current_row, 1, QTableWidgetItem(f"{velocity} km/h"))
        self.table.setItem(current_row, 2, item_color)
        self.table.update()

    @pyqtSlot()
    def on_click(self):
        for currentQTableWidgetItem in self.table.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())