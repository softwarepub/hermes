"""
Slim, self-made version of click so we don't need to use it for simple console questions.
"""

def echo(text: str):
    print(text)

def confirm(text: str, default : bool = True) -> bool:
    while True:
        answer = input(text + (" [Y/n]" if default else " [y/N]") + ": ").lower()
        if answer == "y":
            return True
        elif answer == "n":
            return False
        elif answer == "":
            return default
        else:
            print("Error: invalid input")

def choose(text: str, options: list[tuple[str, str]], default: str = "") -> str:
    default = default.lower()
    print(text)
    for o in options:
        char = o[0]
        if char == default:
            char = char.upper()
        else:
            char = char.lower()
        description = o[1]
        print(f"[{char}] {description}")
    while True:
        answer = input("Your choice: ").lower()
        if answer in list(zip(*options))[0]:
            return answer
        elif answer == "" and default != "":
            return default
        else:
            print("Error: invalid input")
