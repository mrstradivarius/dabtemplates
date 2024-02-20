from datetime import datetime
from pathlib import Path
import string

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


def fetch_template_metadata(template_generator, excluded):
    """Fetch a list of disambiguation templates and their redirects."""
    templates = []
    for page in template_generator:
        logging.info(f"Processing {page}")
        if page.title(with_ns=False) in excluded:
            continue
        redirects = []
        for redirect in page.redirects(namespaces=[10], content=False):
            redirects.append(redirect.title(with_ns=False))
        redirects.sort()
        templates.append(
            {"template": page.title(with_ns=False), "redirects": redirects}
        )
    return templates


def fetch_top_comment(data_page):
    top_comment = []
    for line in data_page.text.split("\n"):
        if line.startswith("--") or line == "":
            top_comment.append(line)
        else:
            break
    return "\n".join(top_comment).strip()


def format_data_page(template_metadata, top_comment):
    """Format the list of disambiguation templates as a Lua module."""
    templates = set(item["template"] for item in template_metadata)

    def prepend_new_line_to_template_keys(table_type, key, value, index):
        if (
            table_type is lua_serializer.TableType.KEY_VALUE
            and index > 0
            and key in templates
        ):
            return "\n"
        else:
            return ""

    keys = []
    for item in template_metadata:
        keys.append(item["template"])
        keys += item["redirects"]

    lua_table = lua_serializer.serialize(
        {key: True for key in keys},
        table_keys=lua_serializer.TableKeyFormat.FULL,
        table_item_prepend=prepend_new_line_to_template_keys,
    )
    return top_comment + "\n\n" + "return " + lua_table + "\n"


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
    data_page = pywikibot.Page(site, title=options["data-page"])
    template_category = pywikibot.Category(site, title=options["cat"])
    logging.info(f"Fetch templates in {template_category} and their redirects")
    template_metadata = fetch_template_metadata(
        template_generator=pagegenerators.CategorizedPageGenerator(template_category),
        excluded=set(options["exclude"]),
    )
    top_comment = fetch_top_comment(data_page)
    data_page_content = format_data_page(template_metadata, top_comment)
    logging.debug(f"Data page content:\n{data_page_content}")

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
    logging.debug(f"Edit request text:\n{edit_request_text}")
    data_talk_page.text = f"{data_talk_page.text.rstrip()}\n\n{edit_request_text}\n"
    data_talk_page.save(options["edit-request-summary"])
    logging.info(f"End dabtemplates task")
