from modules.common.module import BotModule


class MatrixModule(BotModule):

    async def matrix_message(self, bot, room, event):
        msg = f'Ich bin der vLab Bot. Bekannte Befehle:\n\n'

        for modulename, moduleobject in bot.modules.items():
            if moduleobject.enabled:
                msg = msg + '!' + modulename
                try:
                    msg = msg + ' - ' + moduleobject.help() + '\n'
                except AttributeError:
                    pass

        msg += "\nWeitere Infos hier https://wiki.das-labor.org/w/Projekt/vLab_Bot"
        await bot.send_text(room, msg)

    def help(self):
        return '📝 Hilfe zum vLab Bot.'
