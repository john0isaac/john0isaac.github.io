"""Static site generator for johnaziz.org."""

import argparse
import datetime as dt
import functools
import html
import http.server
import json
import math
import re
import shutil
import socketserver
import xml.etree.ElementTree as etree
from email.utils import format_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from scripts.constants import (
    ASSETS_DIR,
    AUTHOR,
    AUTHOR_BIO,
    AUTHOR_IMAGE,
    AUTHOR_JOB_TITLE,
    BLOG_POSTS_PER_PAGE,
    DATA_DIR,
    DATE_PREFIX_RE,
    EXCERPT_MARKER,
    FRONT_MATTER_RE,
    MARKDOWN_EXTENSIONS,
    ROOT_DIR,
    SAME_AS_LINKS,
    SITE_DIR,
    SITE_NAME,
    SITE_URL,
    SRC_DIR,
    TEMPLATES_DIR,
    TWITTER_HANDLE,
    VENDOR_DIR,
)
from scripts.gitinfo import git_last_modified_date
from scripts.minify import minify_site
from scripts.models import Page, Post
from scripts.optimize import optimize_site
from scripts.social import generate_social_cards


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build the static site")
    build_parser.add_argument("--no-minify", action="store_true", help="Skip HTML/CSS/JS minification")
    build_parser.add_argument("--no-optimize", action="store_true", help="Skip image optimization")
    subparsers.add_parser("clean", help="Delete generated site output")
    serve_parser = subparsers.add_parser("serve", help="Build and serve the site")
    serve_parser.add_argument("--port", type=int, default=8000, help="Local HTTP port")
    serve_parser.add_argument("--no-minify", action="store_true", help="Skip HTML/CSS/JS minification")
    serve_parser.add_argument("--no-optimize", action="store_true", help="Skip image optimization")
    return parser.parse_args()


@functools.lru_cache(maxsize=1)
def markdown_engine() -> markdown.Markdown:
    return markdown.Markdown(extensions=MARKDOWN_EXTENSIONS, output_format="html")


def render_markdown(text: str) -> str:
    engine = markdown_engine()
    engine.reset()
    if not text.strip():
        return ""
    return engine.convert(text)


def parse_document(path: Path) -> tuple[dict[str, Any], str]:
    raw_text = path.read_text(encoding="utf-8")
    match = FRONT_MATTER_RE.match(raw_text)
    if not match:
        return {}, raw_text

    metadata = yaml.safe_load(match.group(1)) or {}
    body = raw_text[match.end() :]
    return metadata, body


def ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    ensure_directory(path)
    path.write_text(content, encoding="utf-8")


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or []


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return re.sub(r"-+", "-", normalized).strip("-")


def plain_text_from_markdown(text: str) -> str:
    html_text = render_markdown(text)
    without_tags = re.sub(r"<[^>]+>", " ", html_text)
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def estimate_read_time_minutes(text: str, words_per_minute: int = 200) -> int:
    words = re.findall(r"\b\w+\b", plain_text_from_markdown(text))
    if not words:
        return 1
    return max(1, (len(words) + words_per_minute - 1) // words_per_minute)


def load_authors(path: Path) -> dict[str, dict[str, str]]:
    raw = load_yaml(path)
    if not isinstance(raw, dict):
        return {}
    authors = raw.get("authors")
    if not isinstance(authors, dict):
        return {}

    normalized: dict[str, dict[str, str]] = {}
    for author_id, details in authors.items():
        if not isinstance(details, dict):
            continue
        normalized[str(author_id)] = {
            "id": str(author_id),
            "name": str(details.get("name", author_id)),
            "description": str(details.get("description", "")),
            "avatar": str(details.get("avatar", "")),
            "url": str(details.get("url", "")),
        }
    return normalized


def resolve_post_authors(author_ids: list[str], authors_lookup: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    resolved: list[dict[str, str]] = []
    for author_id in author_ids:
        author_key = str(author_id)
        profile = authors_lookup.get(author_key)
        if profile:
            resolved.append(profile)
            continue
        resolved.append(
            {
                "id": author_key,
                "name": author_key,
                "description": "",
                "avatar": "",
                "url": "",
            }
        )
    return resolved


def split_excerpt(body: str) -> tuple[str, str]:
    if EXCERPT_MARKER in body:
        excerpt, remainder = body.split(EXCERPT_MARKER, maxsplit=1)
        return excerpt.strip(), f"{excerpt.strip()}\n\n{remainder.strip()}".strip()

    paragraphs = [part.strip() for part in body.split("\n\n") if part.strip()]
    excerpt = paragraphs[0] if paragraphs else ""
    return excerpt, body.strip()


def date_from_value(value: Any) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        return dt.date.fromisoformat(value)
    raise ValueError(f"Unsupported date value: {value!r}")


def post_slug(source_path: Path, metadata: dict[str, Any]) -> str:
    explicit_slug = metadata.get("slug")
    if explicit_slug:
        return slugify(str(explicit_slug))

    stem = source_path.stem
    match = DATE_PREFIX_RE.match(stem)
    if match:
        return slugify(match.group(4))
    return slugify(stem)


def collect_posts() -> list[Post]:
    posts: list[Post] = []
    for source_path in sorted((SRC_DIR / "blog" / "posts").rglob("*.md")):
        metadata, body = parse_document(source_path)
        excerpt_markdown, full_markdown = split_excerpt(body)
        slug = post_slug(source_path, metadata)
        post_date = date_from_value(metadata["date"])
        updated_meta = metadata.get("updated")
        if updated_meta is not None:
            updated: dt.date | None = date_from_value(updated_meta)
        else:
            updated = git_last_modified_date(source_path)
            if not updated:
                updated = post_date
        url = f"/blog/{slug}/"
        posts.append(
            Post(
                title=str(metadata["title"]),
                description=str(metadata.get("description", "")),
                date=post_date,
                slug=slug,
                url=url,
                output_path=SITE_DIR / "blog" / slug / "index.html",
                content_html=render_markdown(full_markdown),
                excerpt_html=render_markdown(excerpt_markdown),
                body_markdown=full_markdown,
                categories=list(metadata.get("categories", [])),
                tags=list(metadata.get("tags", [])),
                authors=list(metadata.get("authors", [])),
                read_time_minutes=estimate_read_time_minutes(full_markdown),
                updated=updated,
                metadata=metadata,
                source_path=source_path,
            )
        )
    return sorted(posts, key=lambda item: item.date, reverse=True)


def load_page(source_path: Path, url: str, template: str, output_path: Path) -> Page:
    metadata, body = parse_document(source_path)
    return Page(
        title=str(metadata.get("title", "")),
        description=str(metadata.get("description", "")),
        url=url,
        template=template,
        output_path=output_path,
        content_html=render_markdown(body),
        body_markdown=body,
        metadata=metadata,
    )


def site_navigation() -> list[dict[str, str]]:
    return [
        {"title": "Home", "url": "/"},
        {"title": "Blog", "url": "/blog/"},
        {"title": "Projects", "url": "/projects/"},
        {"title": "Talks", "url": "/talks/"},
    ]


def base_context() -> dict[str, Any]:
    return {
        "site_name": SITE_NAME,
        "site_url": SITE_URL,
        "author_name": AUTHOR,
        "author_bio": AUTHOR_BIO,
        "author_job_title": AUTHOR_JOB_TITLE,
        "author_image": AUTHOR_IMAGE,
        "twitter_handle": TWITTER_HANDLE,
        "same_as_links": SAME_AS_LINKS,
        "navigation": site_navigation(),
        "current_year": dt.date.today().year,
    }


def build_search_index(pages: list[Page], posts: list[Post]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for page in pages:
        body_text = plain_text_from_markdown(page.body_markdown)[:500]
        records.append(
            {
                "kind": "page",
                "title": page.title,
                "url": page.url,
                "description": page.description,
                "text": body_text,
                "tags": [],
                "categories": [],
            }
        )

    for post in posts:
        body_text = plain_text_from_markdown(post.body_markdown)[:500]
        records.append(
            {
                "kind": "post",
                "title": post.title,
                "url": post.url,
                "description": post.description,
                "text": body_text,
                "tags": post.tags,
                "categories": post.categories,
                "date": post.date.isoformat(),
            }
        )
    return records


def post_similarity(left: Post, right: Post) -> int:
    score = 0
    shared_tags = set(left.tags) & set(right.tags)
    shared_categories = set(left.categories) & set(right.categories)
    if shared_tags:
        score += 20 * len(shared_tags)
    if shared_categories:
        score += 12 * len(shared_categories)

    day_distance = abs((left.date - right.date).days)
    if day_distance == 0:
        score += 0
    elif day_distance < 30:
        score += 10
    elif day_distance < 180:
        score += 5

    if left.authors and right.authors and set(left.authors) & set(right.authors):
        score += 4
    return score


def related_posts_for(post: Post, all_posts: list[Post], limit: int = 3) -> list[Post]:
    scored_posts = [
        (candidate, post_similarity(post, candidate)) for candidate in all_posts if candidate.slug != post.slug
    ]
    scored_posts.sort(key=lambda item: (item[1], item[0].date), reverse=True)
    return [candidate for candidate, score in scored_posts if score > 0][:limit] or [
        candidate for candidate in all_posts if candidate.slug != post.slug
    ][:limit]


def build_blog_archive(posts: list[Post], active_url: str | None = None) -> list[dict[str, Any]]:
    grouped: dict[int, dict[int, list[Post]]] = {}
    for post in posts:
        grouped.setdefault(post.date.year, {}).setdefault(post.date.month, []).append(post)

    archive: list[dict[str, Any]] = []
    for year in sorted(grouped.keys(), reverse=True):
        month_groups = grouped[year]
        months: list[dict[str, Any]] = []
        year_has_active = False

        for month in sorted(month_groups.keys(), reverse=True):
            month_posts = sorted(month_groups[month], key=lambda item: item.date, reverse=True)
            month_has_active = any(post.url == active_url for post in month_posts)
            year_has_active = year_has_active or month_has_active
            months.append(
                {
                    "month": month,
                    "month_name": dt.date(2000, month, 1).strftime("%B"),
                    "count": len(month_posts),
                    "open": month_has_active,
                    "posts": [{"title": post.title, "url": post.url} for post in month_posts],
                }
            )

        archive.append(
            {
                "year": year,
                "count": sum(month["count"] for month in months),
                "open": year_has_active,
                "months": months,
            }
        )

    return archive


def build_sitemap(urls: list[Any]) -> str:
    root = etree.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for entry in urls:
        if isinstance(entry, str):
            url, lastmod, changefreq = entry, None, None
        else:
            url = entry.get("url")
            lastmod = entry.get("lastmod")
            changefreq = entry.get("changefreq")
        url_node = etree.SubElement(root, "url")
        loc_node = etree.SubElement(url_node, "loc")
        loc_node.text = urljoin(f"{SITE_URL}/", url.lstrip("/"))
        if lastmod:
            etree.SubElement(url_node, "lastmod").text = lastmod
        if changefreq:
            etree.SubElement(url_node, "changefreq").text = changefreq
    return etree.tostring(root, encoding="unicode", xml_declaration=True)


def render_rss(posts: list[Post]) -> str:
    items: list[str] = []
    for post in posts[:20]:
        description = html.escape(post.description or plain_text_from_markdown(post.body_markdown)[:180])
        item_lines = [
            "    <item>",
            f"      <title>{html.escape(post.title)}</title>",
            f"      <link>{post.absolute_url}</link>",
            f"      <guid>{post.absolute_url}</guid>",
            f"      <pubDate>{post.rss_date}</pubDate>",
            f"      <dc:creator>{html.escape(AUTHOR)}</dc:creator>",
        ]
        for category in post.categories + post.tags:
            item_lines.append(f"      <category>{html.escape(str(category))}</category>")
        item_lines.append(f"      <description>{description}</description>")
        item_lines.append("    </item>")
        items.append("\n".join(item_lines))

    last_build = posts[0].rss_date if posts else format_datetime(dt.datetime.now(dt.UTC))
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:atom="http://www.w3.org/2005/Atom">',
            "  <channel>",
            f"    <title>{html.escape(SITE_NAME)}</title>",
            f"    <link>{SITE_URL}</link>",
            f'    <atom:link href="{SITE_URL}/rss.xml" rel="self" type="application/rss+xml" />',
            "    <description>Posts by John Aziz on AI engineering, cloud, and software.</description>",
            "    <language>en-us</language>",
            f"    <lastBuildDate>{last_build}</lastBuildDate>",
            *items,
            "  </channel>",
            "</rss>",
        ]
    )


def copy_static_assets() -> None:
    if (SRC_DIR / "images").exists():
        shutil.copytree(SRC_DIR / "images", SITE_DIR / "images", dirs_exist_ok=True)
    if ASSETS_DIR.exists():
        shutil.copytree(ASSETS_DIR, SITE_DIR / "assets", dirs_exist_ok=True)
    if VENDOR_DIR.exists():
        shutil.copytree(VENDOR_DIR, SITE_DIR / "vendor", dirs_exist_ok=True)
    robots_path = SRC_DIR / "robots.txt"
    if robots_path.exists():
        shutil.copy2(robots_path, SITE_DIR / "robots.txt")
    resume_path = SRC_DIR / "resume.pdf"
    if resume_path.exists():
        shutil.copy2(resume_path, SITE_DIR / "resume.pdf")


def bind_server(port: int, handler: Any) -> socketserver.TCPServer:
    for candidate_port in range(port, port + 10):
        try:
            return socketserver.TCPServer(("127.0.0.1", candidate_port), handler)
        except OSError:
            continue
    raise OSError(f"No free port found in range {port}-{port + 9}")


def render_template(environment: Environment, template_name: str, output_path: Path, **context: Any) -> None:
    rendered = environment.get_template(template_name).render(**context)
    write_text(output_path, rendered)


def build_environment() -> Environment:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["date_human"] = lambda value: date_from_value(value).strftime("%b %d, %Y")
    return environment


def blog_index_url(page_number: int) -> str:
    if page_number <= 1:
        return "/blog/"
    return f"/blog/page/{page_number}/"


def blog_index_output_path(page_number: int) -> Path:
    if page_number <= 1:
        return SITE_DIR / "blog" / "index.html"
    return SITE_DIR / "blog" / "page" / str(page_number) / "index.html"


def build_site(minify: bool = True, optimize: bool = True) -> None:
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True, exist_ok=True)

    environment = build_environment()
    posts = collect_posts()
    authors_lookup = load_authors(SRC_DIR / "blog" / ".authors.yml")
    for post in posts:
        post.author_profiles = resolve_post_authors(post.authors, authors_lookup)
    pages = [
        load_page(SRC_DIR / "index.md", "/", "home.html", SITE_DIR / "index.html"),
        load_page(
            SRC_DIR / "blog" / "index.md",
            "/blog/",
            "blog_index.html",
            SITE_DIR / "blog" / "index.html",
        ),
        load_page(
            SRC_DIR / "projects.md",
            "/projects/",
            "projects.html",
            SITE_DIR / "projects" / "index.html",
        ),
        load_page(SRC_DIR / "talks.md", "/talks/", "talks.html", SITE_DIR / "talks" / "index.html"),
        load_page(SRC_DIR / "resume.md", "/resume/", "resume.html", SITE_DIR / "resume" / "index.html"),
        Page(
            title="Page Not Found",
            description="The page you requested was not found.",
            url="/404.html",
            template="404.html",
            output_path=SITE_DIR / "404.html",
        ),
    ]
    projects = load_yaml(DATA_DIR / "projects.yml")
    videos = load_yaml(DATA_DIR / "videos.yml")

    common_context = base_context()
    blog_archive = build_blog_archive(posts)
    page_lookup = {page.url: page for page in pages}

    _page_card_slugs = {"/": "home", "/blog/": "blog", "/projects/": "projects", "/talks/": "talks"}
    for page in pages:
        if page.url in _page_card_slugs:
            page.social_card_url = f"/assets/social/{_page_card_slugs[page.url]}.png"
    for post in posts:
        post.social_card_url = f"/assets/social/blog-{post.slug}.png"

    render_template(
        environment,
        "home.html",
        page_lookup["/"].output_path,
        page=page_lookup["/"],
        posts=posts[:6],
        projects=projects[:6],
        videos=sorted(videos, key=lambda item: int(item.get("views", 0)), reverse=True)[:3],
        **common_context,
    )
    total_blog_pages = max(1, math.ceil(len(posts) / BLOG_POSTS_PER_PAGE))
    for page_number in range(1, total_blog_pages + 1):
        start = (page_number - 1) * BLOG_POSTS_PER_PAGE
        end = start + BLOG_POSTS_PER_PAGE
        paged_posts = posts[start:end]

        blog_page = Page(
            title=page_lookup["/blog/"].title,
            description=page_lookup["/blog/"].description,
            url=blog_index_url(page_number),
            template="blog_index.html",
            output_path=blog_index_output_path(page_number),
            content_html=page_lookup["/blog/"].content_html,
            body_markdown=page_lookup["/blog/"].body_markdown,
            metadata=page_lookup["/blog/"].metadata,
        )

        pagination = {
            "current_page": page_number,
            "total_pages": total_blog_pages,
            "has_previous": page_number > 1,
            "has_next": page_number < total_blog_pages,
            "previous_url": blog_index_url(page_number - 1) if page_number > 1 else None,
            "next_url": blog_index_url(page_number + 1) if page_number < total_blog_pages else None,
            "pages": [
                {
                    "number": number,
                    "url": blog_index_url(number),
                    "is_current": number == page_number,
                }
                for number in range(1, total_blog_pages + 1)
            ],
        }

        render_template(
            environment,
            "blog_index.html",
            blog_page.output_path,
            page=blog_page,
            posts=paged_posts,
            blog_archive=blog_archive,
            current_blog_url=blog_page.url,
            pagination=pagination,
            **common_context,
        )
    render_template(
        environment,
        "projects.html",
        page_lookup["/projects/"].output_path,
        page=page_lookup["/projects/"],
        projects=projects,
        **common_context,
    )
    render_template(
        environment,
        "talks.html",
        page_lookup["/talks/"].output_path,
        page=page_lookup["/talks/"],
        videos=sorted(videos, key=lambda item: str(item.get("published", "")), reverse=True),
        **common_context,
    )
    render_template(
        environment,
        "404.html",
        page_lookup["/404.html"].output_path,
        page=page_lookup["/404.html"],
        **common_context,
    )
    render_template(
        environment,
        "resume.html",
        page_lookup["/resume/"].output_path,
        page=page_lookup["/resume/"],
        **common_context,
    )

    for index, post in enumerate(posts):
        related_posts = related_posts_for(post, posts)
        render_template(
            environment,
            "blog_post.html",
            post.output_path,
            page=post,
            post=post,
            blog_archive=build_blog_archive(posts, active_url=post.url),
            current_blog_url=post.url,
            previous_post=posts[index + 1] if index + 1 < len(posts) else None,
            next_post=posts[index - 1] if index > 0 else None,
            related_posts=related_posts,
            **common_context,
        )

    search_records = build_search_index(
        [page_lookup["/"], page_lookup["/blog/"], page_lookup["/projects/"], page_lookup["/talks/"]],
        posts,
    )
    write_text(SITE_DIR / "search.json", json.dumps(search_records, indent=2))
    write_text(SITE_DIR / "rss.xml", render_rss(posts))

    paginated_blog_urls = [blog_index_url(number) for number in range(1, total_blog_pages + 1)]
    latest_modified = max((post.last_modified for post in posts), default=None)
    latest_modified_iso = latest_modified.isoformat() if latest_modified else None
    sitemap_entries: list[Any] = [
        {"url": page.url, "changefreq": "monthly"} for page in pages if page.url not in {"/404.html", "/blog/"}
    ]
    sitemap_entries += [
        {"url": url, "lastmod": latest_modified_iso, "changefreq": "weekly"} for url in paginated_blog_urls
    ]
    sitemap_entries += [
        {"url": post.url, "lastmod": post.last_modified.isoformat(), "changefreq": "yearly"} for post in posts
    ]
    write_text(SITE_DIR / "sitemap.xml", build_sitemap(sitemap_entries))
    copy_static_assets()
    generate_social_cards(
        posts=posts,
        pages=pages,
        site_dir=SITE_DIR,
        site_name=SITE_NAME,
        logo_path=SRC_DIR / "images" / "logo" / "android-chrome-512x512.png",
        fonts_dir=ROOT_DIR / "vendor" / "fonts" / "static",
        cache_dir=ROOT_DIR / ".cache" / "social",
    )
    if minify:
        minify_site(SITE_DIR)
    if optimize:
        optimize_site(SITE_DIR)


def clean_site() -> None:
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)


def serve_site(port: int, minify: bool = True, optimize: bool = True) -> None:
    build_site(minify=minify, optimize=optimize)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE_DIR))
    with bind_server(port, handler) as httpd:
        actual_port = httpd.server_address[1]
        print(f"Serving {SITE_DIR} at http://127.0.0.1:{actual_port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server")


def main() -> None:
    args = parse_args()
    if args.command == "build":
        build_site(minify=not args.no_minify, optimize=not args.no_optimize)
        return
    if args.command == "clean":
        clean_site()
        return
    if args.command == "serve":
        serve_site(args.port, minify=not args.no_minify, optimize=not args.no_optimize)
        return
    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
