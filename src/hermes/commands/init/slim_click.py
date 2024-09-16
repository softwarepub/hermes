# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

"""
Slim, self-made version of click so we don't need to use it for simple console questions.
"""

PRINT_DEBUG = False


def echo(text, debug: bool = False):
    text = str(text)
    if (not debug) or PRINT_DEBUG:
        print(text)


def confirm(text: str, default: bool = True) -> bool:
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
    return input(text)


def press_enter_to_continue(text: str = "Press ENTER to continue") -> None:
    input(text)


def choose(text: str, options: list[tuple[str, str]], default: str = "") -> str:
    default = default.lower()
    print(text)
    for o in options:
        char = o[0].lower()
        description = o[1]
        if char == default.lower():
            description += " [default]"
        description = o[1]
        print(f"[{char}] {description}")
    while True:
        _answer = input("Your choice: ").lower()
        if _answer in list(zip(*options))[0]:
            return _answer
        elif _answer == "" and default != "":
            return default
        else:
            print("Error: invalid input")


USE_FANCY_HYPERLINKS = False


def create_console_hyperlink(url: str, word: str) -> str:
    return f"\033]8;;{url}\033\\{word}\033]8;;\033\\" if USE_FANCY_HYPERLINKS else f"{word} ({url})"
