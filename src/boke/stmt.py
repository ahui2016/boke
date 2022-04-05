from typing import Final

Create_tables: Final = """
PRAGMA foreign_keys = ON;

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
    published   text   NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_article_cat_id ON article(cat_id);
CREATE INDEX IF NOT EXISTS idx_article_published ON article(published);

CREATE TABLE IF NOT EXISTS tag
(
    name   text   PRIMARY KEY COLLATE NOCASE
);

CREATE TABLE IF NOT EXISTS tag_article
(
    tag_name     REFERENCES tag(name)   COLLATE NOCASE,
    article_id   REFERENCES article(id) COLLATE NOCASE
);

CREATE INDEX IF NOT EXISTS idx_tag_article_tag ON tag_article(tag_name);
CREATE INDEX IF NOT EXISTS idx_tag_article_article ON tag_article(article_id);

"""

Insert_metadata: Final = "INSERT INTO metadata (name, value) VALUES (:name, :value);"
Get_metadata: Final = "SELECT value FROM metadata WHERE name=?;"
Update_metadata: Final = "UPDATE metadata SET value=:value WHERE name=:name;"

Get_all_cat: Final = """
    SELECT name FROM category
    """

Insert_cat: Final = """
    INSERT INTO category (id, name, notes) VALUES (:id, :name, :notes)
    """
