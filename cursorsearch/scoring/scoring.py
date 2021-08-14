from cursorsearch.util import normalize_scores


class Scoring(object):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def frequency_score(rows, **kwargs):
        counts = dict([(row[0], 0) for row in rows])
        for row in rows:
            counts[row[0]] += 1
        return normalize_scores(counts)

    @staticmethod
    def location_score(rows, **kwargs):
        locations = dict([(row[0], 1e6) for row in rows])
        for row in rows:
            loc = sum(row[1:])
            if loc < locations[row[0]]:
                locations[row[0]] = loc
        return normalize_scores(locations, smallIsBetter=True)

    @staticmethod
    def distance_score(rows, **kwargs):
        if len(rows[0]) <= 2:
            return dict([(row[0], 1.0) for row in rows])
        min_distance = dict([(row[0], 1e6) for row in rows])
        for row in rows:
            dist = sum([abs(row[i] - row[i - 1]) for i in range(2, len(row))])
            if dist < min_distance[row[0]]:
                min_distance[row[0]] = dist
        return normalize_scores(min_distance, smallIsBetter=True)

    @staticmethod
    def inbound_link_score(rows, **kwargs):
        unique_urls = set([row[0] for row in rows])
        inbound_count = dict([(u, kwargs["conn"].execute(
            "SELECT COUNT(*) FROM link WHERE toid=?", (u,)).fetchone()[0]) for u in unique_urls])
        return normalize_scores(inbound_count)

    @staticmethod
    def pagerank_score(rows, **kwargs):
        pageranks = dict([(row[0], kwargs["conn"].execute(
            "SELECT score FROM pagerank WHERE urlid=?", (row[0],)).fetchone()[0]) for row in rows])
        max_rank = max(pageranks.values())
        return dict([(u, float(l) / max_rank) for (u, l) in pageranks.items()])

    @staticmethod
    def link_text_score(rows, **kwargs):
        link_scores = dict([(row[0], 0) for row in rows])
        for word_id in kwargs["wordIds"]:
            cursor = kwargs["conn"].execute(
                "SELECT link.fromid,link.toid FROM linkwords,link WHERE wordid=? AND linkwords.linkid=link.rowid", (word_id,))
            for (from_id, to_id) in cursor:
                if to_id in link_scores:
                    pr = kwargs["conn"].execute(
                        "SELECT score FROM pagerank WHERE urlid=?", (from_id,)).fetchone()[0]
                    link_scores[to_id] += pr
        max_score = max(link_scores.values())
        return dict([(u, float(l) / max_score) for (u, l) in link_scores.items()])

    @staticmethod
    def predictor_score(rows, **kwargs):
        url_ids = [url_id for url_id in set([row[0] for row in rows])]
        predictor_results = kwargs["predictor"].get_result(
            kwargs["wordIds"], url_ids)
        scores = dict([(url_ids[i], predictor_results[i])
                      for i in range(len(url_ids))])
        return normalize_scores(scores)
