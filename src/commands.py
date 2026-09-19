"""Команды эмулятора командной оболочки.

На первом этапе команды ls и cd являются заглушками: они
выводят собственное имя и переданные аргументы. Команда exit
завершает работу эмулятора.
"""

MAX_CD_ARGUMENTS = 1
MAX_EXIT_ARGUMENTS = 0


class CommandError(Exception):
    """Ошибка выполнения команды эмулятора."""


class ExitRequested(Exception):
    """Запрос пользователя на завершение работы эмулятора."""


def format_stub(name, arguments):
    """Составить ответ команды-заглушки.

    :param name: имя команды.
    :param arguments: список аргументов команды.
    :return: строка с именем команды и её аргументами.
    """
    if not arguments:
        return "{0}: аргументы отсутствуют".format(name)
    return "{0}: {1}".format(name, " ".join(arguments))


def command_ls(arguments):
    """Выполнить заглушку команды ls.

    :param arguments: список аргументов команды.
    :return: строка с именем команды и её аргументами.
    """
    return format_stub("ls", arguments)


def command_cd(arguments):
    """Выполнить заглушку команды cd.

    :param arguments: список аргументов команды.
    :return: строка с именем команды и её аргументами.
    :raises CommandError: если аргументов больше одного.
    """
    if len(arguments) > MAX_CD_ARGUMENTS:
        raise CommandError("cd: слишком много аргументов")
    return format_stub("cd", arguments)


def command_exit(arguments):
    """Завершить работу эмулятора.

    :param arguments: список аргументов команды.
    :raises CommandError: если команде переданы аргументы.
    :raises ExitRequested: всегда при корректном вызове.
    """
    if len(arguments) > MAX_EXIT_ARGUMENTS:
        raise CommandError("exit: команда не принимает аргументов")
    raise ExitRequested()


COMMANDS = {
    "ls": command_ls,
    "cd": command_cd,
    "exit": command_exit,
}


def execute(tokens):
    """Выполнить команду, заданную списком токенов.

    :param tokens: непустой список токенов строки ввода.
    :return: текст, который нужно показать пользователю.
    :raises CommandError: если команда неизвестна или её
        аргументы неверны.
    :raises ExitRequested: если выполнена команда exit.
    """
    name = tokens[0]
    handler = COMMANDS.get(name)
    if handler is None:
        raise CommandError("{0}: команда не найдена".format(name))
    return handler(tokens[1:])
