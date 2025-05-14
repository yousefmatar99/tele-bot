from random import randrange


def rps_game(lst: list[str]):
    if lst[1] is None:
        lst[1] = computer_choice()
    if lst[1] == lst[0]:
        result = 2
    elif (
        (lst[1] == "✂️" and lst[0] == "📄")
        or (lst[1] == "🧱" and lst[0] == "✂️")
        or (lst[1] == "📄" and lst[0] == "🧱")
    ):
        result = 1
    else:
        result = 0
    return result


def computer_choice():
    suggestions = ["✂️", "📄", "🧱"]
    return suggestions[randrange(0, 3)]
