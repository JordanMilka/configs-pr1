"""Команды эмулятора командной оболочки.

Команды ls и cd пока являются заглушками: они выводят собственное
имя и переданные аргументы. Команда exit завершает работу эмулятора.
Каждый обработчик принимает список аргументов и объект Session.
"""

MAX_CD_ARGUMENTS = 1


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


def reject_arguments(name, arguments):
    """Убедиться, что команде не переданы аргументы.

    :param name: имя команды.
    :param arguments: список аргументов команды.
    :raises CommandError: если список аргументов не пуст.
    """
    if arguments:
        raise CommandError(
            "{0}: команда не принимает аргументов".format(name)
        )


def command_ls(arguments, session):
    """Выполнить заглушку команды ls.

    :param arguments: список аргументов команды.
    :param session: состояние сеанса.
    :return: строка с именем команды и её аргументами.
    """
    return format_stub("ls", arguments)


def command_cd(arguments, session):
    """Выполнить заглушку команды cd.

    :param arguments: список аргументов команды.
    :param session: состояние сеанса.
    :return: строка с именем команды и её аргументами.
    :raises CommandError: если аргументов больше одного.
    """
    if len(arguments) > MAX_CD_ARGUMENTS:
        raise CommandError("cd: слишком много аргументов")
    return format_stub("cd", arguments)


def command_exit(arguments, session):
    """Завершить работу эмулятора.

    :param arguments: список аргументов команды.
    :param session: состояние сеанса.
    :raises CommandError: если команде переданы аргументы.
    :raises ExitRequested: всегда при корректном вызове.
    """
    reject_arguments("exit", arguments)
    raise ExitRequested()


COMMANDS = {
    "ls": command_ls,
    "cd": command_cd,
    "exit": command_exit,
}


def execute(tokens, session):
    """Выполнить команду, заданную списком токенов.

    :param tokens: непустой список токенов строки ввода.
    :param session: состояние сеанса.
    :return: текст, который нужно показать пользователю.
    :raises CommandError: если команда неизвестна или её
        аргументы неверны.
    :raises ExitRequested: если выполнена команда exit.
    """
    name = tokens[0]
    handler = COMMANDS.get(name)
    if handler is None:
        raise CommandError("{0}: команда не найдена".format(name))
    return handler(tokens[1:], session)
