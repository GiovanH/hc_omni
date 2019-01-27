__module_name__ = "omni"
__module_version__ = "1.8"
__module_description__ = "Client support for OmniServ"

import hexchat
from string import Formatter

CONFIG_SERVER = "Undernet"
CONFIG_CHANNEL = "#bookz"


class DefaultFormatter(Formatter):
    def __init__(self, **kwargs):
        Formatter.__init__(self)
        self.defaults = kwargs

    def get_value(self, key, args, kwargs):
        if isinstance(key, str):
            passsedValue = kwargs.get(key)
            if passsedValue is not None:
                return passsedValue
            return self.defaults[key]
        else:
            super().get_value(key, args, kwargs)


def send(context, chan, msg):
    do_command(context, "MSG {chan} {msg}".format(**vars()))


def do_command(context, command):
    # context.prnt("[omni.py] <{}>".format(command))
    context.command(command)


def cmd_omni(words, words_eol, userdata):
    undernet = hexchat.find_context(server=CONFIG_SERVER)
    usrmsg = " ".join(words[1:])  # Slice off command
    if len(usrmsg) > 0:
        send(
            context=undernet,
            chan=CONFIG_CHANNEL,
            msg="@find " + usrmsg
        )
        # Clear the menu
        divide_menu()
        # reset_menu()
    return hexchat.EAT_HEXCHAT


def hard_strip(s):
    return "".join([c for c in str(s) if ord(c) in range(128)])


def msg_listener(words, words_eol, userdata):
    import re

    context = hexchat.find_context(server=CONFIG_SERVER)
    (user, msgtype, dest, *usrmsg) = words
    usrmsg = hexchat.strip(" ".join(usrmsg)[1:])  # Slice off :
    if dest[0] == "#":
        return
    # context.prnt(user)
    # context.prnt(msgtype)
    # context.prnt(dest)
    # context.prnt(usrmsg)

    # When we get a PM, parse it for books.
    # Formats:
    # Omenserv: ![BotName] [Book title.ext] ::info:: [SizeXB]  OmenServe v2.71
    # Proper response: Safe to parrot entire line, or substrings.
    # PS2: [INDEX]: ([Book title.ext] 472KB)
    # Proper response: UNKNOWN

    methods = [
        (
            "(?P<bot>\![^ ]+) (?P<title>.+\.[A-Za-z]{0,5}) (::(info|INFO):: ){0,1}(?P<size>[0-9,\.]+[A-Za-z]B){0,1}.*",
            "{title} [{size}]", "{bot} {title}"
        )

    ]
    for (pattern, namefmt, cmdfmt) in methods:
        match = re.match(pattern, hard_strip(usrmsg))
        if match is None:
            continue
        groupdict = match.groupdict()
        try:
            formatter = DefaultFormatter(size="--xB")
            
            Formatter.format
            book_name = formatter.format(namefmt, **groupdict)
            book_cmd = formatter.format(cmdfmt, **groupdict)

            BOOK_CACHE[book_name] = book_cmd
            if groupdict.get("size") is None:
                context.prnt("Book missing size: <{}>".format(usrmsg))
            context.prnt("Found book: <{}>".format(book_name))
            add_menu_item(groupdict.get("bot"), book_name)
        except Exception as e:
            import traceback
            context.prnt(traceback.format_exc())


def divide_menu():
    for heading in MENU_HEADERS:
        cmdstr = 'MENU -p0 ADD "Bookz/{heading}/--------------------" "echo that doesn\'t do anything you dimtwit"'.format(
            heading=heading
        )
        do_command(hexchat, cmdstr)


def reset_menu():
    do_command(hexchat, "MENU DEL Bookz")
    do_command(hexchat, "MENU ADD Bookz")


def add_menu_item(heading, book_name):
    # When given a book name, add it to the menu.
    if heading not in MENU_HEADERS:
        do_command(hexchat, 'MENU ADD "Bookz/{heading}"'.format(
            heading=heading
        ))
        MENU_HEADERS.append(heading)
    cmdstr = 'MENU -p0 ADD "Bookz/{heading}/{label}" "omnidl {label}'.format(
        heading=heading,
        label=book_name
    )
    do_command(hexchat, cmdstr)


def menu_hook(words, words_eol, userdata):
    undernet = hexchat.find_context(server=CONFIG_SERVER)
    key = " ".join(words[1:])
    try:
        msg = BOOK_CACHE[key]
    except KeyError:
        import pprint
        import traceback
        hexchat.prnt(traceback.format_exc())
        hexchat.prnt(pprint.pformat(BOOK_CACHE, width=35))
        hexchat.prnt(pprint.pformat(words, width=35))
        raise
    send(
        context=undernet,
        chan=CONFIG_CHANNEL,
        msg=msg
    )
    return hexchat.EAT_HEXCHAT

    # When given a book name, download it and remove the menu item.


def hook():
    global BOOK_CACHE
    global MENU_HEADERS
    BOOK_CACHE = dict()
    MENU_HEADERS = list()
    hexchat.hook_command("omni", cmd_omni, help="Enter your search string")
    hexchat.hook_command("omnidl", menu_hook)
    hexchat.hook_server("PRIVMSG", msg_listener)

    reset_menu()


hook()
