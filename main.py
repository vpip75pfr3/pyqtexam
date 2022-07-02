import os
import re
import subprocess
from PySide2 import QtWidgets, QtCore
from finder import Ui_Finder


class QFinder(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_Finder()
        self.ui.setupUi(self)

        self.walk_filesThread = None
        self.path_to_open = None

        self.initThreads()
        self.initSignals()

    def initThreads(self):
        self.walk_filesThread = FindFilesThread()

    def initSignals(self):
        # widgets
        self.ui.file_review.clicked.connect(self.getDirectory)
        self.ui.find.clicked.connect(self.find_files)
        self.ui.checkBox_file_size.clicked.connect(self.file_size_filter)
        self.walk_filesThread.PathesSignal.connect(self.show_all_files_Signal)
        self.ui.open_path_file.clicked.connect(self.open_directory)

    def find_files(self):
        if self.ui.lineEdit_path.text():
            self.walk_filesThread.start_folder = self.ui.lineEdit_path.text()
            self.walk_filesThread.max_size = self.get_max_size()
            self.walk_filesThread.pattern = self.ui.lineEdit_pattern.text()
            self.walk_filesThread.pattern_type = self.ui.comboBox_filter.currentText()
            self.walk_filesThread.start()

    def open_directory(self):
        if self.ui.listWidget_pathes.selectedItems():
            for obj_path in self.ui.listWidget_pathes.selectedItems():
                path_to_open = os.path.dirname(obj_path.text())
                subprocess.Popen(f'explorer "{path_to_open}"')

    def get_max_size(self):
        try:
            return int(self.ui.lineEdit_file_size_filter.text())
        except ValueError:
            return 0

    def clear_list_widget(self):
        """ Удаляем предыдущий ответ на запрос """
        for el in reversed(range(self.ui.listWidget_pathes.count())):
            self.ui.listWidget_pathes.takeItem(el)

    def show_all_files_Signal(self, emit):
        self.clear_list_widget()
        for _path in emit:
            item = QtWidgets.QListWidgetItem(_path)
            self.ui.listWidget_pathes.addItem(item)

    def file_size_filter(self):
        self.ui.lineEdit_file_size_filter.setReadOnly(not(self.ui.checkBox_file_size.isChecked()))
        color = "white" if self.ui.checkBox_file_size.isChecked() else "gray"
        self.ui.lineEdit_file_size_filter.setStyleSheet(f"background-color: {color};")

    def getDirectory(self):
        self.ui.lineEdit_path.setText( QtWidgets.QFileDialog.getExistingDirectory(self, "Выбрать папку", "."))


class FindFilesThread(QtCore.QThread):
    PathesSignal = QtCore.Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_folder = None
        self.max_size = 0
        self.pattern = ""
        self.pattern_type = None

    def run(self):
        pattern = self.get_pattern()
        path_list = []
        for root, dirs, files in os.walk(os.path.normpath(self.start_folder)):
            for file in files:
                file_path = os.path.normpath(os.path.join(root, file))
                # Проверяем что подходит по размеру
                if not self.max_size or (os.path.getsize(file_path) <= self.max_size):
                    # Проверяем что подходит по паттерну
                    if self.pattern_type == 'Строки':
                        if pattern.search(file):
                            path_list.append(file_path)
                    elif self.pattern_type == 'Бинарный':
                        with open(file_path, 'rb') as f:
                            if pattern.search(f.read()):
                                path_list.append(file_path)
        self.PathesSignal.emit(path_list)

    def get_pattern(self):
        if self.pattern_type == 'Строки':
            pattern = re.compile(self.pattern)
        elif self.pattern_type == 'Бинарный':
            pattern = re.compile(self.pattern.encode("UTF-8"))
        else:
            pattern = ""
        return pattern


if __name__ == '__main__':
    app = QtWidgets.QApplication()

    myapp = QFinder()
    myapp.show()

    app.exec_()
