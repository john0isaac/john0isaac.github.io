---
template: projects.html
render_macros: true
title: Projects
description: Open-source projects by John Aziz spanning AI engineering, web apps, developer tools, Azure templates, and automation scripts.
---

{% for project in projects %}

## {{ project.name }} { #{{ project.name | lower | replace(' ', '-') | replace('/', '-') }} }

{{ project.description }}

{% endfor %}
