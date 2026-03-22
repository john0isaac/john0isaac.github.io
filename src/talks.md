---
template: talks.html
render_macros: true
---

{% for video in videos %}

## {{ video.title }} { #{{ video.id }} }

{{ video.description | replace("\n#", "\n\\#") }}

{% endfor %}
