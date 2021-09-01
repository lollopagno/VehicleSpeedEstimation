from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout
from PyQt5.Qt import Qt

from MotionTracking.Utility import log

COLUMN_VEHICLE = "Vehicle"
COLUMN_VELOCITY = "Velocity"
COLUMN_COLOR = "Color"
COLUMN_STATIONARY = "Stationary"
COLUMN_DIRECTION = "Direction"


def get_column_index(name_column):
    """
    Get index column by name.

    :param name_column: column name.
    """
    if name_column == COLUMN_VEHICLE:
        index = 0

    elif name_column == COLUMN_VELOCITY:
        index = 1

    elif name_column == COLUMN_STATIONARY:
        index = 2

    elif name_column == COLUMN_DIRECTION:
        index = 3

    else:
        index = 4

    return index


class Table(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'Vehicle list'
        self.left = 0
        self.top = 0
        self.width = 550
        self.height = 300

        self.layout = QVBoxLayout()
        self.table = QTableWidget()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            [COLUMN_VEHICLE, COLUMN_VELOCITY, COLUMN_STATIONARY, COLUMN_DIRECTION, COLUMN_COLOR])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Table in read-only

        self.show()

    def close(self):
        """
        Close the window.
        """

        try:
            self.table.close()
            self.destroy()
        except:
            pass

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

                item_name = QTableWidgetItem(item.name)
                item_name.setTextAlignment(Qt.AlignHCenter)

                item_velocity = QTableWidgetItem(f"{round(item.velocity, 3)} km/h")
                item_velocity.setTextAlignment(Qt.AlignHCenter)

                item_stat = QTableWidgetItem(str(item.is_stationary))
                item_stat.setTextAlignment(Qt.AlignHCenter)

                item_direction = QTableWidgetItem(item.get_direction())
                item_direction.setTextAlignment(Qt.AlignHCenter)

                self.table.insertRow(current_row)
                self.table.setItem(current_row, 0, item_name)
                self.table.setItem(current_row, 1, QTableWidgetItem(item_velocity))
                self.table.setItem(current_row, 2, QTableWidgetItem(item_stat))
                self.table.setItem(current_row, 3, QTableWidgetItem(item_direction))
                self.table.setItem(current_row, 4, item_color)

                self.table.update()

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

    def update_table(self, name_vehicle, name_column, data):
        r"""
        Update information of the vehicles into table.

        :param name_vehicle: vehicle name.
        :param name_column: column to be updated.
        :param data: data to be updated.
        """

        columns = self.table.columnCount()
        rows = self.table.rowCount()

        for column in range(columns):
            column_text = self.table.horizontalHeaderItem(column).text()

            if column_text == COLUMN_VEHICLE:

                for row in range(rows):
                    cell = self.table.item(row, column).text()

                    if cell == name_vehicle:
                        index = get_column_index(name_column)

                        item_cell = QTableWidgetItem(str(data))
                        item_cell.setTextAlignment(Qt.AlignHCenter)

                        log(2, f"Update {name_column} [{data}] of row: {name_vehicle}")
                        self.table.setItem(row, index, item_cell)
                        break
        self.update()
