from modules.common.module import BotModule
from urllib.request import urlopen
import json
from .spaceapi import MatrixModule as SpaceApi

LABOR_STATUS_URL = "https://das-labor.org/status/api"

FREIFUNK_API ='http://map.freifunk-bochum.de:4000/nodes.json'
# FF_LABOR, FF_LABOR_LOUNGE
FREIFUNK_NODE_IDS = ['e894f6f31a41', 'c4e984e8f03a']

class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        await self.open_closed(bot, room)
        await self.freifunk_nodes(bot, room)

    async def open_closed(self, bot, room):
        _spacename, is_open = SpaceApi.open_status(LABOR_STATUS_URL)

        icon = "🔓" if is_open else "🔒"
        msg = f'Geöffnet? {is_open} {icon}\n'
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
