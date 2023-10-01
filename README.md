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
all its redirects to a Lua table. It then writes that table to the sandbox of
the target Lua module page, and if the sandbox and the target Lua module are
different, it adds an edit request to the talk page.

Usage:

```bash
poetry run python -m stradbot.dabtemplates [options]
```

This script provides the following options:

- `-cat:<category name>`: The category to search for disambiguation templates.
  By default, this is
  [Category:Disambiguation message boxes](https://en.wikipedia.org/wiki/Category:Disambiguation_message_boxes).
- `-data-page:<data page>`: The Lua module where the template list is stored.
  By default, this is
  [Module:Disambiguation/templates](https://en.wikipedia.org/wiki/Module:Disambiguation/templates).
- `-data-page-sandbox:<data page sandbox>`: The sandbox page for the template
  list module. By default, this is
  [Module:Disambiguation/templates/sandbox](https://en.wikipedia.org/wiki/Module:Disambiguation/templates/sandbox).
- `-data-page-sandbox-summary:<edit summary>`: The edit summary to use when
  saving the data page sandbox. By default, this is "Bot: update disambiguation
  template list".
- `-exclude:<template 1>,<template 2>,...`: A comma-separated list of templates
  (without the "Template:" prefix) to exclude from the Lua table. By default,
  this is `Dmbox`, meaning
  [Template:Dmbox](https://en.wikipedia.org/wiki/Template:Dmbox) is excluded.
- `-data-talk-page:<data talk page>`: The talk page of the template list
  module. By default, this is
  [Module talk:Disambiguation](https://en.wikipedia.org/wiki/Module_talk:Disambiguation).
- `-edit-request-template:<edit request template path>`: Path to a template of
  the text to use when adding edit requests to the data talk page. This
  defaults to "stradbot/dabtemplates/templates/edit_request.txt". The template
  accepts the following parameters:
  - `$current_date`: The current date in long form (e.g. "7 October 2023").
  - `$data_page`: The title of the data page.
  - `$data_page_sandbox`: The title of the data page sandbox.
  - `$template_category`: The title of the category used to find disambiguation
    templates.
- `-edit-request-summary:<edit request summary>`: The edit summary to use when
  saving edit requests to the data talk page.  By default, this is "Bot: create
  edit request to update disambiguation template list".

In addition, you can use the
[global Pywikibot options](https://www.mediawiki.org/wiki/Manual:Pywikibot/Global_Options).
