---
title: "Helpful Mac Finder Customizations"
date: 2026-04-05
description: Terminal commands to customize Mac Finder for development, including showing the Library folder, hidden files, path bar, and status bar.
categories:
  - Mac
tags:
  - Finder
  - Mac
  - Terminal
  - Defaults
  - Development
comments: true
authors:
  - john0isaac
---

A few terminal commands to make Finder more useful for development.

<!-- more -->

## Show Library Folder

The `~/Library` folder is hidden by default. To make it visible:

```bash
chflags nohidden ~/Library
```

## Show Hidden Files

Display dotfiles and other hidden files in Finder:

```bash
defaults write com.apple.finder AppleShowAllFiles YES
```

## Show Path Bar

Add a path bar at the bottom of Finder windows showing the full directory path:

```bash
defaults write com.apple.finder ShowPathbar -bool true
```

## Show Status Bar

Add a status bar at the bottom of Finder showing item count and available disk space:

```bash
defaults write com.apple.finder ShowStatusBar -bool true
```

## Apply Changes

Restart Finder to apply all changes:

```bash
killall Finder
```
