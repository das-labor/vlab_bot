from modules.common.module import BotModule

class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        URL = "https://www.vesselfinder.com/?imo=9811000"
        await bot.send_text(room, f'{URL}')
        
    def help(self):
        return "Wo ist die Evergiven?"
