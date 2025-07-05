---
layout: page
title: Projects
permalink: /projects/
---

<!-- markdownlint-disable MD033 -->

{% for project in site.data.projects %}

  <div class="project-preview">
    <h2><a href="{{ project.url }}">{{ project.title }}</a></h2>
    <p><small>{{ project.date | date: "%B %d, %Y" }}</small></p>
    <p>{{ project.description }}</p>
  </div>
  <hr>

{% endfor %}

_See my [GitHub Portfolio](https://github.com/john0isaac) for more._
