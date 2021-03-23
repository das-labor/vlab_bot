# Bot module for https://github.com/vranki/hemppa

from modules.common.module import BotModule
import urllib

WIKI_BASE_URL = "https://wiki.das-labor.org/w"

class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        # !wiki some Wiki page
        args = event.body.split()
        
        if len(args) > 1:
            page = urllib.parse.quote(
                ' '.join(args[1:])
                )
            await bot.send_text(room, f'{WIKI_BASE_URL}/{page}')
        
    def help(self):
        return "Verlinke auf das Labor-Wiki."
