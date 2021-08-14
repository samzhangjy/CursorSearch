from cursorsearch.util import seperate_words
from requests import get as get_webpage
from bs4 import BeautifulSoup
import sqlite3 as sqlite


class Crawler(object):
    def __init__(self, dbName) -> None:
        super().__init__()
        self.SITEMAP_URL = "https://www.helloworld.net/blog.xml"
        self.headers = {
            "User-Agent": "CursorSpider"
        }
        self.conn = sqlite.connect(dbName)
        self.IGNOREWORDS = [",", ".", "。", "，", "?", "？", "!", "！",
                            "\"", "“", "”", "'", "……", "的", "了", "：", ":", "", " "]
        self.IGNOREURL = ["https://www.helloworld.net/app/download", "https://www.helloworld.net/html2md",
                          "https://www.helloworld.net/?sort=following", "https://www.helloworld.net/?sort=hottest"]
        # self.visited = []
        self.BASE_URL = "https://www.helloworld.net"
        self.PAGERANK_DAMPING_FACTOR = 0.85
        self.PAGERANK_INITIAL_VALUE = 1.0
        self.PAGERANK_MIN_VALUE = 0.15

    def __del__(self):
        self.conn.close()

    def db_commit(self):
        self.conn.commit()

    def get_entry_id(self, table, field, value, createnew=True):
        cur = self.conn.execute(
            f"SELECT rowid FROM {table} WHERE {field}=?", (value,))
        res = cur.fetchone()
        if res is None:
            cur = self.conn.execute(
                f"INSERT INTO {table} ({field}) VALUES (?)", (value,))
            return cur.lastrowid
        else:
            return res[0]

    def add_to_index(self, url, text):
        if self.is_indexed(url):
            return
        print(f"Indexing {url}")

        words = self.separate_words(text)
        url_id = self.get_entry_id("urllist", "url", url)

        for i in range(len(words)):
            word = words[i]
            if word in self.IGNOREWORDS or not word.strip():
                continue
            word_id = self.get_entry_id("wordlist", "word", word)
            self.conn.execute(
                "INSERT INTO wordlocation(urlid,wordid,location) values (?,?,?)", (url_id, word_id, i))

    def separate_words(self, text):
        return seperate_words(text)

    def is_indexed(self, url):
        u = self.conn.execute(
            "SELECT rowid FROM urllist WHERE url=?", (url,)).fetchone()
        if u is not None:
            v = self.conn.execute(
                "SELECT * FROM wordlocation WHERE urlid=?", (u[0],)).fetchone()
            if v is not None:
                return True
        return False

    def add_link_ref(self, urlFrom, urlTo, linkText):
        words = self.separate_words(linkText)
        fromid = self.get_entry_id('urllist', 'url', urlFrom)
        toid = self.get_entry_id('urllist', 'url', urlTo)
        if fromid == toid:
            return
        cur = self.conn.execute(
            "insert into link(fromid,toid) values (%d,%d)" % (fromid, toid))
        linkid = cur.lastrowid
        for word in words:
            if word in self.IGNOREWORDS:
                continue
            wordid = self.get_entry_id('wordlist', 'word', word)
            self.conn.execute(
                "insert into linkwords(linkid,wordid) values (%d,%d)" % (linkid, wordid))

    def crawl(self, pages: list):
        new_pages = True
        depth = 0
        while new_pages and depth <= 5000:
            new_pages = []
            depth += 1
            for page in pages:
                try:
                    content = get_webpage(page).content
                    soup = BeautifulSoup(content, "html.parser")
                except:
                    print(f"Could not open page {page}")
                    continue
                try:
                    try:
                        self.add_to_index(
                            page, soup.title.text + soup.body.article.text)
                    except:
                        self.add_to_index(
                            page, soup.title.text + soup.body.text)
                except:
                    try:
                        self.add_to_index(page, soup.body.article.text)
                    except:
                        self.add_to_index(page, soup.body.text)
                # print(page, soup.title.text)
                links = soup.body.findAll("a")
                for link in links:
                    try:
                        try:
                            link["href"]
                        except:
                            continue
                        if link["href"].startswith("javascript") or link["href"].startswith("about:blank") or \
                                link["href"].startswith("mailto"):
                            continue
                        url = (self.BASE_URL if not link["href"].startswith(
                            "http") else "") + link["href"]
                        if self.is_indexed(url) or "https://www.helloworld.net/redirect?" in url or \
                                not url.startswith("https://www.helloworld.net") or url in self.IGNOREURL:
                            continue
                        self.add_link_ref(page, url, link.text)
                        new_pages.append(url)
                    except:
                        pass
                self.db_commit()
            pages = new_pages

    def create_index_tables(self):
        self.conn.execute('create table urllist(url)')
        self.conn.execute('create table wordlist(word)')
        self.conn.execute('create table wordlocation(urlid,wordid,location)')
        self.conn.execute('create table link(fromid integer,toid integer)')
        self.conn.execute('create table linkwords(wordid,linkid)')
        self.conn.execute('create index wordidx on wordlist(word)')
        self.conn.execute('create index urlidx on urllist(url)')
        self.conn.execute('create index wordurlidx on wordlocation(wordid)')
        self.conn.execute('create index urltoidx on link(toid)')
        self.conn.execute('create index urlfromidx on link(fromid)')
        self.db_commit()

    def calculate_pagerank(self, iterations=20):
        self.conn.execute("DROP TABLE IF EXISTS pagerank")
        self.conn.execute("CREATE TABLE pagerank(urlid PRIMARY KEY,score)")

        self.conn.execute(
            f"INSERT INTO pagerank SELECT rowid, {self.PAGERANK_INITIAL_VALUE} FROM urllist")
        self.db_commit()

        for i in range(iterations):
            print(f"Calculating PageRank... Iteration {i}")
            row_ids = self.conn.execute("SELECT rowid FROM urllist")
            for (urlid,) in row_ids:
                pr = self.PAGERANK_MIN_VALUE

                linkers = self.conn.execute(
                    "SELECT DISTINCT fromid FROM link WHERE toid=?", (urlid,))
                for (linker,) in linkers:
                    linking_pr = self.conn.execute(
                        "SELECT score FROM pagerank WHERE urlid=?", (linker,)).fetchone()[0]
                    linking_count = self.conn.execute(
                        "SELECT COUNT(*) FROM link WHERE fromid=?", (linker,)).fetchone()[0]
                    pr += self.PAGERANK_DAMPING_FACTOR * \
                        (linking_pr / linking_count)
                self.conn.execute(
                    "UPDATE pagerank SET score=? WHERE urlid=?", (pr, urlid))
            self.db_commit()


if __name__ == "__main__":
    crawler = Crawler("search_index.db")
    try:
        crawler.create_index_tables()
    except:
        pass
    # crawler.crawl(["https://www.helloworld.net/"])
    # crawler.calculate_pagerank()
    cur = crawler.conn.execute(
        'select * from pagerank order by score desc').fetchall()
    for i in cur[:10]:
        print(i)
