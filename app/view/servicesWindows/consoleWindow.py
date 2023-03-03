from PyQt5.QtGui import QFont, QIcon, QColor, QFontMetrics
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5 import QtWidgets as qtw
from app.model.file import Datas
from PyQt5.QtCore import Qt
import app.resource.qrc_resources
import contextlib
import traceback
import pandas
import numpy
import math
import sys
import io


class SimplePythonEditor(QsciScintilla):
    '''
    Класс для украшения окна консоли.
    '''
    def __init__(self, font, parent=None):
        super(SimplePythonEditor, self).__init__(parent)
        self.setFont(font)
        self.setMarginsFont(font)
        # Margin 0 is used for line numbers
        fontmetrics = QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.width("00000") + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#cccccc"))
        # Brace matching: enable for a brace immediately before or after
        # the current position
        #
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        # Current line visible with special background color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#ffe4e4"))
        # Set Python lexer
        # Set style for Python comments (style number 1) to a fixed-width
        # courier.
        lexer = QsciLexerPython()
        lexer.setDefaultFont(font)
        self.setLexer(lexer)
        text = bytearray(str.encode("Arial"))
        self.SendScintilla(QsciScintilla.SCI_STYLESETFONT, 1, text)
        # Don't want to see the horizontal scrollbar at all
        # Use raw message to Scintilla here (all messages are documented
        # here: http://www.scintilla.org/ScintillaDoc.html)
        self.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 0)
        # not too small
        # self.setMinimumSize(200, 200)


class ConsoleWindow(qtw.QMainWindow):
    '''
    Класс для окна консоли.
    controller - контроллер.
    filepath - путь к файлу скрипта, если он требуется.
    parent - окно родителя.
    '''
    def __init__(self, controller, parent):
        super().__init__()
        self.controller = controller
        self.parent = parent
        self.filepath = None
        self.initUI()
        #TODO решить проблему с темной темой

    def initUI(self):
        '''
        Метод инициализации интерфейса окна.
        '''
        self.setGeometry(0, 0, 600, 600)
        self.setWindowTitle("Python console")
        self.createAction()
        self.createMenu()
        self.connectActions()

        splitter = qtw.QSplitter(Qt.Vertical)

        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(11)
        self.textEdit = SimplePythonEditor(font)
        self.label = qtw.QPlainTextEdit()
        self.label.setFont(font)

        self.setCentralWidget(splitter)
        splitter.addWidget(self.textEdit)
        splitter.addWidget(self.label)
        self.textEdit.setText(
            '# Все данные хранятся в переменной "data".\n# Тип данных Dataframe из библиотеки pandas\n# Для постройки графика используется синтаксис graph(data, "JVD_H", "JVD_Vn")\n# Можно использовать numpy, math, pandas')

    def createMenu(self):
        fileToolBar = self.addToolBar('File')
        fileToolBar.addAction(self.openScriptAction)
        fileToolBar.addAction(self.saveScriptAction)
        fileToolBar.addAction(self.executeAction)

    def createAction(self):
        self.openScriptAction = qtw.QAction('&Open *.py...')
        self.openScriptAction.setIcon(QIcon(':file-text.svg'))
        self.saveScriptAction = qtw.QAction('&Save *.py...')
        self.saveScriptAction.setIcon(QIcon(':save.svg'))
        self.executeAction = qtw.QAction('&Execute script')
        self.executeAction.setIcon(QIcon(':play.svg'))
        self.executeAction.setShortcut("Ctrl+Return")

    def connectActions(self):
        self.openScriptAction.triggered.connect(self.openScript)
        self.saveScriptAction.triggered.connect(self.saveScript)
        self.executeAction.triggered.connect(self.execute)

    def execute(self):
        '''
        Метод выполнения команды и установки результата в label.
        Если filepath есть, то рядом будет сохранен бэкап файл.
        Используется перехват вывода в консоль.
        data - копия данных, чтобы не изменять настоящие данные.
        graph - метод для построения графика.
        to_csv(dataframe, filepath) - метод для сохранения датафрейма в файл
        '''
        self.autoSave()
        f = io.StringIO()
        with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            try:
                model = Datas()
                to_csv = model.write_csv
                data = self.controller.get_data().copy()
                graph = self.parent.createGraphForConsole
                command = self.textEdit.text()
                exec(command)
            except:
                print(traceback.format_exc(), file=sys.stderr)
        output = f.getvalue()
        self.label.setPlainText(output)

    def openScript(self):
        '''
        Метод загрузки ранее сохраненного скрипта.
        '''
        self.filepath, check = qtw.QFileDialog.getOpenFileName(None,
                                                                 'Open python file', '', 'Open File (*.py)')
        if check:
            try:
                scriptData = self.controller.load_pytnon_script(
                    self.filepath)
                self.textEdit.setText(scriptData)
                self.parent.setNotify('success', 'script file loaded')
            except Exception as e:
                self.parent.setNotify('error', str(e))

    def saveScript(self):
        '''
        Метод сохранения скрипта.
        '''
        options = qtw.QFileDialog.Options()
        self.filepath, _ = qtw.QFileDialog.getSaveFileName(self,
                                                      "Save File", "", f"python Files (*.py);;All Files(*)",
                                                      options=options)
        data = self.textEdit.text()
        if self.filepath:
            try:
                self.controller.save_python_sript(self.filepath, data)
                self.parent.setNotify(
                    'success', f'python file saved to {self.filepath}')
            except PermissionError:
                self.parent.setNotify(
                    'error', 'File opened in another program')
            except Exception as e:
                self.parent.setNotify('error', str(e))

    def autoSave(self):
        '''
        Метод автосхоранения, если был открыт или сохранен какой-либо скрипт.
        '''
        data = self.textEdit.text()
        if self.filepath:
            try:
                self.controller.save_python_sript(
                    self.filepath + '.bck', data)
            except PermissionError:
                self.parent.setNotify(
                    'error', 'File opened in another program')
            except Exception as e:
                self.parent.setNotify('error', str(e))