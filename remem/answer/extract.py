"""R6 — pull the object out of a question with plain regexes (no model).

"Where are my keys?"                → find   "keys"       → "a photo of keys"
"Where are the sunglasses?"         → find   "sunglasses"
"When was I at the whiteboard?"     → recall "whiteboard"
"""

import re

from remem import config
from remem.contracts import Query

_DET = r"(?:(?:my|the|your|our|a|an|this|that)\s+)?"

_RECALL = re.compile(
    rf"\bwhen\s+(?:was|were)\s+i\s+(?:at|by|near|next\s+to|in\s+front\s+of|in)\s+{_DET}(?P<obj>.+)"
)
_FIND = [
    re.compile(rf"\bwhere\s+did\s+i\s+(?:leave|put|last\s+see|see|drop|set)\s+{_DET}(?P<obj>.+)"),
    re.compile(rf"\bwhere(?:'s|s|\s+is|\s+are|\s+was|\s+were)\s+{_DET}(?P<obj>.+)"),
    re.compile(rf"\b(?:have|did)\s+you\s+(?:seen|see)\s+{_DET}(?P<obj>.+)"),
    re.compile(rf"\b(?:find|locate|show\s+me)\s+{_DET}(?P<obj>.+)"),
]

# Dictation and speech pad the end of a question: "where's my mug now", "... at".
_TRAILING = re.compile(r"\s+(?:now|again|today|please|at|last|lately|recently|anywhere)$")
_LEADING_DET = re.compile(r"^(?:my|the|your|our|a|an|this|that)(?:\s+|$)")

# Fallback when no pattern matches: drop question words, keep what's left.
_STOPWORDS = {
    "where", "wheres", "is", "are", "was", "were", "my", "the", "your", "our", "a", "an",
    "did", "do", "i", "you", "have", "seen", "see", "can", "could", "find", "me", "please",
    "what", "about", "it", "know", "leave", "left", "put", "when", "at", "now", "hey", "s",
}


def _normalize(q: str) -> str:
    q = q.lower().replace("’", "'").replace("‘", "'")  # iOS smart quotes
    q = re.sub(r"[^\w\s'-]", " ", q)
    return re.sub(r"\s+", " ", q).strip()


def _clean(obj: str) -> str:
    obj = obj.strip(" '-")
    while (trimmed := _TRAILING.sub("", obj)) != obj:
        obj = trimmed
    return _LEADING_DET.sub("", obj).strip(" '-")


def extract(q: str) -> Query | None:
    """Return the Query to embed, or None when no object can be found."""
    text = _normalize(q)
    if m := _RECALL.search(text):
        obj = _clean(m["obj"])
        return Query(kind="recall", object=obj, text=config.QUERY_TEMPLATE.format(X=obj)) if obj else None
    for pattern in _FIND:
        if m := pattern.search(text):
            obj = _clean(m["obj"])
            if obj:
                return Query(kind="find", object=obj, text=config.QUERY_TEMPLATE.format(X=obj))
    obj = _clean(" ".join(w for w in text.replace("'", " ").split() if w not in _STOPWORDS))
    return Query(kind="find", object=obj, text=config.QUERY_TEMPLATE.format(X=obj)) if obj else None
