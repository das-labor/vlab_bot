# Bot module for https://github.com/vranki/hemppa

from modules.common.module import BotModule
from urllib.request import urlopen

LABOR_STATUS_URL = "https://das-labor.org/status/status.php?status"

class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        with urlopen(LABOR_STATUS_URL, timeout=5) as response:
            status = response.read().decode()

        if status=='OPEN': icon = "🔓" 
        elif status=='CLOSED': icon = "🔒"
        else: icon = '?'

        await bot.send_text(room, f"Laborstatus {status} {icon}")
        
    def help(self):
        return "🔒 Ist das Labor geöffnet?"
