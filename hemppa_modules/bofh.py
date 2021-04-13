from modules.common.module import BotModule
from urllib.request import urlopen
import json

HOST = 'http://pages.cs.wisc.edu/~ballard/bofh/bofhserver.pl'
API = HOST + ''

class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        with urlopen(API, timeout=5) as response:
            msg_html = response.read().decode('utf-8')
            msg_search_string = "<font size = \"+2\">"
            msg_html_start_pos = msg_html.rindex(msg_search_string) + len(msg_search_string)
            msg_html_end_pos = msg_html.index("\n</font>")
            msg = "BOFH excuse generator: \"" + msg_html[msg_html_start_pos:msg_html_end_pos] + "\""

            await bot.send_text(room, msg)

    def help(self):
        return "BOFH excuse generator"
