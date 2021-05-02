from modules.common.module import BotModule
from urllib.request import urlopen
import json

HOST = 'https://cataas.com'
API = HOST + '/cat?json=true'

class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        with urlopen(API, timeout=5) as response:
            js = json.load(response)

        if 'url' in js:
            img_url = HOST + js["url"]
            await bot.upload_and_send_image(room, img_url)

    def help(self):
        return "🐱 Cat content."
