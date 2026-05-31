"""Unit tests for blog-archive grouping and the search index."""

import datetime as dt

import pytest

import main

pytestmark = pytest.mark.unit


@pytest.fixture
def sample_posts(post_factory):
    return [
        post_factory(slug="jan-2024", date=dt.date(2024, 1, 10), title="Jan 2024"),
        post_factory(slug="jan-2024-b", date=dt.date(2024, 1, 20), title="Jan 2024 B"),
        post_factory(slug="mar-2024", date=dt.date(2024, 3, 5), title="Mar 2024"),
        post_factory(slug="dec-2023", date=dt.date(2023, 12, 1), title="Dec 2023"),
    ]


def test_archive_groups_by_year_descending(sample_posts) -> None:
    archive = main.build_blog_archive(sample_posts)
    years = [entry["year"] for entry in archive]
    assert years == [2024, 2023]


def test_archive_year_counts(sample_posts) -> None:
    archive = main.build_blog_archive(sample_posts)
    by_year = {entry["year"]: entry["count"] for entry in archive}
    assert by_year == {2024: 3, 2023: 1}


def test_archive_months_descending_with_names(sample_posts) -> None:
    archive = main.build_blog_archive(sample_posts)
    year_2024 = next(entry for entry in archive if entry["year"] == 2024)
    months = [(m["month"], m["month_name"]) for m in year_2024["months"]]
    assert months == [(3, "March"), (1, "January")]


def test_archive_active_url_marks_open(sample_posts) -> None:
    archive = main.build_blog_archive(sample_posts, active_url="/blog/mar-2024/")
    year_2024 = next(entry for entry in archive if entry["year"] == 2024)
    march = next(m for m in year_2024["months"] if m["month"] == 3)
    january = next(m for m in year_2024["months"] if m["month"] == 1)
    assert year_2024["open"] is True
    assert march["open"] is True
    assert january["open"] is False


def test_archive_no_active_url_all_closed(sample_posts) -> None:
    archive = main.build_blog_archive(sample_posts)
    assert all(entry["open"] is False for entry in archive)
    assert all(month["open"] is False for entry in archive for month in entry["months"])


def test_archive_empty_posts() -> None:
    assert main.build_blog_archive([]) == []


def test_search_index_includes_pages_and_posts(post_factory) -> None:
    page = main.Page(
        title="Projects",
        description="My projects",
        url="/projects/",
        template="projects.html",
        output_path=main.SITE_DIR / "projects" / "index.html",
        body_markdown="Some project text.",
    )
    posts = [post_factory(slug="a", tags=["python"], categories=["Cloud"])]
    records = main.build_search_index([page], posts)

    kinds = {record["kind"] for record in records}
    assert kinds == {"page", "post"}

    post_record = next(r for r in records if r["kind"] == "post")
    assert post_record["tags"] == ["python"]
    assert post_record["categories"] == ["Cloud"]
    assert "date" in post_record


def test_search_index_truncates_body(post_factory) -> None:
    long_post = post_factory(slug="long")
    long_post.body_markdown = "word " * 500
    records = main.build_search_index([], [long_post])
    assert len(records[0]["text"]) <= 500
