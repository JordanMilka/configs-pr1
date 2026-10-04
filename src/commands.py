"""Команды эмулятора командной оболочки.

Реестр COMMANDS связывает имена команд с обработчиками. Каждый
обработчик принимает список аргументов и объект Session и возвращает
текст для вывода. Здесь собраны служебные команды vfs-info и
vfs-tree и команда exit; ls и cd находятся в src.navigation, cat и
uniq - в src.text_tools, chown и rm - в src.modification.
"""

from src.errors import CommandError, ExitRequested
from src.modification import command_chown, command_rm
from src.navigation import command_cd, command_ls
from src.text_tools import command_cat, command_uniq
from src.vfs import format_info, format_tree


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
    "cat": command_cat,
    "uniq": command_uniq,
    "chown": command_chown,
    "rm": command_rm,
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
