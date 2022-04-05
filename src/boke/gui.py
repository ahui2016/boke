import sys
from typing import Final
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, Signal
import arrow
from result import Err, Ok, Result
from . import model
from . import db
from . import util

# https://doc.qt.io/qtforpython/overviews/qtwidgets-widgets-windowflags-example.html
# from PySide6.QtCore import Qt
# self.setWindowFlag(Qt.WindowContextHelpButtonHint, True)

Icon: Final = QtWidgets.QMessageBox.Icon
ButtonBox: Final = QtWidgets.QDialogButtonBox

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

NewCategory: Final = "新建 (New category)"


class ReadonlyLineEdit(QtWidgets.QLineEdit):
    clicked = Signal(tuple)

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def mousePressEvent(self, event):
        self.clicked.emit((self.name, self.text()))


# 这里 class 只是用来作为 namespace.
class InitBlogForm:
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

        cls.buttonBox = ButtonBox(
            ButtonBox.Ok | ButtonBox.Cancel,  # type: ignore
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


class PostForm:
    @classmethod
    def connect_db(cls) -> None:
        with db.connect() as conn:
            cls.blog_cfg = db.get_cfg(conn).unwrap()

    @classmethod
    def init(cls, filename: str, title: str) -> None:
        cls.connect_db()

        cls.form = QtWidgets.QDialog()
        cls.form.setWindowTitle("boke post")
        cls.form.setStyleSheet(FormStyle)

        vbox = QtWidgets.QVBoxLayout(cls.form)
        vbox.addWidget(label_center("Post an article"))

        grid = QtWidgets.QGridLayout()
        vbox.addLayout(grid)

        row = 0
        tips = "自动分配随机ID, 可修改"
        id_label = QtWidgets.QLabel("&ID")
        cls.id_input = QtWidgets.QLineEdit()
        cls.id_input.setText(model.date_id())
        id_label.setBuddy(cls.id_input)
        id_label.setToolTip(tips)
        cls.id_input.setToolTip(tips)
        grid.addWidget(id_label, row, 0)
        grid.addWidget(cls.id_input, row, 1)

        row += 1
        item_name = "File"
        tips = "要发表的文件，由 'boke post' 命令指定"
        file_label = QtWidgets.QLabel(item_name)
        file_input = ReadonlyLineEdit(item_name)
        file_input.setText(filename)
        file_input.setReadOnly(True)
        file_input.clicked.connect(cls.click_readonly)
        file_label.setBuddy(file_input)
        file_label.setToolTip(tips)
        file_input.setToolTip(tips)
        grid.addWidget(file_label, row, 0)
        grid.addWidget(file_input, row, 1)

        row += 1
        tips = "自动获取第一句作为标题"
        item_name = "Title"
        title_label = QtWidgets.QLabel(item_name)
        title_input = ReadonlyLineEdit(item_name)
        title_input.setText(title)
        title_input.cursorBackward(False, len(title))
        title_input.setReadOnly(True)
        title_input.clicked.connect(cls.click_readonly)
        title_label.setBuddy(title_input)
        title_label.setToolTip(tips)
        title_input.setToolTip(tips)
        grid.addWidget(title_label, row, 0)
        grid.addWidget(title_input, row, 1)

        row += 1
        tips = "自动获取默认作者，可修改"
        author_label = QtWidgets.QLabel("&Author")
        cls.author_input = QtWidgets.QLineEdit()
        cls.author_input.setText(cls.blog_cfg.author)
        author_label.setBuddy(cls.author_input)
        author_label.setToolTip(tips)
        cls.author_input.setToolTip(tips)
        grid.addWidget(author_label, row, 0)
        grid.addWidget(cls.author_input, row, 1)

        row += 1
        tips = "文章的类别, 必选"
        cat_label = QtWidgets.QLabel("Category")
        cls.cat_index: int | None = None
        cls.cat_list = QtWidgets.QComboBox()
        cls.cat_list.setPlaceholderText(" ")
        cls.cat_list.addItems(["abc", "1234", "cdefg", NewCategory])
        cls.cat_list.insertSeparator(3)
        cls.cat_list.textActivated.connect(cls.select_cat)  # type: ignore
        cat_label.setBuddy(cls.cat_list)
        cat_label.setToolTip(tips)
        cls.cat_list.setToolTip(tips)
        grid.addWidget(cat_label, row, 0)
        grid.addWidget(cls.cat_list, row, 1)

        row += 1
        tips = "发布日期，可修改（必须符合格式）"
        date_label = QtWidgets.QLabel("&Datetime")
        cls.date_input = QtWidgets.QLineEdit()
        cls.date_input.setText(model.now())
        date_label.setBuddy(cls.date_input)
        date_label.setToolTip(tips)
        cls.date_input.setToolTip(tips)
        grid.addWidget(date_label, row, 0)
        grid.addWidget(cls.date_input, row, 1)

        cls.buttonBox = ButtonBox(
            ButtonBox.Ok | ButtonBox.Cancel,  # type: ignore
            orientation=Qt.Horizontal,
        )
        cls.buttonBox.rejected.connect(cls.form.reject)  # type: ignore
        cls.buttonBox.accepted.connect(cls.accept)  # type: ignore
        vbox.addWidget(cls.buttonBox)

        cls.form.resize(640, cls.form.sizeHint().height())

    @classmethod
    def click_readonly(cls, args: tuple[str, str]) -> None:
        padding = "                                       "
        msg_box_show(args[0], args[1] + padding, Icon.Information)

    @classmethod
    def select_cat(cls, cat: str) -> None:
        if cat != NewCategory:
            cls.cat_index = cls.cat_list.currentIndex()
            print(cat)
            return

        if cls.cat_index is not None:
            cls.cat_list.setCurrentIndex(cls.cat_index)
        text, ok = QtWidgets.QInputDialog.getText(
            cls.form, "New Category", "新类别：", QtWidgets.QLineEdit.Normal
        )
        cat = text.strip()
        if ok and cat:
            cls.cat_list.insertItem(0, cat)
            cls.cat_list.setCurrentIndex(0)
            cls.cat_index = 0
        elif cls.cat_index is not None:
            cls.cat_list.setCurrentIndex(cls.cat_index)
        else:
            cls.cat_list.setCurrentText("")

    @classmethod
    def accept(cls) -> None:
        # 检查文章类型
        cat = cls.cat_list.currentText().strip()
        if not cat:
            msg_box_show("category Error", "Category is empty (请选择文章类别)", Icon.Critical)
            return

        # 检查发布时间
        published = cls.date_input.text().strip()
        try:
            _ = arrow.get(published, model.RFC3339)
        except Exception as e:
            msg_box_show("Datetime Error", str(e), Icon.Critical)
            return

        author = cls.author_input.text().strip()
        cls.form.close()

    @classmethod
    def exec(cls, filename: str, title: str) -> None:
        app = QtWidgets.QApplication(sys.argv)
        cls.init(filename, title)
        cls.form.show()
        app.exec()


def label_center(text: str) -> QtWidgets.QLabel:
    label = QtWidgets.QLabel(text)
    label.setAlignment(Qt.AlignCenter)  # type: ignore
    return label


def msg_box_show(title: str, text: str, icon: Icon = Icon.NoIcon) -> None:
    msgBox = QtWidgets.QMessageBox()
    msgBox.setIcon(icon)
    msgBox.setWindowTitle(title)
    msgBox.setText(text)
    msgBox.exec()
