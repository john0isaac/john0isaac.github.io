---
layout: page
title: Blog
permalink: /blog/
---

<!-- markdownlint-disable MD033 -->

Welcome to my blog! Here you'll find posts on AI, cloud, software engineering, and community stories.

{% for post in site.posts %}

  <div class="post-preview">
    <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
    <p><small>{{ post.date | date: "%B %d, %Y" }}</small></p>
    <p>{{ post.excerpt }}</p>
  </div>
  <hr>
{% endfor %}

{% for post in site.data.blogs %}

  <div class="post-preview">
    <h2><a href="{{ post.url }}" target="_blank" rel="noopener noreferrer">{{ post.title }}</a></h2>
    <p><small>{{ post.date | date: "%B %d, %Y" }}</small></p>
    <p>{{ post.description }}</p>
  </div>
  <hr>
{% endfor %}
