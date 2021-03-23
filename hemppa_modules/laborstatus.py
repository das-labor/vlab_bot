# Bot module for https://github.com/vranki/hemppa

from modules.common.module import BotModule
from urllib.request import urlopen

LABOR_STATUS_URL = "https://das-labor.org/status/status.php?status"
LAB_STATE_URL = "https://www.das-labor.org/status/LAB_STATE.png"

class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        with urlopen(LABOR_STATUS_URL) as response:
            status = response.read().decode()
        
        await bot.send_text(room, f'Laborstatus: {status}')
        
    def help(self):
        return "Ist das Labor geöffnet?"
