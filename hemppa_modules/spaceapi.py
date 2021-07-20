from modules.common.pollingservice import PollingService
from urllib.request import urlopen
import json
import time

class MatrixModule(PollingService):
    def __init__(self, name):
        super().__init__(name)
        self.poll_interval_min = 10
        self.poll_interval_random = 1
        self.accountroomid_laststatus = {}

    async def poll_implementation(self, bot, account, roomid, send_messages):
        self.logger.debug(f'polling space api {account}.')
        with urlopen(account, timeout=5) as response:
            js = json.load(response)

        spacename = js['space']
        open = 'open 🔓' if js['state']['open'] else 'closed 🔒'
        last_status = self.accountroomid_laststatus.get(account+roomid, False)
        text = f'{spacename} is now {open}'

        if send_messages and last_status != open:
            await bot.send_text(bot.get_room_by_id(roomid), text)
            self.accountroomid_laststatus[account+roomid] = js['state']['open']
            bot.save_settings()

    def get_settings(self):
        data = super().get_settings()
        data['laststatus'] = self.accountroomid_laststatus
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('laststatus'):
            self.accountroomid_laststatus = data['laststatus']

    def help(self):
        return "Notify about Space-API status changes (open or closed)."

    def long_help(self, bot, event, **kwargs):
        return self.help() + \
            ' This is a polling service. Therefore there are additional ' + \
            'commands: list, debug, poll, clear, add URL, del URL\n' + \
            '!spaceapi add URL: to add a space-api endpoint\n' + \
            '!spaceapi list: to list the endpoint configured for this room.\n' + \
            f'I will look for changes roughly every {self.poll_interval_min} ' + \
            'minutes. Find out more about Space-API at https://spaceapi.io/.'
