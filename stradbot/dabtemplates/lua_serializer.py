from collections.abc import Iterable, Mapping
import json
from enum import Enum, auto
import math
from numbers import Number
import re


LUA_RESTRICTED_TOKENS = {
    "and",
    "break",
    "do",
    "else",
    "elseif",
    "end",
    "false",
    "for",
    "function",
    "if",
    "in",
    "local",
    "nil",
    "not",
    "or",
    "repeat",
    "return",
    "then",
    "true",
    "until",
    "while",
}


class TableType(Enum):
    """The type of a Lua table."""

    SEQUENCE = auto()  # Example: {"value1", "value2"}
    KEY_VALUE = auto()  # Example: {key1 = "value1", key2 = "value2"}


class TableKeyFormat(Enum):
    """The format of a table key."""

    SHORT = auto()  # Example: {key = "value"}
    FULL = auto()  # Example: {["key"] = "value"}


def make_lua_string(s):
    if not isinstance(s, str):
        raise TypeError(f"make_lua_string expects strings ({type(s).__name__} given)")
    return json.dumps(s, ensure_ascii=False)


lua_name_regex = re.compile("[_a-zA-Z][_a-zA-Z0-9]*")  # Basic Lua name requirements
lua_internal_regex = re.compile("_[A-Z]+")  # Reserved for internal Lua use


def make_lua_table_key(s, *, table_keys):
    if (
        table_keys is not TableKeyFormat.FULL
        and s not in LUA_RESTRICTED_TOKENS
        and lua_name_regex.fullmatch(s)
        and not lua_internal_regex.fullmatch(s)
    ):
        return s
    else:
        return "[" + make_lua_string(s) + "]"


def is_object(obj):
    return isinstance(obj, Iterable) and not isinstance(obj, str)


def is_one_line(obj, *, indent_level, min_single_line_indent_level):
    for item in obj:
        if is_object(item):
            return False
    return indent_level >= min_single_line_indent_level


def add_lua_sequence(
    obj,
    ret,
    *,
    indent,
    indent_level,
    min_single_line_indent_level,
    table_sort_key,
    table_keys,
    table_item_prepend,
    table_item_append,
):
    one_line = is_one_line(
        obj,
        indent_level=indent_level,
        min_single_line_indent_level=min_single_line_indent_level,
    )
    next_indent_level = indent_level + 1
    ret.append("{")
    for i, item in enumerate(obj):
        ret.append(table_item_prepend(TableType.SEQUENCE, None, item, i))
        if not one_line:
            ret.append("\n")
            ret += [indent] * next_indent_level
        add_lua_code(
            item,
            ret,
            indent=indent,
            indent_level=next_indent_level,
            min_single_line_indent_level=min_single_line_indent_level,
            table_sort_key=table_sort_key,
            table_keys=table_keys,
            table_item_prepend=table_item_prepend,
            table_item_append=table_item_append,
        )
        if not one_line:
            ret.append(",")
        elif i < len(obj) - 1:
            ret.append(", ")
        ret.append(table_item_append(TableType.SEQUENCE, None, item, i))
    if not one_line:
        ret.append("\n")
        ret += [indent] * indent_level
    ret.append("}")


def add_lua_table(
    obj,
    ret,
    *,
    indent,
    indent_level,
    min_single_line_indent_level,
    table_sort_key,
    table_keys,
    table_item_prepend,
    table_item_append,
):
    one_line = is_one_line(
        obj,
        indent_level=indent_level,
        min_single_line_indent_level=min_single_line_indent_level,
    )
    next_indent_level = indent_level + 1
    ret.append("{")
    props = obj.keys()
    if table_sort_key is not None:
        props = sorted(props, key=table_sort_key)
    for i, prop in enumerate(props):
        ret.append(table_item_prepend(TableType.KEY_VALUE, prop, obj[prop], i))
        if not one_line:
            ret.append("\n")
            ret += [indent] * next_indent_level
        ret.append(make_lua_table_key(prop, table_keys=table_keys))
        ret.append(" = ")
        add_lua_code(
            obj[prop],
            ret,
            indent=indent,
            indent_level=next_indent_level,
            min_single_line_indent_level=min_single_line_indent_level,
            table_sort_key=table_sort_key,
            table_keys=table_keys,
            table_item_prepend=table_item_prepend,
            table_item_append=table_item_append,
        )
        if not one_line:
            ret.append(",")
        elif i < len(props) - 1:
            ret.append(", ")
        ret.append(table_item_append(TableType.KEY_VALUE, prop, obj[prop], i))
    if not one_line:
        ret.append("\n")
        ret += [indent] * indent_level
    ret.append("}")


def add_lua_code(
    obj,
    ret,
    *,
    indent,
    indent_level,
    min_single_line_indent_level,
    table_sort_key,
    table_keys,
    table_item_prepend,
    table_item_append,
):
    if obj is None:
        ret.append("nil")
    elif obj is True:
        ret.append("true")
    elif obj is False:
        ret.append("false")
    elif isinstance(obj, str):
        ret.append(make_lua_string(obj))
    elif isinstance(obj, Number):
        ret.append(str(obj))
    elif isinstance(obj, Mapping):
        add_lua_table(
            obj,
            ret,
            indent=indent,
            indent_level=indent_level,
            min_single_line_indent_level=min_single_line_indent_level,
            table_sort_key=table_sort_key,
            table_keys=table_keys,
            table_item_prepend=table_item_prepend,
            table_item_append=table_item_append,
        )
    elif isinstance(obj, Iterable):
        add_lua_sequence(
            obj,
            ret,
            indent=indent,
            indent_level=indent_level,
            min_single_line_indent_level=min_single_line_indent_level,
            table_sort_key=table_sort_key,
            table_keys=table_keys,
            table_item_prepend=table_item_prepend,
            table_item_append=table_item_append,
        )
    else:
        raise TypeError(f"Cannot serialize type {type(obj).__name__}")


def return_blank_string(table_type, key, value, index):
    return ""


def serialize(
    obj,
    *,
    indent="\t",
    indent_level=0,
    min_single_line_indent_level=math.inf,
    table_sort_key=None,
    table_keys=TableKeyFormat.SHORT,
    table_item_prepend=return_blank_string,
    table_item_append=return_blank_string,
):
    """
    Serializes a Python object to a Lua table.

    Args:
        obj (number, int, float, str, dict, list): The object to serialize.
        indent (str, optional): The string to indent with, e.g. "\t" or "  ".
        indent_level (int, optional): The initial indentation level.
        min_single_line_indent_level (int, optional): At this indentation level
            or above, tables will be formatted on a single line.
        table_sort_key (Callable, optional): A key function with which to sort
            keys of Lua tables. If not specified, the table is not sorted. For
            details of key functions, see
            https://docs.python.org/3/howto/sorting.html#key-functions.
        table_keys (TableKeyFormat): Whether to use short table keys when
            possible, or to use long-form table keys all the time.
        table_item_prepend: A function to specify text to prepend to a table
            key. Takes a TableType enum value, the key (or None for sequences),
            the value, and the index of the table item in the table as
            parameters, and should return the string to prepend as output.
            Defaults to a function outputting the blank string.
        table_item_prepend: A function to specify text to append to a table
            key. Takes a TableType enum value, the key (or None for sequences),
            the value, and the index of the table item in the table as
            parameters, and should return the string to append as output.
            Defaults to a function outputting the blank string.

    Returns:
        string: A serialized Lua data table string.
    """
    ret = []
    add_lua_code(
        obj,
        ret,
        indent=indent,
        indent_level=indent_level,
        table_keys=table_keys,
        min_single_line_indent_level=min_single_line_indent_level,
        table_sort_key=table_sort_key,
        table_item_prepend=table_item_prepend,
        table_item_append=table_item_append,
    )
    return "".join(ret)
