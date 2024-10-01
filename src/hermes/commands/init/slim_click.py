# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

"""
Slim, self-made version of click so we don't need to use it for simple console questions.
"""

PRINT_DEBUG = False
"""If this is true, echo() will print texts with debug=True."""


def echo(text: str, debug: bool = False):
    """
    :param text: The printed text.
    :param debug: If debug, the text will only be printed when slim_click.PRINT_DEBUG is true.
    """
    text = str(text)
    if (not debug) or PRINT_DEBUG:
        print(text)


def confirm(text: str, default: bool = True) -> bool:
    """The user gets to decide between yes (y) and no (n). The answer will be returned as bool."""
    while True:
        _answer = input(text + (" [Y/n]" if default else " [y/N]") + ": ").lower()
        if _answer == "y":
            return True
        elif _answer == "n":
            return False
        elif _answer == "":
            return default
        else:
            print("Error: invalid input")


def answer(text: str) -> str:
    """Returns the user's response to the given text. It is just a wrapper for input()."""
    return input(text)


def press_enter_to_continue(text: str = "Press ENTER to continue") -> None:
    input(text)


def choose(text: str, options: dict[str, str], default: str = "") -> str:
    """
    The user gets to make a choice between predefined answers.

    :param text: Displayed text / question
    :param options: Dict with possible answers {char -> description}
    :param default: Selected answer (char) if the user doesn't enter anything
    """
    default = default.lower().strip()
    assert default in options.keys(), "Default char should be a key in the options dict."
    print(text)
    for char, description in options.items():
        char = char.lower().strip()
        if char == default.lower():
            description += " (default)"
        print(f"[{char}] {description}")
    while True:
        _answer = input("Your choice: ").lower().strip()
        if _answer in options.keys():
            return _answer
        elif _answer == "" and default != "":
            return default
        else:
            print("Error: invalid input")


USE_FANCY_HYPERLINKS = False
"""If true links will be hidden in the console. Not all consoles support this however."""


def create_console_hyperlink(url: str, word: str) -> str:
    """Use this to have a consistent display of hyperlinks."""
    return f"\033]8;;{url}\033\\{word}\033]8;;\033\\" if USE_FANCY_HYPERLINKS else f"{word} ({url})"
