"""Unit tests for sitemap/RSS generation and pagination URL helpers."""

import datetime as dt
import re
import xml.etree.ElementTree as etree
from pathlib import Path

import pytest

import main

pytestmark = pytest.mark.unit


def test_build_sitemap_is_valid_xml() -> None:
    xml_text = main.build_sitemap(["/", "/blog/", "/blog/post-one/"])
    root = etree.fromstring(xml_text)
    assert root.tag.endswith("urlset")
    locs = [loc.text for loc in root.iter() if loc.tag.endswith("loc")]
    assert f"{main.SITE_URL}/" in locs
    assert f"{main.SITE_URL}/blog/post-one/" in locs


def test_build_sitemap_absolute_urls() -> None:
    xml_text = main.build_sitemap(["/projects/"])
    assert f"{main.SITE_URL}/projects/" in xml_text


def test_build_sitemap_empty() -> None:
    xml_text = main.build_sitemap([])
    root = etree.fromstring(xml_text)
    assert list(root) == []


def test_build_sitemap_dict_entries_emit_lastmod_and_changefreq() -> None:
    xml_text = main.build_sitemap([{"url": "/blog/post-one/", "lastmod": "2026-05-29", "changefreq": "yearly"}])
    root = etree.fromstring(xml_text)
    url_node = next(node for node in root if node.tag.endswith("url"))
    lastmod = next(child for child in url_node if child.tag.endswith("lastmod"))
    changefreq = next(child for child in url_node if child.tag.endswith("changefreq"))
    assert lastmod.text == "2026-05-29"
    assert changefreq.text == "yearly"


def test_build_sitemap_dict_without_optional_fields() -> None:
    xml_text = main.build_sitemap([{"url": "/projects/"}])
    root = etree.fromstring(xml_text)
    url_node = next(node for node in root if node.tag.endswith("url"))
    children = [child.tag.split("}")[-1] for child in url_node]
    assert children == ["loc"]


def test_build_sitemap_mixes_str_and_dict_entries() -> None:
    xml_text = main.build_sitemap(["/", {"url": "/blog/x/", "lastmod": "2026-01-01"}])
    assert f"{main.SITE_URL}/" in xml_text
    assert f"{main.SITE_URL}/blog/x/" in xml_text
    assert "2026-01-01" in xml_text


def test_render_rss_is_valid_xml(post_factory) -> None:
    posts = [
        post_factory(slug="newest", date=dt.date(2024, 6, 1), title="Newest"),
        post_factory(slug="older", date=dt.date(2024, 1, 1), title="Older"),
    ]
    rss = main.render_rss(posts)
    root = etree.fromstring(rss)
    assert root.tag == "rss"
    titles = [t.text for t in root.iter("title")]
    assert "Newest" in titles
    assert "Older" in titles


def test_render_rss_escapes_html(post_factory) -> None:
    post = post_factory(slug="x", title="A & B <script>", description="1 < 2 & 3")
    rss = main.render_rss([post])
    # Raw markup may only appear inside content:encoded CDATA blocks.
    outside_cdata = re.sub(r"<!\[CDATA\[.*?\]\]>", "", rss, flags=re.DOTALL)
    assert "<script>" not in outside_cdata
    assert "A &amp; B" in rss


def test_render_rss_limits_to_20(post_factory) -> None:
    posts = [post_factory(slug=str(i), date=dt.date(2024, 1, 1) + dt.timedelta(days=i)) for i in range(30)]
    rss = main.render_rss(posts)
    assert rss.count("<item>") == 20


def test_render_rss_empty_has_build_date() -> None:
    rss = main.render_rss([])
    root = etree.fromstring(rss)
    assert root.find("./channel/lastBuildDate") is not None


def test_render_rss_includes_author_creator(post_factory) -> None:
    rss = main.render_rss([post_factory(slug="x")])
    root = etree.fromstring(rss)
    creators = list(root.iter("{http://purl.org/dc/elements/1.1/}creator"))
    assert creators, "expected dc:creator element"
    assert creators[0].text == main.AUTHOR


def test_render_rss_includes_categories(post_factory) -> None:
    post = post_factory(slug="x", categories=["AI"], tags=["RAG", "Azure"])
    rss = main.render_rss([post])
    root = etree.fromstring(rss)
    categories = [node.text for node in root.iter("category")]
    assert categories == ["AI", "RAG", "Azure"]


def test_render_rss_category_domains_link_to_taxonomy_pages(post_factory) -> None:
    post = post_factory(slug="x", categories=["AI"], tags=["Azure ML"])
    rss = main.render_rss([post])
    root = etree.fromstring(rss)
    domains = [node.get("domain") for node in root.iter("category")]
    assert f"{main.SITE_URL}/blog/category/ai/" in domains
    assert f"{main.SITE_URL}/blog/tag/azure-ml/" in domains


def test_render_rss_includes_content_encoded(post_factory) -> None:
    post = post_factory(slug="x", title="Hello")
    rss = main.render_rss([post])
    assert "<content:encoded><![CDATA[<p>Hello</p>]]></content:encoded>" in rss


def test_render_rss_includes_media_image_when_social_card_set(post_factory) -> None:
    post = post_factory(slug="x")
    post.social_card_url = "/assets/social/blog-x.png"
    rss = main.render_rss([post])
    assert f'<media:content url="{main.SITE_URL}/assets/social/blog-x.png"' in rss
    rss_without_card = main.render_rss([post_factory(slug="y")])
    assert "<media:content" not in rss_without_card


def test_render_rss_channel_metadata(post_factory) -> None:
    rss = main.render_rss([post_factory(slug="x")])
    root = etree.fromstring(rss)
    assert root.find("./channel/copyright") is not None
    assert root.find("./channel/ttl") is not None
    assert root.find("./channel/pubDate") is not None
    image = root.find("./channel/image")
    assert image is not None
    assert image.findtext("url", "").endswith(".png")


def test_render_rss_atom_updated_only_for_updated_posts(post_factory) -> None:
    updated = post_factory(slug="u", date=dt.date(2024, 1, 1), updated=dt.date(2024, 6, 1))
    fresh = post_factory(slug="f", date=dt.date(2024, 1, 1))
    rss = main.render_rss([updated, fresh])
    assert rss.count("<atom:updated>") == 1


def test_build_sitemap_emits_image_extension() -> None:
    xml_text = main.build_sitemap([{"url": "/blog/x/", "image": "/assets/social/blog-x.png"}])
    root = etree.fromstring(xml_text)
    image_ns = "{http://www.google.com/schemas/sitemap-image/1.1}"
    locs = [node.text for node in root.iter(f"{image_ns}loc")]
    assert locs == [f"{main.SITE_URL}/assets/social/blog-x.png"]


def test_render_rss_self_link_and_namespaces(post_factory) -> None:
    rss = main.render_rss([post_factory(slug="x")])
    assert 'xmlns:dc="http://purl.org/dc/elements/1.1/"' in rss
    atom_link = f'<atom:link href="{main.SITE_URL}/rss.xml"'
    assert atom_link in rss


@pytest.mark.parametrize(
    ("page_number", "expected_url"),
    [
        (1, "/blog/"),
        (0, "/blog/"),
        (2, "/blog/page/2/"),
        (5, "/blog/page/5/"),
    ],
)
def test_blog_index_url(page_number: int, expected_url: str) -> None:
    assert main.blog_index_url(page_number) == expected_url


@pytest.mark.parametrize(
    ("page_number", "expected_suffix"),
    [
        (1, Path("blog") / "index.html"),
        (2, Path("blog") / "page" / "2" / "index.html"),
        (3, Path("blog") / "page" / "3" / "index.html"),
    ],
)
def test_blog_index_output_path(page_number: int, expected_suffix: Path) -> None:
    result = main.blog_index_output_path(page_number)
    assert result == main.SITE_DIR / expected_suffix
