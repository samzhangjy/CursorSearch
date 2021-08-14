import jieba

def seperate_words(text: str) -> list:
    results = jieba.lcut_for_search(text)
    return results

def dtanh(y):
    return 1.0 - y * y

def normalize_scores(scores: dict, smallIsBetter=False):
    vsmall = 1e-5
    if smallIsBetter:
        min_score = min(scores.values())
        return dict([(u, float(min_score) / max(vsmall, l)) for (u, l) in scores.items()])
    else:
        max_score = max(scores.values())
        if max_score == 0:
            max_score = vsmall
        return dict([(u, float(c) / max_score) for (u, c) in scores.items()])
