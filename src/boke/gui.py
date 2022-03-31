import sys
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QDialog,
    QLineEdit,
    QVBoxLayout,
)
from PySide6.QtCore import Slot

# https://doc.qt.io/qtforpython/overviews/qtwidgets-widgets-windowflags-example.html
# from PySide6.QtCore import Qt
# self.setWindowFlag(Qt.WindowContextHelpButtonHint, True)


class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setWindowTitle("My Form")
        self.resize(300, 200)

        self.edit = QLineEdit("Write your name here")
        self.button = QPushButton("Greet")

        layout = QVBoxLayout()
        layout.addWidget(self.edit)
        layout.addWidget(self.button)

        self.setLayout(layout)
        self.button.clicked.connect(self.greetings)

    def greetings(self):
        print(f"Hello {self.edit.text()}")


@Slot()
def say_hello():
    print("Button clicked, Hello!")


def hello() -> None:
    app = QApplication(sys.argv)
    form = Form()
    form.show()

    # label = QLabel("<font color=red size=40>Hello World!</font>")
    # label.show()
    # button = QPushButton("Click me")
    # button.clicked.connect(say_hello)
    # button.show()

    app.exec()
