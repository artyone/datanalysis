from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QMainWindow, QSplitter, QPlainTextEdit,
    QAction, QFileDialog
)
from app.model import file_methods
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt
from app.view.servicesWindows.graphWindow import GraphWindow
from pprint import pprint
import copy
import app.resource.qrc_resources
import contextlib
import traceback
import pandas
import numpy
import math
import sys
import io


class ConsoleWindow(QMainWindow):
    '''
    Класс для окна консоли.
    controller - контроллер.
    filepath - путь к файлу скрипта, если он требуется.
    parent - окно родителя.
    '''

    def __init__(self, controller, parent) -> None:
        super().__init__()
        self.controller = controller
        self.parent = parent
        self.filepath = None
        self.initUI()

    def initUI(self) -> None:
        '''
        Метод инициализации интерфейса окна.
        '''
        self.setGeometry(0, 0, 900, 800)
        self.setWindowTitle("Python console")
        self.createAction()
        self.createMenu()
        self.connectActions()

        splitter = QSplitter(Qt.Vertical) # type: ignore

        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(11)

        # self.textEdit = SimplePythonEditor(font)
        self.textEdit = QPlainTextEdit()
        self.textEdit.setFont(font)
        self.label = QPlainTextEdit()
        self.label.setFont(font)

        self.setCentralWidget(splitter)
        splitter.addWidget(self.textEdit)
        splitter.addWidget(self.label)
        self.textEdit.setPlainText(
            '# Все данные хранятся в переменной "data" print(data).\n' +
            '# Тип данных словарь с Dataframe из библиотеки pandas\n' +
            '# Для постройки графика используется синтаксис graph(data["PNK"]["ADR8"], "JVD_VN", "JVD_H")\n' +
            '# Можно использовать numpy, math, pandas\n' +
            '# Для выгрузки данных используем код to_csv(data["PNK"]["ADR8"], "123.csv")\n' +
            '# Для добавления в основные данные столбца используем метод: setNewData\n' +
            '# setNewData(category: str, adr: str, columnName: str, timeData: list, columnData: list)\n'
        )

    def createMenu(self) -> None:
        fileToolBar = self.addToolBar('File')
        fileToolBar.addAction(self.openScriptAction)
        fileToolBar.addAction(self.saveScriptAction)
        fileToolBar.addAction(self.executeAction)

    def createAction(self) -> None:
        self.openScriptAction = QAction('&Открыть *.py...')
        self.openScriptAction.setIcon(
            QIcon(self.parent.getIcon(':file-text.svg')))
        self.saveScriptAction = QAction('&Сохранить *.py...')
        self.saveScriptAction.setIcon(QIcon(self.parent.getIcon(':save.svg')))
        self.executeAction = QAction('&Выполнить скрипт.')
        self.executeAction.setIcon(self.parent.getIcon((':play.svg')))
        self.executeAction.setShortcut("Ctrl+Return")

    def connectActions(self) -> None:
        self.openScriptAction.triggered.connect(self.openScript)
        self.saveScriptAction.triggered.connect(self.saveScript)
        self.executeAction.triggered.connect(self.execute)

    def execute(self) -> None:
        '''
        Метод выполнения команды и установки результата в label.
        Если filepath есть, то рядом будет сохранен бэкап файл.
        Используется перехват вывода в консоль.
        data - копия данных, чтобы не изменять настоящие данные.
        graph - метод для построения графика.
        to_csv(dataframe, filepath) - метод для сохранения датафрейма в файл
        '''
        self.autoSave()
        self.f = io.StringIO()
        with contextlib.redirect_stdout(self.f), contextlib.redirect_stderr(self.f):
            try:
                command = self.textEdit.toPlainText()
                model = file_methods()
                to_csv = model.write_csv
                data = copy.deepcopy(self.controller.get_data())
                graph = self.graph
                setNewData = self.setNewData
                exec(command)
            except:
                print(traceback.format_exc(), file=sys.stderr)
        output = self.f.getvalue()
        self.label.setPlainText(output)

    def openScript(self) -> None:
        '''
        Метод загрузки ранее сохраненного скрипта.
        '''
        filepath, check = QFileDialog.getOpenFileName(
            None,
            'Open python file',
            '',
            'Open File (*.py)'
        )
        if check:
            try:
                scriptData = self.controller.load_pytnon_script(
                    filepath)
                self.textEdit.setPlainText(scriptData)
                self.parent.setNotify('успех', 'Скрипт загружен')
                self.filepath = filepath
            except Exception as e:
                self.parent.setNotify('ошибка', str(e))

    def saveScript(self) -> None:
        '''
        Метод сохранения скрипта.
        '''
        options = QFileDialog.Options()
        self.filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            f"python Files (*.py);;All Files(*)",
            options=options
        )
        data = self.textEdit.toPlainText()
        if self.filepath:
            try:
                self.controller.save_python_sript(self.filepath, data)
                self.parent.setNotify(
                    'успех', f'Python файл сохранен в {self.filepath}')
            except PermissionError:
                self.parent.setNotify(
                    'ошибка', 'Файл открыт в другой программе')
            except Exception as e:
                self.parent.setNotify('ошибка', str(e))

    def autoSave(self) -> None:
        '''
        Метод автосхоранения, если был открыт или сохранен какой-либо скрипт.
        '''
        data = self.textEdit.toPlainText()
        if self.filepath:
            try:
                self.controller.save_python_sript(
                    self.filepath + '.bck', data)
            except PermissionError:
                self.parent.setNotify(
                    'ошибка', 'Автосейв не выполнен')
            except Exception as e:
                self.parent.setNotify('ошибка', str(e))

    def graph(self, data: pandas.DataFrame, *args) -> None:
        '''
        Вспомогательный Метод для создания графика из консоли.
        '''
        dataForGraph = {'console': {'ADR0': data}}
        treeSelected = [('console', 'ADR0', arg) for arg in args]

        try:
            graphWindow = GraphWindow(
                dataForGraph, treeSelected, 1, self.parent)
            self.parent.mdi.addSubWindow(graphWindow)
            graphWindow.show()
            self.parent.trackGraph()
            self.parent.checkPositioningWindows()
        except AttributeError as e:
            self.f.write(f'Данные для графика не являются dataframe\n{str(e)}')
            self.parent.setNotify(
                'предупреждение',
                'Данные для графика не являются dataframe'
            )
        except KeyError as e:
            self.f.write(
                f'Необходимо правильно выбрать данные для графика или ошибка имен элементов\n{str(e)}')
            self.parent.setNotify(
                'предупреждение',
                'Необходимо правильно выбрать данные для графика или ошибка имен элементов'
            )

    def setNewData(
            self, 
            category: str, 
            adr: str, 
            columnName: str,
            timeData: list, 
            columnData: list
    ) -> None:
        
        mainData = self.controller.get_data()
        
        if category not in mainData:
            newData = pandas.DataFrame({'time': timeData, columnName: columnData})
            mainData[category] = {adr: newData}
        elif adr not in mainData[category]:
            newData = pandas.DataFrame({'time': timeData, columnName: columnData})
            mainData[category][adr] = newData
        else:
            df: pandas.DataFrame = mainData[category][adr]
            while True:
                if columnName not in df.columns:
                    break
                columnName += '1'
            newData = pandas.DataFrame({'time': timeData, columnName: columnData})
            newData['time'] = newData['time'].astype(df.dtypes['time'])
            df = df.merge(newData, on='time', how='outer')
            self.controller.get_data()[category][adr] = df


        
        self.parent.tree_widget.update_check_box()
        print(f'Столбец: {columnName} успешно добавлен в: {category}/{adr}')
        

            
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape: # type: ignore
            self.hide()
        else:
            super().keyPressEvent(event)