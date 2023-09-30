import sys
import traceback

import pywikibot
from pywikibot import logging, pagegenerators

from . import lua_serializer


def parse_options():
    """Parse command line arguments and invoke bot."""
    options = {
        "cat": "Category:Disambiguation message boxes",
        "data-page": "Module:Disambiguation/templates",
        "exclude": ["Dmbox"],
        "summary": "Bot: update disambiguation template list",
    }
    local_args = pywikibot.handle_args()  # global options
    for arg in local_args:
        opt, sep, value = arg.partition(":")
        opt = opt[1:]
        if opt in options:
            if isinstance(options[opt], list):
                options[opt] = value.split(",")
            else:
                options[opt] = value
    return options


def fetch_template_aliases(template_generator, excluded):
    """Fetch a list of disambiguation templates and their redirects."""
    aliases = []
    for page in template_generator:
        logging.info(f"Processing {page}")
        if page.title(with_ns=False) in excluded:
            continue
        aliases.append(page.title(with_ns=False))
        for redirect in page.backlinks(
            follow_redirects=False,
            filter_redirects=True,
            namespaces=[10],
            content=False,
        ):
            aliases.append(redirect.title(with_ns=False))
    return aliases


def format_data_page(aliases):
    """Format the list of disambiguation templates as a Lua module."""
    lua_table = lua_serializer.serialize(
        {alias: True for alias in aliases},
        table_keys=lua_serializer.TableKeyFormat.FULL,
    )
    return "return " + lua_table


def save_page(site, title, content, summary):
    """Save a page."""
    page = pywikibot.Page(site, title=title)
    if page.text == content:
        logging.info(f"Content of {page} unchanged; skip saving page")
        return
    page.text = content
    page.save(summary)


def main():
    options = parse_options()
    site = pywikibot.Site()
    template_aliases = fetch_template_aliases(
        template_generator=pagegenerators.CategorizedPageGenerator(
            pywikibot.Category(site, title=options["cat"])
        ),
        excluded=set(options["exclude"])
    )
    save_page(
        site=site,
        title=options["data-page"],
        content=format_data_page(template_aliases),
        summary=options["summary"],
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Error running dabtemplates task: {e}")
        logging.debug(traceback.format_exc())
        sys.exit(1)
    except KeyboardInterrupt:
        logging.critical("Dabtemplates task interrupted by user")
        sys.exit(2)
