from math import tanh
import sqlite3 as sqlite
from cursorsearch.util import dtanh

class Predictor(object):
    def __init__(self, dbName) -> None:
        super().__init__()
        self.conn = sqlite.connect(dbName)
        self.DEFAULT = -0.2
    
    def __del__(self):
        self.conn.close()
    
    def make_tables(self):
        self.conn.execute("CREATE TABLE hiddennode(create_key)")
        self.conn.execute("CREATE TABLE wordhidden(fromid,toid,strength)")
        self.conn.execute("CREATE TABLE hiddenurl(fromid,toid,strength)")
        self.conn.commit()
    
    def get_table(self, layer):
        return ("wordhidden" if layer == 0 else "hiddenurl")
    
    def get_strength(self, fromId, toId, layer):
        table = self.get_table(layer)
        res = self.conn.execute(f"SELECT strength FROM {table} WHERE fromid=? AND toid=?", (fromId, toId)).fetchone()
        if res is None:
            if layer == 0: return self.DEFAULT
            if layer == 1: return 0
        return res[0]
    
    def set_strength(self, fromId, toId, layer, strength):
        table = self.get_table(layer)
        res = self.conn.execute(f"SELECT rowid FROM {table} WHERE fromid=? AND toid=?", (fromId, toId)).fetchone()
        if res is None:
            self.conn.execute(f"INSERT INTO {table} (fromid,toid,strength) values (?,?,?)", (fromId, toId, strength))
        else:
            self.conn.execute(f"UPDATE {table} SET strength={strength} WHERE rowid=?", (res[0],))
    
    def generate_hidden_node(self, wordIds, urls):
        if len(wordIds) > 3: return None
        create_key = "_".join(sorted([str(wi) for wi in wordIds]))
        res = self.conn.execute("SELECT rowid FROM hiddennode WHERE create_key=?", (create_key,)).fetchone()

        if res is None:
            cursor = self.conn.execute("INSERT INTO hiddennode (create_key) VALUES (?)", (create_key,))
            hidden_id = cursor.lastrowid
            for word_id in wordIds:
                self.set_strength(word_id, hidden_id, 0, 1.0 / len(wordIds))
            for url_id in urls:
                self.set_strength(hidden_id, url_id, 1, 0.1)
            self.conn.commit()
    
    def get_all_hidden_ids(self, wordIds, urlIds):
        l1 = {}
        for wordId in wordIds:
            cursor = self.conn.execute("SELECT toid FROM wordhidden WHERE fromid=?", (wordId,))
            for row in cursor: l1[row[0]] = 1
        for url_id in urlIds:
            cursor = self.conn.execute("SELECT fromid FROM hiddenurl WHERE toid=?", (url_id,))
            for row in cursor: l1[row[0]] = 1
        return list(l1.keys())
    
    def setup_network(self, wordIds, urlIds):
        self.word_ids = wordIds
        self.hidden_ids = self.get_all_hidden_ids(wordIds, urlIds)
        self.url_ids = urlIds

        self.a_i = [1.0] * len(self.word_ids)
        self.a_h = [1.0] * len(self.hidden_ids)
        self.a_o = [1.0] * len(self.url_ids)

        self.w_i = [[self.get_strength(word_id, hidden_id, 0) for hidden_id in self.hidden_ids] for word_id in self.word_ids]
        self.w_o = [[self.get_strength(hidden_id, url_id, 1) for url_id in self.url_ids] for hidden_id in self.hidden_ids]

    def feed_forward(self):
        for i in range(len(self.word_ids)):
            self.a_i[i] = 1.0

        for i in range(len(self.hidden_ids)):
            sum = 0.0
            for j in range(len(self.word_ids)):
                sum += self.a_i[j] * self.w_i[j][i]
            self.a_h[i] = tanh(sum)
        
        for i in range(len(self.url_ids)):
            sum = 0.0
            for j in range(len(self.hidden_ids)):
                sum += self.a_h[j] * self.w_o[j][i]
            self.a_o[i] = tanh(sum)

        return self.a_o[:]
    
    def get_result(self, wordIds, urlIds):
        self.setup_network(wordIds, urlIds)
        return self.feed_forward()
    
    def back_propagate(self, targets, N=0.5):
        output_deltas = [0.0] * len(self.url_ids)
        for i in range(len(self.url_ids)):
            error = targets[i] - self.a_o[i]
            output_deltas[i] = dtanh(self.a_o[i]) * error
        hidden_deltas = [0.0] * len(self.hidden_ids)
        for i in range(len(self.hidden_ids)):
            error = float(0)
            for j in range(len(self.url_ids)):
                error = error + output_deltas[j] * self.w_o[i][j]
            hidden_deltas[i] = dtanh(self.a_h[i]) * error
        for i in range(len(self.hidden_ids)):
            for j in range(len(self.url_ids)):
                change = output_deltas[j] * self.a_h[i]
                self.w_o[i][j] = self.w_o[i][j] + N * change
        for i in range(len(self.word_ids)):
            for j in range(len(self.hidden_ids)):
                change = hidden_deltas[j] * self.a_i[i]
                self.w_i[i][j] = self.w_i[i][j] + N * change
    
    def update_database(self):
        for i in range(len(self.word_ids)):
            for j in range(len(self.hidden_ids)):
                self.set_strength(self.word_ids[i], self.hidden_ids[j], 0, self.w_i[i][j])
        for i in range(len(self.hidden_ids)):
            for j in range(len(self.url_ids)):
                self.set_strength(self.hidden_ids[i], self.url_ids[j], 1, self.w_o[i][j])
        self.conn.commit()
    
    def train_query(self, wordIds, urlIds, selectedUrl):
        self.generate_hidden_node(wordIds, urlIds)
        self.setup_network(wordIds, urlIds)
        self.feed_forward()
        targets = [0.0] * len(urlIds)
        targets[urlIds.index(selectedUrl)] = 1.0
        error = self.back_propagate(targets)
        self.update_database()
