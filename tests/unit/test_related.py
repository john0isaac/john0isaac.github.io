"""Unit tests for related-post scoring and selection."""

import datetime as dt

import pytest

import main

pytestmark = pytest.mark.unit


def test_similarity_shared_tags_scores_higher(post_factory) -> None:
    base = post_factory(slug="a", tags=["python", "ai"])
    similar = post_factory(slug="b", tags=["python", "ai"])
    different = post_factory(slug="c", tags=["cooking"])
    assert main.post_similarity(base, similar) > main.post_similarity(base, different)


def test_similarity_shared_categories(post_factory) -> None:
    base = post_factory(slug="a", categories=["Cloud"])
    same = post_factory(slug="b", categories=["Cloud"])
    none = post_factory(slug="c", categories=["Food"])
    assert main.post_similarity(base, same) > main.post_similarity(base, none)


@pytest.mark.parametrize(
    ("day_gap", "min_expected"),
    [
        (0, 0),
        (10, 10),
        (90, 5),
        (365, 0),
    ],
)
def test_similarity_date_proximity(post_factory, day_gap: int, min_expected: int) -> None:
    base = post_factory(slug="a", date=dt.date(2024, 6, 1))
    other = post_factory(slug="b", date=dt.date(2024, 6, 1) + dt.timedelta(days=day_gap))
    assert main.post_similarity(base, other) >= min_expected


def test_similarity_shared_authors_bonus(post_factory) -> None:
    base = post_factory(slug="a", authors=["john"], date=dt.date(2020, 1, 1))
    shared = post_factory(slug="b", authors=["john"], date=dt.date(2024, 1, 1))
    none = post_factory(slug="c", authors=["jane"], date=dt.date(2024, 1, 1))
    assert main.post_similarity(base, shared) > main.post_similarity(base, none)


def test_related_posts_excludes_self(post_factory) -> None:
    base = post_factory(slug="a", tags=["x"])
    others = [base, post_factory(slug="b", tags=["x"]), post_factory(slug="c", tags=["x"])]
    related = main.related_posts_for(base, others)
    assert all(p.slug != "a" for p in related)


def test_related_posts_respects_limit(post_factory) -> None:
    base = post_factory(slug="a", tags=["x"])
    pool = [base] + [post_factory(slug=str(i), tags=["x"]) for i in range(10)]
    assert len(main.related_posts_for(base, pool, limit=3)) == 3


def test_related_posts_fallback_when_no_overlap(post_factory) -> None:
    """With zero similarity, it still returns recent posts as a fallback."""
    base = post_factory(slug="a", tags=["unique"])
    pool = [base, post_factory(slug="b", tags=["nothing"]), post_factory(slug="c", tags=["else"])]
    related = main.related_posts_for(base, pool, limit=2)
    assert len(related) == 2
    assert all(p.slug != "a" for p in related)


def test_related_posts_orders_by_score(post_factory) -> None:
    base = post_factory(slug="a", tags=["python", "ai"], categories=["Cloud"])
    strong = post_factory(slug="strong", tags=["python", "ai"], categories=["Cloud"])
    weak = post_factory(slug="weak", tags=["python"])
    pool = [base, weak, strong]
    related = main.related_posts_for(base, pool)
    assert related[0].slug == "strong"
