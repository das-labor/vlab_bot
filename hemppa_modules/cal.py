from modules.common.module import BotModule
from urllib.request import urlopen
import datetime
import json
import xml.etree.ElementTree as ET
import os

CAL_RSS_URL ="https://www.das-labor.org/termine.rss"
MAIN_ROOM_ID = os.environ["VLAB_MAIN_ROOM_ID"]

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.poll_interval = 6 * 10 # * 10 seconds
        self.main_room = MAIN_ROOM_ID

    async def matrix_message(self, bot, room, event):
        msg = '📅 Termine der nächsten Tage:\n'

        for date, title, link in self.next_events():
            evdat = date.strftime('%Y-%m-%d %H:%M')
            msg += f'{evdat} {title}\n {link}\n'

        msg += 'https://wiki.das-labor.org/w/Kalender'
        await bot.send_text(room, msg)

    async def matrix_poll(self, bot, pollcount):
        'called every 10 seconds'
        if pollcount % self.poll_interval != 0:
            return

        event_date, title, link = self.next_events(num=1)[0]
        # now  |  event date | next poll interval
        #
        time_until_event = event_date - datetime.datetime.now()
        if time_until_event.total_seconds() < self.poll_interval * 10:
            room = bot.get_room_by_id(self.main_room)
            if room is None:
                return

            msg = f"⏰ Gleich: {title} ({event_date})\n{link}"
            self.logger.debug(f'notify event: {msg}')
            await bot.send_text(room, msg)

    def next_events(self, num=3):
        'return the next num events (date, title, link).'

        tree = ET.parse(urlopen(CAL_RSS_URL, timeout=5))
        root = tree.getroot()
        events = []
        for item in root.iter('item'):
            it_desc = item.find('description').text
            it_link = item.find('link').text

            event_date, title = self.extract(it_desc)
            events.append( (event_date, title, it_link))

            if len(events) >= num:
                return events

    def help(self):
        return "Die nächsten Labor-Termine"

    def extract(self, date_title_line):
        'Extract date and title of event from string'

        # example: 31.03.2021 (Mi) 19:00 - Workshop Labor-Selbstverständnis VI (Online Event)

        date_title = date_title_line.split('-')
        title = '-'.join(date_title[1:])
        # expecting something like: 31.03.2021 (Mi) 19:00
        date = date_title[0].split('(')[0] + date_title[0].split(')')[1]
        dtformat = '%d.%m.%Y %H:%M'
        dt = datetime.datetime.strptime(date.strip(), dtformat)
        return dt, title
