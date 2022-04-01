import sys
from PySide6 import QtWidgets
from PySide6.QtCore import Qt

# https://doc.qt.io/qtforpython/overviews/qtwidgets-widgets-windowflags-example.html
# from PySide6.QtCore import Qt
# self.setWindowFlag(Qt.WindowContextHelpButtonHint, True)

class InitBlogForm:
    @classmethod
    def form(cls) -> QtWidgets.QDialog:
        form = QtWidgets.QDialog()
        form.setWindowTitle("boke init")
        form.setStyleSheet("""
        QWidget {
            font-size: 18px;
            margin: 5px 0 5px 0;
        }
        QPushButton {
            font-size: 14px;
            padding: 5px 10px 5px 10px;
        }
        """)

        vbox = QtWidgets.QVBoxLayout(form)

        vbox.addWidget(label_center("Initialize the blog"))

        grid = QtWidgets.QGridLayout()
        vbox.addLayout(grid)

        name_label = QtWidgets.QLabel("Blog's name")
        name_input = QtWidgets.QLineEdit()
        name_label.setBuddy(name_input)
        grid.addWidget(name_label, 0, 0)
        grid.addWidget(name_input, 0, 1)

        author_label = QtWidgets.QLabel("Author")
        author_input = QtWidgets.QLineEdit()
        author_label.setBuddy(author_input)
        grid.addWidget(author_label, 1, 0)
        grid.addWidget(author_input, 1, 1)

        submit_btn = QtWidgets.QPushButton('Submit')
        vbox.addWidget(submit_btn, alignment=Qt.AlignRight) # type: ignore

        form.resize(500, form.sizeHint().height())
        return form
    
    @classmethod
    def show(cls) -> None:
        app = QtWidgets.QApplication(sys.argv)
        window = cls.form()
        window.show()
        app.exec()


def label_center(text:str) -> QtWidgets.QLabel:
    label = QtWidgets.QLabel(text)
    label.setAlignment(Qt.AlignCenter)  # type: ignore
    return label


class Form(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setWindowTitle("My Form")
        self.resize(300, 200)

        self.edit = QtWidgets.QLineEdit("Write your name here")
        self.button = QtWidgets.QPushButton("Greet")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.edit)
        layout.addWidget(self.button)

        self.setLayout(layout)
        self.button.clicked.connect(self.greetings)  # type: ignore

    def greetings(self):
        print(f"Hello {self.edit.text()}")


def hello() -> None:
    app = QtWidgets.QApplication(sys.argv)
    form = Form()
    form.show()

    # label = QLabel("<font color=red size=40>Hello World!</font>")
    # label.show()
    # button = QPushButton("Click me")
    # button.clicked.connect(say_hello)
    # button.show()

    app.exec()
