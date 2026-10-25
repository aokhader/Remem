"""R6 object extraction (Varick). S0 stub: only "where is/are my X" (contracts.md → Functions)."""

import re

from remem import config
from remem.contracts import Query


def extract(q: str) -> Query | None:
    m = re.search(r"where (is|are) my (.+?)\??$", q.strip().lower())
    if m is None:
        return None
    return Query(kind="find", object=m.group(2), text=config.QUERY_TEMPLATE.format(X=m.group(2)))
