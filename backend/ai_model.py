"""
AI Model Module - Dream AI System.

By default the app uses fast built-in fallbacks so first-run demos do not stall
while downloading large models. Set DREAMAI_ENABLE_TRANSFORMER=1 to opt into the
Hugging Face classifier.
"""

import os
from typing import Tuple, List

# We lazy-load these because they're slow to import
_classifier = None

USE_TRANSFORMER = os.environ.get('DREAMAI_ENABLE_TRANSFORMER', '').strip() == '1'


def _load_classifier():
    """Load or return cached emotion classifier."""
    global _classifier
    if not USE_TRANSFORMER:
        raise RuntimeError("Transformer classifier is disabled for stable local runs.")
    if _classifier is None:
        print("Loading emotion classifier (this may take a moment on first run)...")
        from transformers import pipeline
        _classifier = pipeline(
            'text-classification',
            model='bhadresh-savani/bert-base-uncased-emotion',
            return_all_scores=False  # we only need the top prediction
        )
        print("Classifier loaded.")
    return _classifier


# Mapping from model output labels to user-friendly labels
# The base model uses: sadness, joy, love, anger, fear, surprise
# We expand to include stress and anxiety using heuristic mapping
EMOTION_LABEL_MAP = {
    'sadness': 'sadness',
    'joy': 'happiness',
    'love': 'happiness',   # love maps to happiness for our purposes
    'anger': 'stress',     # anger in dreams often correlates with stress
    'fear': 'fear',
    'surprise': 'neutral', # surprise is ambiguous; map to neutral
}

# Keywords that suggest stress even if the model says something else
STRESS_KEYWORDS = {
    'exam', 'test', 'deadline', 'late', 'fail', 'failed', 'failing',
    'chase', 'chased', 'trapped', 'stuck', 'lost', 'confused', 'overwhelmed',
    'work', 'boss', 'assignment', 'forgot', 'missing', 'can\'t', 'unable'
}


def analyse_emotion(text: str) -> Tuple[str, float]:
    """
    Analyse the emotional content of a dream description.

    Args:
        text: The dream description (raw string from user).

    Returns:
        Tuple of (emotion_label: str, confidence: float)
        confidence is 0.0 to 1.0
    """
    if not text or len(text.strip()) < 5:
        return 'neutral', 0.5

    # Truncate to 512 tokens max (BERT limit) by characters first
    # Roughly 512 tokens ≈ 1800 characters for English text
    truncated = text[:1800]

    try:
        clf = _load_classifier()
        result = clf(truncated)[0]
        raw_label = result['label'].lower()
        confidence = float(result['score'])

        # Map to our label scheme
        emotion = EMOTION_LABEL_MAP.get(raw_label, 'neutral')

        # Override: if text contains multiple stress keywords, elevate to 'stress'
        # This is a simple heuristic augmentation
        text_lower = text.lower()
        stress_hit_count = sum(1 for kw in STRESS_KEYWORDS if kw in text_lower)
        if stress_hit_count >= 3 and emotion not in ('fear',):
            emotion = 'stress'
            # Slightly reduce confidence since we're overriding
            confidence = min(confidence, 0.75)

        return emotion, confidence

    except Exception as e:
        print(f"Classifier error: {e}")
        # Fallback: simple rule-based classification
        return _rule_based_fallback(text)


def extract_keywords(text: str, limit: int = 5) -> List[str]:
    """
    Extract a few representative keywords from a single dream.

    This keeps dream detail responses useful even when recurring pattern
    detection is only meaningful across multiple dreams.
    """
    if not text or not text.strip():
        return []

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer

        vectorizer = TfidfVectorizer(
            stop_words="english",
            token_pattern=r"\b[a-zA-Z]{3,}\b",
            ngram_range=(1, 2),
            max_features=max(limit * 3, 10),
        )
        matrix = vectorizer.fit_transform([text])
        scores = matrix.toarray()[0]
        features = vectorizer.get_feature_names_out()

        ranked = sorted(
            (
                (term, score)
                for term, score in zip(features, scores)
                if score > 0
            ),
            key=lambda item: item[1],
            reverse=True,
        )
        return [term for term, _ in ranked[:limit]]
    except Exception:
        return _simple_keyword_fallback(text, limit=limit)


def _rule_based_fallback(text: str) -> Tuple[str, float]:
    """
    Very simple rule-based fallback in case the model fails.
    Not accurate, just a safety net.
    """
    text_lower = text.lower()
    fear_words = {'afraid', 'scared', 'horror', 'monster', 'nightmare', 'dark', 'death', 'dying'}
    happy_words = {'happy', 'joy', 'love', 'beautiful', 'wonderful', 'laugh', 'smile', 'fun'}
    sad_words = {'sad', 'cry', 'crying', 'alone', 'lost', 'grief', 'miss', 'missing'}

    fear_score = sum(1 for w in fear_words if w in text_lower)
    happy_score = sum(1 for w in happy_words if w in text_lower)
    sad_score = sum(1 for w in sad_words if w in text_lower)
    stress_score = sum(1 for w in STRESS_KEYWORDS if w in text_lower)

    scores = {
        'fear': fear_score,
        'happiness': happy_score,
        'sadness': sad_score,
        'stress': stress_score
    }
    top_emotion = max(scores, key=scores.get)
    if scores[top_emotion] == 0:
        return 'neutral', 0.5
    return top_emotion, 0.65


def detect_patterns(dream_texts: List[str]) -> List[dict]:
    """
    Detect recurring symbols/themes across multiple dream entries.

    Uses TF-IDF to find tokens that are both frequent and distinctive
    across the corpus of a user's dreams.

    Args:
        dream_texts: List of raw dream text strings for a single user.

    Returns:
        List of dicts: [{'word': str, 'count': int, 'score': float}, ...]
        Sorted by TF-IDF score descending.
    """
    if len(dream_texts) < 2:
        return []  # Need at least 2 dreams to detect patterns

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np

        # We use a fairly aggressive stop word removal
        # Also filter very short tokens (< 3 chars)
        vectorizer = TfidfVectorizer(
            stop_words='english',
            min_df=2,           # must appear in at least 2 documents
            max_df=1.0 if len(dream_texts) < 3 else 0.9,
            # For tiny datasets, 0.9 can exclude every term.
            token_pattern=r'\b[a-zA-Z]{3,}\b',  # only alphabetic, min 3 chars
            ngram_range=(1, 2)  # include bigrams for things like "falling down"
        )

        tfidf_matrix = vectorizer.fit_transform(dream_texts)
        feature_names = vectorizer.get_feature_names_out()

        # Sum TF-IDF scores across all documents for each term
        scores_sum = np.asarray(tfidf_matrix.sum(axis=0)).flatten()

        # Count document frequency (how many dreams contain this word)
        doc_freq = np.asarray((tfidf_matrix > 0).sum(axis=0)).flatten()

        # Build result list, filter by doc frequency >= 2
        results = []
        for i, (term, score, freq) in enumerate(zip(feature_names, scores_sum, doc_freq)):
            if freq >= 2:
                results.append({
                    'word': term,
                    'count': int(freq),
                    'score': round(float(score), 4)
                })

        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:15]  # top 15

    except Exception as e:
        print(f"Pattern detection error: {e}")
        # Fallback: simple word frequency count
        return _simple_frequency_fallback(dream_texts)


def _simple_frequency_fallback(texts: List[str]) -> List[dict]:
    """Very basic word frequency fallback."""
    from collections import Counter
    import re

    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
                  'for', 'of', 'with', 'i', 'was', 'is', 'it', 'my', 'me', 'we',
                  'had', 'have', 'he', 'she', 'they', 'then', 'that', 'this', 'were'}

    all_words = []
    for text in texts:
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        all_words.extend([w for w in words if w not in stop_words])

    counter = Counter(all_words)
    results = [{'word': word, 'count': count, 'score': float(count)}
               for word, count in counter.most_common(15) if count >= 2]
    return results


def _simple_keyword_fallback(text: str, limit: int = 5) -> List[str]:
    """Extract keywords from one text without external dependencies."""
    import re
    from collections import Counter

    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
        'for', 'of', 'with', 'i', 'was', 'is', 'it', 'my', 'me', 'we',
        'had', 'have', 'he', 'she', 'they', 'then', 'that', 'this', 'were',
        'there', 'from', 'into', 'about', 'through', 'when', 'what', 'where'
    }

    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered = [word for word in words if word not in stop_words]
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(limit)]


# ---- Quick test when run directly ----
if __name__ == '__main__':
    test_dream = ("I was running through a dark corridor trying to reach an exam room "
                  "but I kept getting lost. The walls were closing in and I couldn't find "
                  "the door. Everyone else seemed to know where to go except me.")
    emotion, conf = analyse_emotion(test_dream)
    print(f"Emotion: {emotion} ({conf*100:.1f}% confidence)")

    dreams = [
        test_dream,
        "I was falling from a tall building and woke up right before hitting the ground. Very frightening.",
        "I was running late for a presentation and couldn't find my notes anywhere.",
        "Someone was chasing me through a forest and I couldn't run fast enough to escape.",
    ]
    patterns = detect_patterns(dreams)
    print("Recurring patterns:", patterns[:5])
