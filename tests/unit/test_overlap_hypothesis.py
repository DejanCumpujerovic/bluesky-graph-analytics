from hypothesis import given
from hypothesis import strategies as st

from bluesky_graph_analytics.domain.similarity.overlap import compute_overlap

_text_sets = st.sets(st.text(min_size=1, max_size=8), max_size=20)


@given(_text_sets, _text_sets)
def test_overlap_symmetric(a: set[str], b: set[str]) -> None:
    fa, fb = frozenset(a), frozenset(b)
    assert compute_overlap(fa, fb) == compute_overlap(fb, fa)


@given(st.sets(st.text(min_size=1, max_size=8), max_size=20))
def test_overlap_identity(a: set[str]) -> None:
    fa = frozenset(a)
    if not fa:
        assert compute_overlap(fa, fa) == 0.0
    else:
        assert compute_overlap(fa, fa) == 1.0


def test_overlap_bounds() -> None:
    assert 0.0 <= compute_overlap(frozenset("ab"), frozenset("cd")) <= 1.0
