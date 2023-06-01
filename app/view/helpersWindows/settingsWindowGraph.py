from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFormLayout, QScrollArea, QComboBox, QFrame
)


class ValueErrorGraph(Exception):
    pass


class FieldWidget(QWidget):
    def __init__(self, field):
        super().__init__()
        self.category_edit = QLineEdit(field['category'])
        self.adr_edit = QLineEdit(field['adr'])
        self.column_edit = QLineEdit(field['column'])

        layout = QHBoxLayout()

        delete_btn = QPushButton('-')
        delete_btn.setFixedWidth(20)
        delete_btn.clicked.connect(self.deleteLater)

        layout.addWidget(delete_btn)
        layout.addWidget(QLabel("Category: "))
        layout.addWidget(self.category_edit)
        layout.addWidget(QLabel("Adr: "))
        layout.addWidget(self.adr_edit)
        layout.addWidget(QLabel("Column: "))
        layout.addWidget(self.column_edit)

        self.setLayout(layout)

    def get_field(self) -> dict:
        category = self.category_edit.text()
        adr = self.adr_edit.text()
        column = self.column_edit.text()
        if not (category and adr and column):
            raise ValueErrorGraph(
                'Заполнены не все поля на вкладке настройки графиков'
            )
        try:
            field = {
                'category': category,
                'adr': adr,
                'column': column
            }
        except RuntimeError:
            field = None
        finally:
            return field


class RowWidget(QWidget):
    def __init__(self, row) -> None:
        super().__init__()
        self.field_widgets = []

        for field in row['fields']:
            field_widget = FieldWidget(field)
            self.field_widgets.append(field_widget)

        self.layout = QFormLayout()

        self.rowWidget = QWidget()
        rowLayout = QHBoxLayout()

        rowDeleteBtn = QPushButton('-')
        rowDeleteBtn.clicked.connect(self.deleteLater)
        rowDeleteBtn.setFixedWidth(20)

        rowLabel = QLabel('Ряд: ')
        widthLabel = QLabel('Высота %: ')
        self.rowEdit = QLineEdit(f'{row["row"]}')
        self.widthEdit = QLineEdit(f'{row["width"]}')

        rowLayout.addWidget(rowDeleteBtn)
        rowLayout.addWidget(rowLabel)
        rowLayout.addWidget(self.rowEdit)
        rowLayout.addWidget(widthLabel)
        rowLayout.addWidget(self.widthEdit)
        self.rowWidget.setLayout(rowLayout)

        self.layout.addRow(self.rowWidget)
        for field_widget in self.field_widgets:
            self.layout.addRow(field_widget)

        self.add_field_btn = QPushButton('+ элемент графика')
        self.add_field_btn.clicked.connect(self.add_field)
        self.layout.addRow(self.add_field_btn)

        self.setLayout(self.layout)

    def add_field(self) -> None:
        self.layout.removeWidget(self.add_field_btn)
        field = {'category': '', 'adr': '', 'column': ''}
        field_widget = FieldWidget(field)
        self.field_widgets.append(field_widget)
        self.layout.addRow(field_widget)
        self.layout.addRow(self.add_field_btn)

    def get_row(self) -> dict:
        if self.rowEdit.text() == '' or self.widthEdit.text() == '':
            raise ValueErrorGraph(
                'Не заполнено поле row или width на вкладке настройки графиков'
            )
        try:
            row = {
                'row': int(self.rowEdit.text()),
                'width': int(self.widthEdit.text()),
                'fields': [
                    field_widget.get_field()
                    for field_widget in self.field_widgets
                    if field_widget.get_field()]
            }
            return row
        except RuntimeError:
            return None


class CategoryGraphWidget(QWidget):
    def __init__(self, name, rows) -> None:
        super().__init__()
        self.rowWidgets = []

        for row in rows:
            rowWidget = RowWidget(row)
            self.rowWidgets.append(rowWidget)

        self.layout = QVBoxLayout()

        self.categoryWidget = QWidget()
        categoryLayout = QHBoxLayout()
        categoryDeleteBtn = QPushButton('-')
        categoryDeleteBtn.clicked.connect(self.deleteLater)
        categoryDeleteBtn.setFixedWidth(20)
        categoryLabel = QLabel('Название категории графиков: ')
        self.categoryEdit = QLineEdit(name)
        categoryLayout.addWidget(categoryDeleteBtn)
        categoryLayout.addWidget(categoryLabel)
        categoryLayout.addWidget(self.categoryEdit)
        self.categoryWidget.setLayout(categoryLayout)
        self.layout.addWidget(self.categoryWidget)

        for rowWidget in self.rowWidgets:
            self.layout.addWidget(rowWidget)

        self.addRowBtn = QPushButton('+ ряд')
        self.addRowBtn.clicked.connect(self.addRow)

        self.layout.addWidget(self.addRowBtn)

        lineWidget = QFrame()
        lineWidget.setFrameShape(QFrame.HLine)
        lineWidget.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(lineWidget)
        self.setLayout(self.layout)

    def addRow(self) -> None:
        self.layout.removeWidget(self.addRowBtn)
        row = {
            'row': '', 'width': '', 'fields': []
        }
        row_widget = RowWidget(row)
        row_widget.add_field()
        self.rowWidgets.append(row_widget)
        self.layout.addWidget(row_widget)
        self.layout.addWidget(self.addRowBtn)

    def getCategory(self) -> dict:
        if self.categoryEdit.text() == '':
            raise ValueErrorGraph(
                'Не заполнена категория на вкладке настройки графиков'
            )
        try:
            analysisResult = {
                'name': self.categoryEdit.text(),
                'rows': [
                    row_widget.get_row()
                    for row_widget in self.rowWidgets
                    if row_widget.get_row()]
            }
            return analysisResult
        except RuntimeError:
            return None


class GraphTab(QWidget):
    def __init__(self, data) -> None:
        super().__init__()
        background = data['background']
        self.data = data['default']
        self.widgets = [CategoryGraphWidget(
            elem['name'], elem['rows']) for elem in self.data]

        scrollArea = QScrollArea()
        scrollWidget = QWidget()
        self.scrollLayout = QFormLayout(scrollWidget)

        self.backgroundCombo = QComboBox()
        self.backgroundCombo.addItems(
            ['black', 'white', 'red', 'green', 'pink', 'blue', 'gray']
        )
        self.backgroundCombo.setCurrentText(background)

        for widget in self.widgets:
            self.scrollLayout.addRow(widget)

        self.add_analysis_btn = QPushButton('+ категорию графиков')
        self.add_analysis_btn.clicked.connect(self.add_analysis)
        self.scrollLayout.addRow(self.add_analysis_btn)

        scrollArea.setWidget(scrollWidget)
        scrollArea.setWidgetResizable(True)

        mainLayout = QFormLayout()
        mainLayout.addRow(QLabel('Цвет фона: '), self.backgroundCombo)
        mainLayout.addRow(QLabel('Графики по умолчанию'), scrollArea)

        self.setLayout(mainLayout)

    def add_analysis(self) -> None:
        self.scrollLayout.removeWidget(self.add_analysis_btn)
        analysis_widget = CategoryGraphWidget('', [])
        analysis_widget.addRow()
        self.widgets.append(analysis_widget)
        self.scrollLayout.addRow(analysis_widget)
        self.scrollLayout.addRow(self.add_analysis_btn)

    def get_data(self) -> list:
        if self.backgroundCombo.currentText() == '':
            raise ValueErrorGraph(
                'Заполнены не все поля на вкладке настройки графиков'
            )
        result = {
            'background': self.backgroundCombo.currentText(),
            'default': [category.getCategory() for category in self.widgets if category.getCategory()]
        }
        return result


if __name__ == '__main__':
    import sys
    data = {
        'background': 'black',
        'default': [
            {
                "name": "Анализ Частот",
                "rows": [
                    {
                        "row": 1,
                        "width": 50,
                        "fields": [
                            {
                                "category": "DIS D001",
                                "adr": "ADR1",
                                "column": "Fd1",
                            },
                        ]
                    },
                    {
                        "row": 2,
                        "width": 50,
                        "fields": [
                            {
                                "category": "DIS D001",
                                "adr": "ADR1",
                                "column": "Fd2",
                            }
                        ]
                    }
                ],
            }
        ]
    }
    app = QApplication(sys.argv)
    window = GraphTab(data)
    window.show()
    print(window.get_data())
    sys.exit(app.exec_())
