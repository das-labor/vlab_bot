from modules.common.module import BotModule


class MatrixModule(BotModule):

    async def matrix_message(self, bot, room, event):
        msg = '1/2 Limette\n' + \
               '2EL (20g) Brauner Zucker\n' + \
                '100-200g Crushed Ice\n' + \
                '4cl Rum\n' + \
                '100-150ml Mate\n' + \
                '1 Strohhalm\n' + \
                '(bei Entropia geklaut)'
        
        await bot.send_text(room, msg)

    def help(self):
        return '📝 Tschunkrezept.'
