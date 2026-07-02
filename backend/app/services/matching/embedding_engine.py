"""Semantic similarity between resume and JD.

Primary backend: sentence-transformers (all-mpnet-base-v2 or BGE), loaded
lazily on first use. If the package isn't installed, falls back to TF-IDF
cosine similarity (scikit-learn) so the platform stays functional; the active
backend is reported in the analysis metadata.
"""
from __future__ import annotations

import logging
import math
import threading

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_st_model = None
_st_failed = False


def _get_st_model():
    global _st_model, _st_failed
    if _st_model is not None or _st_failed:
        return _st_model
    with _lock:
        if _st_model is not None or _st_failed:
            return _st_model
        try:
            from sentence_transformers import SentenceTransformer

            name = get_settings().embedding_model
            logger.info("Loading sentence-transformers model %s ...", name)
            _st_model = SentenceTransformer(name)
        except Exception as exc:  # not installed / download failed
            logger.warning("sentence-transformers unavailable (%s); using TF-IDF fallback", exc)
            _st_failed = True
    return _st_model


def backend_name() -> str:
    return "sentence-transformers" if _get_st_model() is not None else "tfidf"


def similarity_matrix(texts_a: list[str], texts_b: list[str]) -> list[list[float]]:
    """Cosine similarity for every pair (a, b). Values in [-1, 1]."""
    model = _get_st_model()
    if model is not None:
        import numpy as np

        emb = model.encode(texts_a + texts_b, normalize_embeddings=True)
        a, b = emb[: len(texts_a)], emb[len(texts_a):]
        return (a @ b.T).tolist()
    return _tfidf_similarity(texts_a, texts_b)


def _tfidf_similarity(texts_a: list[str], texts_b: list[str]) -> list[list[float]]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    matrix = vec.fit_transform(texts_a + texts_b)
    a, b = matrix[: len(texts_a)], matrix[len(texts_a):]
    return cosine_similarity(a, b).tolist()


def similarity(text_a: str, text_b: str) -> float:
    if not text_a.strip() or not text_b.strip():
        return 0.0
    return float(similarity_matrix([text_a], [text_b])[0][0])


def calibrate(cosine: float) -> float:
    """Map raw cosine similarity to an intuitive 0–100 score.

    Raw cosines cluster in a narrow band (ST: ~0.2–0.8 for related docs;
    TF-IDF lower still). A logistic curve centred per backend spreads that
    band across the score range without hard clipping.
    """
    midpoint = 0.45 if backend_name() == "sentence-transformers" else 0.22
    steepness = 8.0
    score = 100.0 / (1.0 + math.exp(-steepness * (cosine - midpoint)))
    return round(score, 1)
