import sys
from typing import Final
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from . import util

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
    def init(cls) -> None:
        cls.form = QtWidgets.QDialog()
        raise NotImplementedError

    @classmethod
    def show(cls) -> None:
        app = QtWidgets.QApplication(sys.argv)
        cls.init()
        cls.form.show()
        app.exec()


# 这里 class 只是用来作为 namespace.
class InitBlogForm(MyForm):
    @classmethod
    def init(cls) -> None:
        cls.form = QtWidgets.QDialog()
        cls.form.setWindowTitle("boke init")
        cls.form.setStyleSheet(FormStyle)

        vbox = QtWidgets.QVBoxLayout(cls.form)

        vbox.addWidget(label_center("Initialize the blog"))

        grid = QtWidgets.QGridLayout()
        vbox.addLayout(grid)

        name_label = QtWidgets.QLabel("Blog's name")
        cls.name_input = QtWidgets.QLineEdit()
        name_label.setBuddy(cls.name_input)
        grid.addWidget(name_label, 0, 0)
        grid.addWidget(cls.name_input, 0, 1)

        author_label = QtWidgets.QLabel("Author")
        cls.author_input = QtWidgets.QLineEdit()
        author_label.setBuddy(cls.author_input)
        grid.addWidget(author_label, 1, 0)
        grid.addWidget(cls.author_input, 1, 1)

        cls.buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,  # type: ignore
            orientation=Qt.Horizontal,
        )
        cls.buttonBox.rejected.connect(cls.form.reject)  # type: ignore
        cls.buttonBox.accepted.connect(cls.accept) # type: ignore
        vbox.addWidget(cls.buttonBox)

        cls.form.resize(500, cls.form.sizeHint().height())
    
    @classmethod
    def accept(cls) -> None:
        blog_name = cls.name_input.text().strip()
        author = cls.author_input.text().strip()
        util.init_blog(blog_name, author)
        QtWidgets.QDialog.accept(cls.form)


def label_center(text: str) -> QtWidgets.QLabel:
    label = QtWidgets.QLabel(text)
    label.setAlignment(Qt.AlignCenter)  # type: ignore
    return label
