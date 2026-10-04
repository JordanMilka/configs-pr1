"""Команды эмулятора командной оболочки.

Команды ls и cd пока являются заглушками: они выводят собственное
имя и переданные аргументы. Команда exit завершает работу эмулятора.
Служебные команды vfs-info и vfs-tree показывают сведения о
подключённой VFS и её дерево. Каждый обработчик принимает список
аргументов и объект Session.
"""

from src.errors import CommandError, ExitRequested
from src.vfs import format_info, format_tree

MAX_CD_ARGUMENTS = 1


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


def require_vfs(name, session):
    """Получить подключённую VFS или сообщить, что её нет.

    :param name: имя команды для сообщения об ошибке.
    :param session: состояние сеанса.
    :return: объект Vfs.
    :raises CommandError: если VFS не подключена.
    """
    if session.vfs is None:
        raise CommandError(
            "{0}: VFS не подключена, задайте параметр --vfs".format(name)
        )
    return session.vfs


def command_vfs_info(arguments, session):
    """Показать сведения о подключённой VFS.

    :param arguments: список аргументов команды.
    :param session: состояние сеанса.
    :return: многострочный текст со сведениями о VFS.
    :raises CommandError: если переданы аргументы или нет VFS.
    """
    reject_arguments("vfs-info", arguments)
    return format_info(require_vfs("vfs-info", session))


def command_vfs_tree(arguments, session):
    """Показать дерево каталогов и файлов подключённой VFS.

    :param arguments: список аргументов команды.
    :param session: состояние сеанса.
    :return: многострочный текст с деревом VFS.
    :raises CommandError: если переданы аргументы или нет VFS.
    """
    reject_arguments("vfs-tree", arguments)
    return format_tree(require_vfs("vfs-tree", session))


COMMANDS = {
    "ls": command_ls,
    "cd": command_cd,
    "vfs-info": command_vfs_info,
    "vfs-tree": command_vfs_tree,
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
