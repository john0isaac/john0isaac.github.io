---
template: projects.html
render_macros: true
---

{% for project in projects %}

## {{ project.name }} { #{{ project.name | lower | replace(' ', '-') | replace('/', '-') }} }

{{ project.description }}

{% endfor %}
