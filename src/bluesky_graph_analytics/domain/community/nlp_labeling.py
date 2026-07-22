"""Community labeling via c-TF-IDF on English descriptions (DEO 8.2)."""

from __future__ import annotations

import re
from collections import Counter

from langdetect import detect_langs
from langdetect.lang_detect_exception import LangDetectException
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

from bluesky_graph_analytics.domain.models import Profile

_HASHTAG = re.compile(r"#\w+")
_URL_MENTION = re.compile(r"https?://\S+|@\w+")


def preprocess_description(text: str) -> str:
    t = text.lower()
    t = _URL_MENTION.sub(" ", t)
    t = _HASHTAG.sub(lambda m: m.group(0)[1:], t)
    return " ".join(t.split())


def profile_language_ok(
    profile: Profile,
    *,
    threshold: float,
    target: str = "en",
) -> tuple[bool, str, float]:
    if not profile.description or not profile.description.strip():
        return False, "unknown", 0.0
    try:
        langs = detect_langs(profile.description)
    except LangDetectException:
        return False, "unknown", 0.0
    if not langs:
        return False, "unknown", 0.0
    top = langs[0]
    if top.lang == target and top.prob >= threshold:
        return True, top.lang, float(top.prob)
    return False, "unknown", float(top.prob)


def community_top_terms(
    profiles: list[Profile],
    *,
    lang_threshold: float,
    top_n: int = 10,
) -> tuple[tuple[str, ...], dict[str, int]]:
    docs: list[str] = []
    lang_dist: Counter[str] = Counter()
    for p in profiles:
        ok, lang, _conf = profile_language_ok(p, threshold=lang_threshold)
        lang_dist[lang] += 1
        if not ok or not p.description:
            continue
        docs.append(preprocess_description(p.description))

    if not docs:
        return (), dict(lang_dist)

    corpus = " ".join(docs)
    try:
        import nltk
        from nltk.corpus import stopwords

        try:
            stops = set(stopwords.words("english"))
        except LookupError:
            nltk.download("stopwords", quiet=True)
            stops = set(stopwords.words("english"))
    except Exception:  # noqa: BLE001
        stops = set()

    vectorizer = CountVectorizer(
        stop_words=list(stops),
        token_pattern=r"(?u)\b\w{2,}\b",
        max_features=5000,
    )
    try:
        counts = vectorizer.fit_transform([corpus])
    except ValueError:
        # empty vocabulary after stopword filtering
        return (), dict(lang_dist)
    if counts.shape[1] == 0:
        return (), dict(lang_dist)
    tfidf = TfidfTransformer()
    matrix = tfidf.fit_transform(counts)
    terms = vectorizer.get_feature_names_out()
    scores = matrix.toarray()[0]
    ranked = sorted(zip(terms, scores, strict=False), key=lambda x: -x[1])
    top = tuple(t for t, _s in ranked[:top_n])
    return top, dict(lang_dist)
