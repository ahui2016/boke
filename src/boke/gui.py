import sys
from typing import Final
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from result import Err, Ok, Result
from . import util

# https://doc.qt.io/qtforpython/overviews/qtwidgets-widgets-windowflags-example.html
# from PySide6.QtCore import Qt
# self.setWindowFlag(Qt.WindowContextHelpButtonHint, True)


FormStyle: Final = """
QWidget {
    font-size: 18px;
    margin: 5px 0 5px 0;
}
QPushButton {
    font-size: 14px;
    padding: 5px 10px 5px 10px;
}
"""


# 这里 class 只是用来作为 namespace.
class InitBlogForm():
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
        cls.buttonBox.accepted.connect(cls.accept)  # type: ignore
        vbox.addWidget(cls.buttonBox)

        cls.form.resize(500, cls.form.sizeHint().height())

    @classmethod
    def accept(cls) -> None:
        blog_name = cls.name_input.text().strip()
        author = cls.author_input.text().strip()
        util.init_blog(blog_name, author)
        cls.form.close()
        # QtWidgets.QDialog.accept(cls.form) # 这句与 close() 的效果差不多。

    @classmethod
    def exec(cls) -> None:
        app = QtWidgets.QApplication(sys.argv)
        cls.init()
        cls.form.show()
        app.exec()

class PostForm():
    @classmethod
    def init(cls, filename:str, title:str) -> None:
        cls.form = QtWidgets.QDialog()
        cls.form.setWindowTitle("boke post")
        cls.form.setStyleSheet(FormStyle)

        vbox = QtWidgets.QVBoxLayout(cls.form)
        vbox.addWidget(label_center("Post an article"))

        grid = QtWidgets.QGridLayout()
        vbox.addLayout(grid)

        file_label = QtWidgets.QLabel("File")
        file_input = QtWidgets.QLineEdit()
        file_input.setText(filename)
        file_input.setReadOnly(True)
        file_label.setBuddy(file_input)
        grid.addWidget(file_label, 0, 0)
        grid.addWidget(file_input, 0, 1)

        title_label = QtWidgets.QLabel("Title")
        title_input = QtWidgets.QLineEdit()
        title_input.setText(title)
        title_input.setReadOnly(True)
        title_label.setBuddy(title_input)
        grid.addWidget(title_label, 1, 0)
        grid.addWidget(title_input, 1, 1)

        author_label = QtWidgets.QLabel("Author")
        cls.author_input = QtWidgets.QLineEdit()
        author_label.setBuddy(cls.author_input)
        grid.addWidget(author_label, 2, 0)
        grid.addWidget(cls.author_input, 2, 1)

        cls.buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,  # type: ignore
            orientation=Qt.Horizontal,
        )
        cls.buttonBox.rejected.connect(cls.form.reject)  # type: ignore
        # cls.buttonBox.accepted.connect(cls.accept)  # type: ignore
        vbox.addWidget(cls.buttonBox)

        cls.form.resize(500, cls.form.sizeHint().height())

    @classmethod
    def exec(cls, filename:str, title:str) -> None:
        app = QtWidgets.QApplication(sys.argv)
        cls.init(filename, title)
        cls.form.show()
        app.exec()

def label_center(text: str) -> QtWidgets.QLabel:
    label = QtWidgets.QLabel(text)
    label.setAlignment(Qt.AlignCenter)  # type: ignore
    return label
