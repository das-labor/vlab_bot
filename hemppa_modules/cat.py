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
            matrix_img_url = await bot.upload_image(img_url)
            if matrix_img_url:
                await bot.send_image(room, matrix_img_url, "a cat")

            # Old version just linking to the image. Will not be shown by 
            # default.
            '''
            await bot.send_html(
                room,
                f"cat <img src='{img_url}'> content",
                f"Cat content {img_url}")
            '''

    def help(self):
        return "Cat content."
