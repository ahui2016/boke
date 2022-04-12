from pathlib import Path
import re
import sys
from typing import Final, cast
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, Signal
import arrow
from result import Err, Ok, Result
from . import model
from . import stmt
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
    margin-top: 5px;
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


# 这里 class 只是用来作为 namespace.
class ArticleForm:
    @classmethod
    def init(cls, filename: Path, title: str) -> None:
        cls.src_file = filename
        cls.article_title = title
        with db.connect() as conn:
            cls.blog_cfg: model.BlogConfig = db.get_cfg(conn).unwrap()
            cls.cats: list[str] = db.get_all_cats_name(conn)

        cls.form = QtWidgets.QDialog()
        cls.form.setWindowTitle("boke")
        cls.form.setStyleSheet(FormStyle)

        cls.title = label_center("boke")
        vbox = QtWidgets.QVBoxLayout(cls.form)
        vbox.addWidget(cls.title)

        grid = QtWidgets.QGridLayout()
        vbox.addLayout(grid)

        row = 0
        cls.id_label = QtWidgets.QLabel("&ID")
        cls.id_input = QtWidgets.QLineEdit()
        cls.id_input.setText(model.date_id())
        cls.id_label.setBuddy(cls.id_input)
        grid.addWidget(cls.id_label, row, 0)
        grid.addWidget(cls.id_input, row, 1)

        row += 1
        item_name = "File"
        cls.file_label = QtWidgets.QLabel(item_name)
        cls.file_input = ReadonlyLineEdit(item_name)
        cls.file_input.setText(str(filename))
        cls.file_input.setReadOnly(True)
        cls.file_input.clicked.connect(cls.click_readonly)
        cls.file_label.setBuddy(cls.file_input)
        grid.addWidget(cls.file_label, row, 0)
        grid.addWidget(cls.file_input, row, 1)

        row += 1
        title_tips = "自动获取第一句作为标题"
        item_name = "Title"
        title_label = QtWidgets.QLabel(item_name)
        title_input = ReadonlyLineEdit(item_name)
        title_input.setText(title)
        title_input.cursorBackward(False, len(title))
        title_input.setReadOnly(True)
        title_input.clicked.connect(cls.click_readonly)
        title_label.setBuddy(title_input)
        title_label.setToolTip(title_tips)
        title_input.setToolTip(title_tips)
        grid.addWidget(title_label, row, 0)
        grid.addWidget(title_input, row, 1)

        row += 1
        cls.author_label = QtWidgets.QLabel("&Author")
        cls.author_input = QtWidgets.QLineEdit()
        cls.author_input.setText(cls.blog_cfg.author)
        cls.author_label.setBuddy(cls.author_input)
        grid.addWidget(cls.author_label, row, 0)
        grid.addWidget(cls.author_input, row, 1)

        row += 1
        cat_tips = "文章的类别, 必选"
        cls.cat_label = QtWidgets.QLabel("Category")
        cls.cat_index: int | None = None
        cls.cat_list = QtWidgets.QComboBox()
        cls.cat_list.setPlaceholderText(" ")
        cls.cat_list.addItems(cls.cats + [NewCategory])
        cls.cat_list.insertSeparator(len(cls.cats))
        cls.cat_list.textActivated.connect(cls.select_cat)  # type: ignore
        cls.cat_label.setBuddy(cls.cat_list)
        cls.cat_label.setToolTip(cat_tips)
        cls.cat_list.setToolTip(cat_tips)
        grid.addWidget(cls.cat_label, row, 0)
        grid.addWidget(cls.cat_list, row, 1)

        row += 1
        cls.date_label = QtWidgets.QLabel("&Datetime")
        cls.date_input = QtWidgets.QLineEdit()
        cls.date_input.setText(model.now())
        cls.date_label.setBuddy(cls.date_input)
        grid.addWidget(cls.date_label, row, 0)
        grid.addWidget(cls.date_input, row, 1)

        row += 1
        tips = "标签，用逗号或空格间隔"
        tags_label = QtWidgets.QLabel("&Tags")
        cls.tags_input = QtWidgets.QPlainTextEdit()
        cls.tags_input.setFixedHeight(70)
        tags_label.setBuddy(cls.tags_input)
        tags_label.setToolTip(tips)
        cls.tags_input.setToolTip(tips)
        grid.addWidget(tags_label, row, 0, Qt.AlignTop)  # type: ignore
        grid.addWidget(cls.tags_input, row, 1, 2, 1)

        row += 1
        cls.tags_preview_btn = QtWidgets.QPushButton("&preview")
        cls.tags_preview_btn.clicked.connect(cls.preview_tags)  # type: ignore
        grid.addWidget(cls.tags_preview_btn, row, 0)

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
        alert(args[0], args[1] + padding, Icon.Information)

    @classmethod
    def select_cat(cls, cat: str) -> None:
        if cat != NewCategory:
            cls.cat_index = cls.cat_list.currentIndex()
            return

        cls.reset_cat_list()
        text, ok = QtWidgets.QInputDialog.getText(
            cls.form, "New Category", "新类别：", QtWidgets.QLineEdit.Normal
        )
        cat = text.strip()
        if ok and cat:
            cls.insert_cat(cat)

    @classmethod
    def reset_cat_list(cls) -> None:
        if cls.cat_index is not None:
            cls.cat_list.setCurrentIndex(cls.cat_index)
        else:
            cls.cat_list.setCurrentText("")

    @classmethod
    def preview_tags(cls) -> None:
        match extract_tags(cls.tags_input.toPlainText()):
            case Err(e):
                alert("Tags Error", e, Icon.Critical)
            case Ok(tags):
                preview = "  #".join(tags)
                if preview:
                    preview = "#" + preview
                else:
                    preview = "(Tags: empty) 没有标签"
                alert("Tags Preview", preview)

    @classmethod
    def insert_cat(cls, cat: str) -> None:
        r = db.execute(db.insert_cat, cat)
        err = cast(Result[str, str], r).err()
        if err:
            alert("Category Error", err, Icon.Critical)
            return

        cls.cat_list.insertItem(0, cat)
        cls.cat_list.setCurrentIndex(0)
        cls.cat_index = 0

    @classmethod
    def accept(cls) -> None:
        pass

    @classmethod
    def exec(cls, filename: Path, title: str) -> None:
        app = QtWidgets.QApplication(sys.argv)
        cls.init(filename, title)
        cls.form.show()
        app.exec()


class PostForm(ArticleForm):
    @classmethod
    def init(cls, filename: Path, title: str) -> None:
        super().init(filename, title)
        cls.form.setWindowTitle("boke post")
        cls.title.setText("Post an article")

        id_tips = "自动分配随机ID, 可修改"
        cls.id_label.setToolTip(id_tips)
        cls.id_input.setToolTip(id_tips)

        file_tips = "要发表的文件，由 'boke post' 命令指定"
        cls.file_label.setToolTip(file_tips)
        cls.file_input.setToolTip(file_tips)

        author_tips = "自动获取默认作者，可修改"
        cls.author_label.setToolTip(author_tips)
        cls.author_input.setToolTip(author_tips)

        date_tips = "发布日期，可修改（必须符合格式）"
        cls.date_label.setToolTip(date_tips)
        cls.date_input.setToolTip(date_tips)

        # submit button
        cls.buttonBox.button(ButtonBox.Ok).setText("Post")

    @classmethod
    def accept(cls) -> None:
        # 检查 ID
        article_id = cls.id_input.text().strip()
        if not article_id:
            alert("ID Error", "ID is empty (请填写ID)", Icon.Critical)
            return

        err = model.check_article_id(article_id).err()
        if err:
            alert("ID Error", err, Icon.Critical)
            return

        if db.execute(db.exists, stmt.Article_id, (article_id,)):
            alert("ID Error", f"ID exists (ID已存在): {article_id}", Icon.Critical)
            return

        # 检查文章类别
        cat = cls.cat_list.currentText().strip()
        if not cat:
            alert("category Error", "Category is empty (请选择文章类别)", Icon.Critical)
            return
        cat_id = db.execute(db.fetchone, stmt.Get_cat_id, (cat,))

        # 检查发布时间
        published = cls.date_input.text().strip()
        try:
            _ = arrow.get(published, model.RFC3339)
        except Exception as e:
            alert("Datetime Error", str(e), Icon.Critical)
            return

        # 检查标签
        tags = []
        match extract_tags(cls.tags_input.toPlainText()):
            case Err(e):
                alert("Tags Error", e, Icon.Critical)
                return
            case Ok(items):
                tags = items

        # 如果作者就是默认作者，那么，在数据库里 author 就是空字符串。
        author = cls.author_input.text().strip()
        if author == cls.blog_cfg.author:
            author = ""
        article = model.new_article_from(
            dict(
                id=article_id,
                cat_id=cat_id,
                title=cls.article_title,
                author=author,
                published=published,
                updated=published,
                last_pub="",
            )
        )

        # 发表文章（从 drafts 移动到 posted）
        util.post_article(cls.src_file, article, tags)
        util.show_article_info(article, cat, tags, cls.blog_cfg)
        cls.form.close()


class UpdateForm(PostForm):
    @classmethod
    def init(cls, filename: Path, title: str) -> None:
        super().init(filename, title)
        cls.form.setWindowTitle("boke update")
        cls.title.setText("Update the article")

        cls.article_id = filename.stem
        cat = ""
        tags = []
        with db.connect() as conn:
            article = db.get_article(conn, cls.article_id)
            cat = db.fetchone(conn, stmt.Get_cat_name, (article.cat_id,))
            tags = db.get_tags_by_article(conn, cls.article_id)
            cls.published = article.published
            cls.last_pub = article.last_pub

        # 只能更新 posted 文件夹里的文件
        if util.not_in_posted(cls.src_file, cls.article_id, cls.published):
            sys.exit()

        id_tips = "如果更改ID, 文件名与网址都会随之变更。"
        cls.id_input.setText(cls.article_id)
        cls.id_label.setToolTip(id_tips)
        cls.id_input.setToolTip(id_tips)

        file_tips = "文件名"
        cls.file_label.setToolTip(file_tips)
        cls.file_input.setToolTip(file_tips)

        author_tips = "作者"
        cls.author_label.setToolTip(author_tips)
        cls.author_input.setToolTip(author_tips)

        # 文章类别
        cls.cat_index = cls.cats.index(cat)
        cls.cat_list.setCurrentIndex(cls.cat_index)

        # 更新日期
        date_tips = "更新日期，自动获取当前时间，可修改"
        cls.date_label.setToolTip(date_tips)
        cls.date_input.setToolTip(date_tips)

        # 标签
        cls.tags_input.setPlainText(", ".join(tags))

        # submit button
        cls.buttonBox.button(ButtonBox.Ok).setText("Update")

    @classmethod
    def accept(cls) -> None:
        # 检查 ID
        new_id = cls.id_input.text().strip()
        if not new_id:
            alert("ID Error", "ID is empty (请填写ID)", Icon.Critical)
            return

        err = model.check_article_id(new_id).err()
        if err:
            alert("ID Error", err, Icon.Critical)
            return

        new_id_exists = db.execute(db.exists, stmt.Article_id, (new_id,))
        if new_id != cls.article_id and new_id_exists:
            alert("ID Error", f"ID exists (ID已存在): {new_id}", Icon.Critical)
            return

        # 检查文章类别
        cat = cls.cat_list.currentText().strip()
        if not cat:
            alert("category Error", "Category is empty (请选择文章类别)", Icon.Critical)
            return
        cat_id = db.execute(db.fetchone, stmt.Get_cat_id, (cat,))

        # 检查更新时间
        updated = cls.date_input.text().strip()
        try:
            _ = arrow.get(updated, model.RFC3339)
        except Exception as e:
            alert("Datetime Error", str(e), Icon.Critical)
            return

        if updated <= cls.last_pub:
            alert(
                "Datetime Error",
                f"更新日期不可早于上次执行 'boke gen' 的时间 ({cls.last_pub})",
                Icon.Critical,
            )
            return

        # 检查标签
        tags = []
        match extract_tags(cls.tags_input.toPlainText()):
            case Err(e):
                alert("Tags Error", e, Icon.Critical)
                return
            case Ok(items):
                tags = items

        # 如果作者就是默认作者，那么，在数据库里 author 就是空字符串。
        author = cls.author_input.text().strip()
        if author == cls.blog_cfg.author:
            author = ""

        art_dict = dict(
            id=cls.article_id,
            new_id=new_id,
            cat_id=cat_id,
            title=cls.article_title,
            author=author,
            updated=updated,
        )

        # 更新数据库
        with db.connect() as conn:
            db.connUpdate(conn, stmt.Update_article, art_dict)

        # 更新文件名
        if new_id != cls.article_id:
            src = db.posted_file_path(cls.article_id, cls.published)
            target = db.posted_file_path(new_id, cls.published)
            print(src)
            print(target)
            src.rename(target)

        # 显示更新后的文章信息
        art_dict["published"] = cls.published
        art_dict["last_pub"] = cls.last_pub
        if new_id != cls.article_id:
            art_dict["id"] = new_id
        util.show_article_info(
            model.new_article_from(art_dict), cat, tags, cls.blog_cfg
        )
        cls.form.close()


def label_center(text: str) -> QtWidgets.QLabel:
    label = QtWidgets.QLabel(text)
    label.setAlignment(Qt.AlignCenter)  # type: ignore
    return label


def alert(title: str, text: str, icon: Icon = Icon.Information) -> None:
    msgBox = QtWidgets.QMessageBox()
    msgBox.setIcon(icon)
    msgBox.setWindowTitle(title)
    msgBox.setText(text)
    msgBox.exec()


def extract_tags(s: str) -> Result[list[str], str]:
    sep_pattern: Final = re.compile(r"[#;,，；\s]")
    forbid_pattern: Final = re.compile(
        r"[\`\~\!\@\$\%\^\&\*\(\)\-\=\+\[\]\{\}\\\|\:\'\"\<\>\.\?\/]"
    )

    matched = forbid_pattern.search(s)
    if matched is not None:
        return Err(f"Forbidden character (标签不可包含): {matched.group(0)}")

    tags = sep_pattern.split(s)
    not_empty = [tag for tag in tags if tag]
    return Ok(model.unique_str_list(not_empty))
