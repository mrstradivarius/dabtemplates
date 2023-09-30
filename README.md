# StradBot

A Pywikibot bot operated by
[Mr. Stradivarius](https://en.wikipedia.org/wiki/User:Mr._Stradivarius).

## Installation

Currently, only development installations are supported.

### Prequisites

Make sure the following software is installed on your computer:

- Git
- Python 3.10 or greater
- Poetry

### Installation steps

1. Download the project.


```bash
git clone https://github.com/mrstradivarius/stradbot.git 
```

2. Enter the project directory.

```bash
cd stradbot
```

3. Install dependencies

```bash
poetry install
```

4. Generate Pywikibot config files

```bash
poetry run pwb generate_user_files.py
```

5. Log in (not needed if using OAuth)

```bash
poetry run pwb login.py
```

## Tasks

### Dabtemplates

Generate a Lua table of disambiguation templates and their redirects. It is
intended to populate
[Module:Disambiguation/templates](https://en.wikipedia.org/wiki/Module:Disambiguation/templates)
on the English Wikipedia.

The script iterates through a category of disambiguation templates. For all
templates that are not in an exclusion list, the script adds the template and
all its redirects to a Lua table, and then writes that table to the target Lua
module page.

Usage:

```bash
poetry run python -m stradbot.dabtemplates [options]
```

This script provides the following options:

- `-cat:<category name>`: The category to search for disambiguation templates.
  By default, this is
  [Category:Disambiguation message boxes](https://en.wikipedia.org/wiki/Category:Disambiguation_message_boxes).
- `-data-page:<data page>`: The Lua module to write the output to. By default,
  this is
  [Module:Disambiguation/templates](https://en.wikipedia.org/wiki/Module:Disambiguation/templates).
- `-exclude:<template 1>,<template 2>,...`: A comma-separated list of templates
  (without the "Template:" prefix) to exclude from the Lua table. By default,
  this is `Dmbox`, meaning
  [Template:Dmbox](https://en.wikipedia.org/wiki/Template:Dmbox) is excluded.
- `-summary:<edit summary>`: The edit summary to use when saving the data page.
  By default, this is "Bot: update disambiguation template list".

In addition, you can use the
[global Pywikibot options](https://www.mediawiki.org/wiki/Manual:Pywikibot/Global_Options).
