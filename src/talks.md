---
template: talks.html
render_macros: true
title: Talks & Videos
description: Conference talks, workshops, and video content by John Aziz covering AI engineering, Azure, RAG, and open-source development.
---

{% for video in videos %}

## {{ video.title }} { #{{ video.id }} }

{{ video.description | replace("\n#", "\n\\#") }}

{% endfor %}
