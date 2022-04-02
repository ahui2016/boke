import sys
from typing import Final
from PySide6 import QtWidgets
from PySide6.QtCore import Qt

# https://doc.qt.io/qtforpython/overviews/qtwidgets-widgets-windowflags-example.html
# from PySide6.QtCore import Qt
# self.setWindowFlag(Qt.WindowContextHelpButtonHint, True)


FormStyle: Final[str] = """
QWidget {
    font-size: 18px;
    margin: 5px 0 5px 0;
}
QPushButton {
    font-size: 14px;
    padding: 5px 10px 5px 10px;
}
"""


class MyForm:
    @classmethod
    def init(cls) -> QtWidgets.QDialog:
        raise NotImplementedError

    @classmethod
    def show(cls) -> None:
        app = QtWidgets.QApplication(sys.argv)
        window = cls.init()
        window.show()
        app.exec()


# 这里 class 只是用来作为 namespace.
class InitBlogForm(MyForm):
    @classmethod
    def init(cls) -> QtWidgets.QDialog:
        form = QtWidgets.QDialog()
        form.setWindowTitle("boke init")
        form.setStyleSheet(FormStyle)

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

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,  # type: ignore
            orientation=Qt.Horizontal,
        )
        buttonBox.rejected.connect(form.reject)  # type: ignore
        vbox.addWidget(buttonBox)

        form.resize(500, form.sizeHint().height())
        return form


def label_center(text: str) -> QtWidgets.QLabel:
    label = QtWidgets.QLabel(text)
    label.setAlignment(Qt.AlignCenter)  # type: ignore
    return label
