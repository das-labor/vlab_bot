from modules.common.module import BotModule
from urllib.request import urlopen
import json
import threading


LABOR_STATUS_URL = "https://das-labor.org/status/status.php?status"

FREIFUNK_API ='http://map.freifunk-bochum.de:4000/nodes.json'
# FF_LABOR, FF_LABOR_LOUNGE
FREIFUNK_NODE_IDS = ['e894f6f31a41', 'c4e984e8f03a']

class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        await self.open_closed(bot, room)
        await self.freifunk_nodes(bot, room)
        await bot.send_text(room, f'vLab Bot: {threading.active_count()} laufende Threads')

    async def open_closed(self, bot, room):
        with urlopen(LABOR_STATUS_URL, timeout=5) as response:
            status = response.read().decode()

        if status=='OPEN': icon = "🔓" 
        elif status=='CLOSED': icon = "🔒"
        else: icon = '?'
        msg = f'Geöffnet? {status} {icon}\n'
        await bot.send_text(room, msg)

    async def freifunk_nodes(self, bot, room):
        with urlopen(FREIFUNK_API, timeout=5) as resp:
            js = json.load(resp)

        msg = "🖧 Freifunk: "
        for node in js['nodes']:
            node_info = node['nodeinfo']
            node_id = node_info['node_id']
            if node_id in FREIFUNK_NODE_IDS:
                hostname = node_info['hostname']
                onoff = 'ON' if node['flags']['online'] else 'OFF'
                msg += f'{hostname} {onoff} | '

        # remove last separator
        msg = msg.strip()[:-2]

        await bot.send_text(room, msg)

    def help(self):
        return "🔒 Verschiedene Statusinformationen zum Labor."
