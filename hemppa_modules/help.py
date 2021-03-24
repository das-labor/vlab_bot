from modules.common.module import BotModule


class MatrixModule(BotModule):

    async def matrix_message(self, bot, room, event):
        msg = f'This is vLab Bot. Known commands:\n\n'

        for modulename, moduleobject in bot.modules.items():
            if moduleobject.enabled:
                msg = msg + '!' + modulename
                try:
                    msg = msg + ' - ' + moduleobject.help() + '\n'
                except AttributeError:
                    pass

        msg += "\nMore information at https://github.com/das-labor/vlab_bot"
        await bot.send_text(room, msg)

    def help(self):
        return 'Prints help on commands'
