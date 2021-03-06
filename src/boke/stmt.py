from typing import Final

Enable_foreign_keys: Final = "PRAGMA foreign_keys = 1;"

Create_tables: Final = """
CREATE TABLE IF NOT EXISTS metadata
(
    name    text   NOT NULL UNIQUE,
    value   text   NOT NULL
);

CREATE TABLE IF NOT EXISTS category
(
    id      text   PRIMARY KEY COLLATE NOCASE,
    name    text   NOT NULL UNIQUE COLLATE NOCASE,
    notes   text   NOT NULL
);

CREATE TABLE IF NOT EXISTS article
(
    id          text   PRIMARY KEY COLLATE NOCASE,
    cat_id      REFERENCES category(id) COLLATE NOCASE,
    title       text   NOT NULL UNIQUE COLLATE NOCASE,
    author      text   NOT NULL,
    published   text   NOT NULL,
    hidden      int    NOT NULL,
    updated     text   NOT NULL,
    last_pub    text   NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_article_cat_id ON article(cat_id);
CREATE INDEX IF NOT EXISTS idx_article_published ON article(published);

CREATE TABLE IF NOT EXISTS tag
(
    id     text   PRIMARY KEY COLLATE NOCASE,
    name   text   NOT NULL UNIQUE COLLATE NOCASE
);

CREATE TABLE IF NOT EXISTS tag_article
(
    tag_id       REFERENCES tag(id)     COLLATE NOCASE,
    article_id   REFERENCES article(id) ON UPDATE CASCADE COLLATE NOCASE
);

CREATE INDEX IF NOT EXISTS idx_tag_article_tag ON tag_article(tag_id);
CREATE INDEX IF NOT EXISTS idx_tag_article_article ON tag_article(article_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tag_article
    ON tag_article(tag_id, article_id);
"""

Insert_metadata: Final = (
    "INSERT INTO metadata (name, value) VALUES (:name, :value);"
)
Get_metadata: Final = "SELECT value FROM metadata WHERE name=?;"
Update_metadata: Final = "UPDATE metadata SET value=:value WHERE name=:name;"


Get_all_cats: Final = """
    SELECT * FROM category;
    """

Get_cat_id: Final = """
    SELECT id FROM category WHERE name=?;
    """

Get_cat: Final = """
    SELECT * FROM category WHERE id=?;
    """

Insert_cat: Final = """
    INSERT INTO category (id, name, notes) VALUES (:id, :name, :notes);
    """

Update_cat: Final = """
    UPDATE category SET name=:name, notes=:notes WHERE id=:id;
    """

Delete_cat: Final = """
    DELETE FROM category WHERE id=?;
"""

Get_articles_by_cat: Final = """
    SELECT * FROM article WHERE cat_id=? ORDER BY published DESC;
    """

Count_articles_by_cat: Final = """
    SELECT count(*) FROM article WHERE cat_id=?;
"""

Get_article: Final = """
    SELECT * FROM article WHERE id=?;
    """

Get_all_tags: Final = """
    SELECT * FROM tag;
    """

Get_tag_names: Final = """
    SELECT tag.name FROM tag_article, tag
    WHERE tag_article.tag_id=tag.id and article_id=?;
    """

Get_tags_by_article: Final = """
    SELECT tag.id, tag.name FROM tag_article, tag
    WHERE tag_article.tag_id=tag.id and article_id=?;
    """

Count_articles_by_tag: Final = """
    SELECT count(*) FROM tag_article, tag
    WHERE tag_article.tag_id=tag.id and tag.name=?;
    """

Get_art_ids_by_tag: Final = """
    SELECT article_id FROM tag_article, tag
    WHERE tag_article.tag_id=tag.id and tag.name=?;
    """

Get_article_hidden: Final = """
    SELECT hidden FROM article WHERE id=?;
    """

Get_recent_articles: Final = """
    SELECT * FROM article WHERE hidden=0 ORDER BY published DESC LIMIT ?;
    """

Article_id: Final = """
    SELECT count(*) FROM article WHERE id=?;
    """

Article_title: Final = """
    SELECT count(*) FROM article WHERE title=?;
    """

Get_article_id_by_title: Final = """
    SELECT id FROM article WHERE title=?;
    """

Tag_name: Final = """
    SELECT count(*) FROM tag WHERE name=?;
    """
Get_tag_name: Final = """
    SELECT name FROM tag WHERE id=?;
    """
Get_tag_id: Final = """
    SELECT id FROM tag WHERE name=?;
    """

Insert_tag: Final = """
    INSERT INTO tag (id, name) VALUES (:id, :name);
    """

Rename_tag: Final = """
    UPDATE tag SET name=:new_name WHERE name=:old_name;
"""

Insert_article: Final = """
    INSERT INTO article (
       id,  cat_id,  title,  author,  published,  hidden,  updated,  last_pub)
    VALUES (
      :id, :cat_id, :title, :author, :published, :hidden, :updated, :last_pub);
    """

Insert_tag_article: Final = """
    INSERT INTO tag_article (tag_id, article_id) VALUES (:tag_id, :article_id);
    """

Delete_article: Final = """
    DELETE FROM article WHERE id=?;
"""

Delete_tag_article = """
    DELETE FROM tag_article WHERE article_id=:article_id and
    tag_id=(SELECT id FROM tag WHERE tag.name=:tag_name);
    """

Del_tag_art_by_art_id = """
    DELETE FROM tag_article WHERE article_id=:article_id;
    """

Update_last_pub: Final = """
    UPDATE article SET last_pub=:last_pub WHERE id=:id;
    """

Update_article_date: Final = """
    UPDATE article SET updated=:updated, title=:title WHERE id=:id;
    """

Update_article: Final = """
    UPDATE article SET
        id=:new_id,     cat_id=:cat_id,   title=:title,
        author=:author, updated=:updated, hidden=:hidden
    WHERE id=:id;
    """

Delete_tag = """
    DELETE FROM tag WHERE name=?;
    """
