import sqlite3 as sqlite
from cursorsearch.util import seperate_words
from pprint import pprint
from cursorsearch.dl.predict import Predictor
from cursorsearch.scoring.scoring import Scoring


class Searcher(object):
    def __init__(self, dbName, predictDbName = "predictor.db", weights=[], **kwargs) -> None:
        super().__init__()
        self.conn = sqlite.connect(dbName)
        self.predictor = Predictor(predictDbName)
        self.score = Scoring()
        self.weights = []
        try:
            self.predictor.make_tables()
        except:
            pass
        if weights == []:
            self.weights = [(1.0, self.score.frequency_score),
                            (1.5, self.score.location_score),
                            (0.5, self.score.distance_score),
                            (1.0, self.score.inbound_link_score),
                            (1.5, self.score.pagerank_score),
                            (1.0, self.score.link_text_score),
                            (1.5, self.score.predictor_score)]
        else:
            self.weights = weights

    def __del__(self):
        self.conn.close()

    def get_match_rows(self, q):
        fields = "w0.urlid"
        tables = ""
        clauses = ""
        word_ids = []

        words = seperate_words(q)
        table_number = 0

        for word in words:
            word_row = self.conn.execute(
                "SELECT rowid FROM wordlist WHERE word=?", (word,)).fetchone()
            if word_row is not None:
                word_id = word_row[0]
                word_ids.append(word_id)
                if table_number > 0:
                    tables += ","
                    clauses += " AND "
                    clauses += f"w{table_number - 1}.urlid=w{table_number}.urlid AND "
                fields += f",w{table_number}.location"
                tables += f"wordlocation w{table_number}"
                clauses += f"w{table_number}.wordid={word_id}"
                table_number += 1
        cursor = self.conn.execute(
            f"SELECT {fields} FROM {tables} WHERE {clauses}")
        rows = [row for row in cursor]
        return rows, word_ids

    def get_scored_list(self, rows, wordIds):
        total_scores = dict([(row[0], 0) for row in rows])
        weights = [(weight, func(rows, wordIds=wordIds, conn=self.conn,
                    predictor=self.predictor)) for (weight, func) in self.weights]

        for (weight, scores) in weights:
            for url in total_scores:
                total_scores[url] += weight * scores[url]

        return total_scores

    def get_url_name(self, id):
        return self.conn.execute("SELECT url FROM urllist WHERE rowid=?", (id,)).fetchone()[0]

    def query(self, q):
        (rows, word_ids) = self.get_match_rows(q)
        scores = self.get_scored_list(rows, word_ids)
        ranked_scores = sorted([(score, url)
                               for (url, score) in scores.items()], reverse=True)
        for (score, url_id) in ranked_scores[:10]:
            print(f"{score}\t{url_id}\t{self.get_url_name(url_id)}")
        return {
            "query_words": word_ids,
            "results": [{"score": score, "url_id": url_id} for (score, url_id) in ranked_scores]
        }


if __name__ == "__main__":
    engine = Searcher("search_index.db")
    result = engine.query("Python爬虫")
    pprint(result)
