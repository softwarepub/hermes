# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

"""
Slim, self-made version of click so we don't need to use it for simple console questions.
"""
import logging
from enum import Enum

PRINT_DEBUG = False
"""If this is true, echo() will print texts with debug=True."""


class Formats(Enum):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    EMPTY = ''

    def __add__(self, other):
        new = Formats(self)
        new.ansi = self.value + other.value
        return new

    def get_ansi(self) -> str:
        return getattr(self, "ansi", "") or self.value


def echo(text: str, debug: bool = False, formatting: Formats = Formats.EMPTY):
    """
    :param text: The printed text.
    :param debug: If debug, the text will only be printed when slim_click.PRINT_DEBUG is true.
    :param formatting: You can use the Formats Enum to give the text a special color or formatting.
    """
    if formatting != Formats.EMPTY:
        text = f"{formatting.get_ansi()}{text}{Formats.ENDC.get_ansi()}"
    if (not debug) or PRINT_DEBUG:
        print(("DEBUG: " if debug else "") + str(text))


def debug_info(*args, **kwargs):
    kwarg_lines = [f"{str(k)} = {str(v)}" for k, v in kwargs.items()]
    kwarg_lines.extend([str(arg) for arg in args])
    for text in kwarg_lines:
        echo(str(text), True)


def confirm(text: str, default: bool = True) -> bool:
    """The user gets to decide between yes (y) and no (n). The answer will be returned as bool."""
    while True:
        _answer = input(text + (" [Y/n]" if default else " [y/N]") + ": \n").lower()
        if _answer == "y":
            echo("")
            return True
        elif _answer == "n":
            echo("")
            return False
        elif _answer == "":
            echo("Y\n" if default else "N\n")
            return default
        else:
            echo("Error: invalid input", formatting=Formats.FAIL)


def answer(text: str) -> str:
    """Returns the user's response to the given text. It is just a wrapper for input()."""
    a = input(text)
    echo("")
    return a


def press_enter_to_continue(text: str = "Press ENTER to continue") -> None:
    input(text + "\n")
    echo("")


def choose(text: str, options: list[str], default: int = 0) -> int:
    """
    The user gets to make a choice between predefined answers.

    :param text: Displayed text / question
    :param options: List with possible answers
    :param default: Selected answer (index) if the user doesn't enter anything
    :return: The index of the selected option
    """
    assert 0 <= default < len(options), "Default index should match the options list."
    print(text)
    for i, option in enumerate(options):
        index = f"{i:>2d}"
        if i == default:
            index = f"*{i:>1d}"
        print(f"[{index}] {option}")
    while True:
        chosen_index = -1
        response: str = input(f"Your choice [default is {default}]: ").lower().strip()
        if response == "":
            chosen_index = default
        elif response.isdigit():
            chosen_index = int(response)
        if 0 <= chosen_index < len(options):
            echo(f"You selected \"{options[chosen_index]}\".\n", formatting=Formats.OKCYAN)
            return chosen_index
        else:
            echo("Error: invalid input", formatting=Formats.FAIL)


def headline(text: str):
    echo("")
    echo(text, formatting=Formats.HEADER)


current_steps = 0
max_steps = 0


def next_step(description: str):
    global current_steps
    current_steps += 1
    headline(f"-- Step {current_steps} of {max_steps}: {description} --")


USE_FANCY_HYPERLINKS = False
"""If true links will be hidden in the console. Not all consoles support this however."""


def create_console_hyperlink(url: str, word: str) -> str:
    """Use this to have a consistent display of hyperlinks."""
    return f"\033]8;;{url}\033\\{word}\033]8;;\033\\" if USE_FANCY_HYPERLINKS else f"{word} ({url})"


class ColorLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.setLevel(logging.DEBUG)
        self.formatter = ColorLogFormatter()

    def emit(self, record):
        log_entry = self.formatter.format(record)
        echo(log_entry)


class ColorLogFormatter(logging.Formatter):
    def __init__(self, _formats = None):
        """
        Own version of a terminal log formatter to print our log messages with color.
        """
        super().__init__()
        self.formats = {
            'DEBUG': Formats.ITALIC.get_ansi() + '%(message)s' + Formats.ENDC.get_ansi(),
            'INFO': Formats.OKGREEN.get_ansi() + '%(message)s' + Formats.ENDC.get_ansi(),
            'WARNING': Formats.WARNING.get_ansi() + '%(message)s' + Formats.ENDC.get_ansi(),
            'ERROR': Formats.FAIL.get_ansi() + '%(message)s' + Formats.ENDC.get_ansi(),
            'CRITICAL': (Formats.FAIL + Formats.BOLD).get_ansi() + '%(message)s' + Formats.ENDC.get_ansi(),
        }

    def format(self, record):
        log_format = self.formats.get(record.levelname, self._default_format())
        formatter = logging.Formatter(log_format)
        return formatter.format(record)

    @staticmethod
    def _default_format():
        return '%(message)s'
