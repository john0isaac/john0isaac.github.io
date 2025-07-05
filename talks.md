---
layout: page
title: Talks
permalink: /talks/
---

<!-- markdownlint-disable MD033 -->

{% for talk in site.data.talks %}

  <div class="talk-preview">
    <h2><a href="{{ talk.url }}">{{ talk.title }}</a></h2>
    <p><small>{{ talk.date | date: "%B %d, %Y" }}</small></p>
    <p>{{ talk.description }}</p>
  </div>
  <hr>

{% endfor %}

_See my [Youtube Channel](https://www.youtube.com/@john0isaac) for more._
