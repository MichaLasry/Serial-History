from Collected_data import Database
from PyQt5.QtWidgets import QTabWidget, QApplication, QStyledItemDelegate, QLabel, QLineEdit, QSplitter, QTableView, QWidget, QVBoxLayout, QHBoxLayout, QMainWindow, QStyleOptionViewItem
from PyQt5.QtCore import Qt, QModelIndex, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPalette, QStandardItemModel, QStandardItem, QBrush, QIcon
import sys

database_instance = Database()


class ColorDelegate(QStyledItemDelegate):
    def __init__(self, column=None, row=None, parent=None):
        super().__init__(parent)
        self.column = column
        self.row = row

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        # Row-level painting
        if self.row is not None and index.row() == self.row:
            value = index.data()
            background_color = QColor(255, 0, 0)  # Default Red for failed rows

            painter.save()
            painter.fillRect(option.rect, background_color)
            painter.setPen(option.palette.color(QPalette.Text))
            painter.drawText(option.rect, Qt.AlignCenter, value)
            painter.restore()
        # Column-level painting
        elif self.column is not None and index.column() == self.column:
            value = index.data()
            background_color = QColor(0, 255, 0)  # Default Green for "Pass"
            if value != 'Pass':
                background_color = QColor(255, 0, 0)  # Red for anything other than "Pass"
            painter.save()
            painter.fillRect(option.rect, background_color)
            painter.setPen(option.palette.color(QPalette.Text))
            painter.drawText(option.rect, Qt.AlignCenter, value)
            painter.restore()
        else:
            super().paint(painter, option, index)


class WorkerThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, model, data, headers):
        super().__init__()
        self.model = model
        self.data = data
        self.headers = headers

    def run(self):
        for row in range(len(self.data)):
            for col in range(len(self.headers)):
                item = QStandardItem(str(self.data.iloc[row, col]))
                self.model.setItem(row, col, item)
        self.finished.emit("Serial History")
        print("Table Updated")


class MainWindow(QMainWindow):
    def __init__(self, external_input=""):
        super().__init__()
        self.thread = None
        # Set the window title and size
        self.tab_widget = QTabWidget()
        self.database_instance = Database()

        self.serial_tabs = {}  # Dictionary to store serial tabs
        self.main_serial = None  #

        self.setWindowTitle('Serial History')
        self.resize(800, 600)
        # Create a central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.setWindowIcon(QIcon("D:\\HULK\\builds\\Serial History\\serial.ico"))

        self.setGeometry(100, 100, 800, 600)
        # Create the input field and label
        input_label = QLabel("Enter Serial:")
        font = input_label.font()
        font.setPointSize(16)  # Change this value to your desired font size
        font.setFamily('Arial')

        # Apply the font to the QLabel
        input_label.setFont(font)
        self.input_field = QLineEdit()
        self.input_field.setFont(font)
        self.input_field.setFixedHeight(40)
        self.input_field.setText(external_input)
        self.input_field.returnPressed.connect(
            self.handle_enter_pressed)  # Connect returnPressed signal to handle_enter_pressed function

        input_layout = QHBoxLayout()
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_field)
        self.delegate = None


        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

        # Create the main layout and add the input and tables layouts to it
        main_layout = QVBoxLayout()
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.tab_widget)
        # main_layout.addWidget(splitter)

        # Set the main layout as the layout for the central widget
        central_widget.setLayout(main_layout)

    def handle_enter_pressed(self):
        self.serial = self.input_field.text()
        self.create_new_tab()
        # self.create_collected_data_table()

    def create_new_tab(self):
        if self.serial in self.serial_tabs:
            self.tab_widget.setCurrentWidget(self.serial_tabs[self.serial])
        else:
            if not self.main_serial:
                self.main_serial = self.serial
            new_tab = QWidget()
            self.collected_data_table = QTableView()
            self.collected_data_table.setSortingEnabled(True)
            self.collected_data_table.clicked.connect(self.collected_data_row_clicked)
            self.collected_data_model = QStandardItemModel()
            self.collected_data_table.setModel(self.collected_data_model)

            # Create the right table
            self.results_data_table = QTableView()
            self.results_data_table.setSortingEnabled(True)
            self.results_data_model = QStandardItemModel()
            self.results_data_table.setModel(self.results_data_model)

            splitter = QSplitter(Qt.Horizontal)
            splitter.addWidget(self.collected_data_table)
            splitter.addWidget(self.results_data_table)
            splitter.setStretchFactor(1, 1)
            splitter.setStretchFactor(0, 1)  # The first widget takes up 1 part
            splitter.setStretchFactor(1, 1)

            # tab_index = self.tab_widget.addTab(splitter, f"Serial {self.serial}")
            # self.tab_widget.setCurrentIndex(tab_index)
            # Set layout for the new tab
            tab_layout = QVBoxLayout()
            tab_layout.addWidget(splitter)
            new_tab.setLayout(tab_layout)

            # Add the new tab to the tab widget
            self.tab_widget.addTab(new_tab, f"SN: {self.serial}")

            # Populate tables with data
            self.create_collected_data_table()

    def create_collected_data_table(self):
        try:
            self.data, headers = self.database_instance.get_collected_data_rows(self.serial)
            self.column = dict(self.data)['Result_Text']
            headers = list(map(str, headers))
            self.collected_data_model.setHorizontalHeaderLabels(headers)
            self.collected_data_model.setColumnCount(len(headers))
            self.collected_data_model.setRowCount(len(self.data))
            self.start_task(self.collected_data_model, self.data, headers)
            self.collected_data_table.setModel(self.collected_data_model)
            self.collected_data_table.setSelectionBehavior(QTableView.SelectRows)
            self.collected_data_table.setAlternatingRowColors(True)
            self.paint_result_col_collectedTable()
        except KeyError as e:
            print(f"Key error: {e}")
        except ValueError as e:
            print(f"Value error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def close_tab(self, index):
        self.tab_widget.removeTab(index)
        serial_to_remove = None
        for serial, widget in self.serial_tabs.items():
            if widget == self.tab_widget:
                serial_to_remove = serial
                break

        if serial_to_remove:
            # Remove tab and update serial_tabs dictionary
            self.tab_widget.removeTab(index)
            del self.serial_tabs[serial_to_remove]

            # If the closed tab was the main serial, set a new main serial
            if self.main_serial == serial_to_remove:
                if self.serial_tabs:
                    # Set new main serial to the first available serial
                    self.set_main_serial(next(iter(self.serial_tabs)))
                else:
                    self.main_serial = None

        print(f"Main serial is now: {self.main_serial}")

    def set_main_serial(self, serial):
        # Set the provided serial as the main serial and print the update
        self.main_serial = serial
        print(f"Main serial set to: {self.main_serial}")

    def get_column_number(self):
        if self.collected_data_model is not None:
            column_count = self.collected_data_model.columnCount()
            column = -1
            for col in range(column_count):
                header_data = self.collected_data_model.headerData(col, Qt.Horizontal)
                if header_data == 'Result_Text':
                    column = col
                    break
            if column != -1:
                # Corrected line
                self.delegate = ColorDelegate(column, self.collected_data_table)
                self.collected_data_table.setItemDelegateForColumn(column, self.delegate)
            return column
        return None

    # In your MainWindow class
    def paint_result_col_collectedTable(self):
        self.column = self.get_column_number()
        if self.column is not None:
            self.delegate = ColorDelegate(self.column, self.collected_data_table)
            self.collected_data_table.setItemDelegateForColumn(self.column, self.delegate)

    def collected_data_row_clicked(self, index: QModelIndex):
        try:
            self.selected_row = index.row()
            self.create_results_data_table()
        except Exception as e:
            print(f"Error occurred while processing row click: {e}")

    def create_results_data_table(self):
        try:
            self.resetDelegate()
            id_row = dict(self.data)['ID'][self.selected_row]
            print(id_row)
            self.row_data, headers = self.database_instance.get_data_per_row(id_row)
            #
            # print(dict(self.data)['Result_Text'][self.selected_row])
            headers = list(map(str, headers))
            if 'Rank' in headers:
                rank_index = headers.index('Rank')
                headers.pop(rank_index)
                self.data = self.data.drop(columns=['Rank'])
            self.results_data_model.setHorizontalHeaderLabels(headers)
            self.results_data_model.setColumnCount(len(headers))
            self.results_data_model.setRowCount(len(self.row_data))
            self.start_task(self.results_data_model, self.row_data, headers)

            self.results_data_table.setModel(self.results_data_model)
            self.results_data_table.setSelectionBehavior(QTableView.SelectRows)
            self.results_data_table.setAlternatingRowColors(True)
            if dict(self.data)['Result_Text'][self.selected_row] != "Pass":
                self.paint_specific_row()
        except KeyError as e:
            print(f"Key error: {e}")
        except ValueError as e:
            print(f"Value error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def paint_specific_row(self):
        # List of Test Names (assuming this is the row identifier in the right table)
        row_list = list(dict(self.row_data)['Test_Name'])
        # Retrieve the column for "Result_Text" from the original data
        for i, result in enumerate(row_list):
            if self.data["Result_Text"][self.selected_row] == result:
                delegate = ColorDelegate(row=i, parent=self.results_data_table)
                self.results_data_table.setItemDelegateForRow(i, delegate)

    def resetDelegate(self):
        # Reset the delegate to the default delegate (None) for all rows
        if isinstance(self.results_data_table, QTableView):
            for row in range(self.results_data_model.rowCount()):
                self.results_data_table.setItemDelegateForRow(row, None)

    def removeRowDelegate(self, row):
        for column in range(self.results_data_model.columnCount()):
            index = self.results_data_model.item(row, column)
            self.results_data_table.closePersistentEditor(index)
            self.results_data_table.setIndexWidget(index, None)
            self.results_data_table.setData(index, QBrush(Qt.NoBrush), Qt.BackgroundRole)
        self.results_data_table.clearSelection()

    # Thread  Function
    def start_task(self, model, data, headers):
        self.thread = WorkerThread(model, data, headers)
        self.thread.finished.connect(self.update_progress)
        self.thread.start()
        self.setWindowTitle('Loading...')

    # Thread  Function
    def update_progress(self, results):
        self.setWindowTitle(results)

    def closeEvent(self, event):
        database_instance.close_connection()
        print("Window closed")
        event.accept()


if __name__ == '__main__':
    try:
        app = QApplication([])
        app.setStyle('Fusion')
        external_input = ""
        if len(sys.argv) > 1:
            external_input = sys.argv[1]
        window = MainWindow(external_input)
        window.handle_enter_pressed()
        window.show()

        app.exec_()
    except Exception as e:
        print("Error in main loop:", e)

