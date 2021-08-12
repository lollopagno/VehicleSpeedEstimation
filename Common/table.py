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
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Table in read-only

        self.show()

    def update_table(self, name_vehicle, velocity):
        r"""
        Update velocity of the vehicles into table.

        :param name_vehicle: vehicle name.
        :param velocity: velocity to be updated.
        """

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
        r"""
        Delete row in the table.

        :param name_vehicle: name of the vehicle to be deleted.
        """

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

    def add_rows(self, rows):
        r"""
        Added rows in the table.

        :param rows: rows to add.
        """

        for item in rows:
            if not self.check_cell(COLUMN_VEHICLE, item.name):
                color = item.color
                color_qt = QColor.fromRgb(color[2], color[1], color[0])
                log(2, f"Add row: {item.name}, {item.velocity}, {color}")

                current_row = self.table.rowCount()
                item_color = QTableWidgetItem()
                item_color.setBackground(color_qt)

                self.table.insertRow(current_row)
                self.table.setItem(current_row, 0, QTableWidgetItem(item.name))
                self.table.setItem(current_row, 1, QTableWidgetItem(f"{item.velocity} km/h"))
                self.table.setItem(current_row, 2, item_color)
                self.table.update()

    def check_cell(self, name_column, name_cell):
        r"""
        Check if name of the cell is present in the table.

        :param name_column: column name.
        :param name_cell: text to search into cell of the table.

        :return: True if text is present, false otherwise.
        """

        columns = self.table.columnCount()
        rows = self.table.rowCount()

        is_present = False

        for column in range(columns):
            column_text = self.table.horizontalHeaderItem(column).text()

            if column_text == name_column:

                for row in range(rows):
                    try:
                        cell = self.table.item(row, column).text()

                        if cell == name_cell:
                            is_present = True
                            break
                    except Exception as e:
                        log(1, f"Error in CHECK CELL: {e}")

        return is_present
