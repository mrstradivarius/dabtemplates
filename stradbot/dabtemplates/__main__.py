from datetime import datetime
from pathlib import Path
import string
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
        "data-page-sandbox": "Module:Disambiguation/templates/sandbox",
        "data-page-sandbox-summary": "Bot: update disambiguation template list",
        "exclude": ["Dmbox"],
        "data-talk-page": "Module talk:Disambiguation",
        "edit-request-template": Path(
            __file__, "..", "templates", "edit_request.txt"
        ).resolve(),
        "edit-request-summary": "Bot: create edit request to update disambiguation template list",
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
    return "return " + lua_table + "\n"


def format_edit_request_text(
    edit_request_template_path, data_page, data_page_sandbox, template_category
):
    """Format the edit request text to post on the data module talk page."""
    edit_request_template = edit_request_template_path.read_text(encoding="utf-8")
    return (
        string.Template(edit_request_template)
        .substitute(
            current_date=datetime.utcnow().strftime("%d %B %Y").lstrip("0"),
            data_page=data_page.title(),
            data_page_sandbox=data_page_sandbox.title(),
            template_category=template_category.title(),
        )
        .strip()
    )


def is_content_equal(content1, content2):
    """Compare page content, ignoring final whitespace."""
    return content1.rstrip() == content2.rstrip()


def main():
    logging.info(f"Start dabtemplates task")
    options = parse_options()
    site = pywikibot.Site()
    logging.info(f"Options: {options}")
    logging.info(f"Site: {site}")

    # Construct the new data module content
    template_category = pywikibot.Category(site, title=options["cat"])
    logging.info(f"Fetch templates in {template_category} and their redirects")
    template_aliases = fetch_template_aliases(
        template_generator=pagegenerators.CategorizedPageGenerator(template_category),
        excluded=set(options["exclude"]),
    )
    data_page_content = format_data_page(template_aliases)

    # Check if the module sandbox content would change, and exit if not
    data_page_sandbox = pywikibot.Page(site, title=options["data-page-sandbox"])
    logging.info(f"Check if {data_page_sandbox} content needs updating")
    if is_content_equal(data_page_sandbox.text, data_page_content):
        logging.info(
            f"Content of {data_page_sandbox} would not change; skip saving page"
        )
        return

    # Save the new module content
    data_page_sandbox.save(options["data-page-sandbox-summary"], text=data_page_content)

    # Check if the module content would change, and exit if not
    data_page = pywikibot.Page(site, title=options["data-page"])
    logging.info(f"Check if {data_page} content needs updating")
    if is_content_equal(data_page.text, data_page_content):
        logging.info(
            f"Content of {data_page} is identical to new sandbox content; "
            f"skip adding edit request"
        )
        return

    # Create an edit request for the new content
    data_talk_page = pywikibot.Page(site, title=options["data-talk-page"])
    logging.info(f"Post edit request at {data_talk_page}")
    edit_request_text = format_edit_request_text(
        Path(options["edit-request-template"]),
        data_page,
        data_page_sandbox,
        template_category,
    )
    data_talk_page.text = f"{data_talk_page.text.rstrip()}\n\n{edit_request_text}\n"
    data_talk_page.save(options["edit-request-summary"])
    logging.info(f"End dabtemplates task")


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
