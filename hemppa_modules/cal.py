from modules.common.module import BotModule
from urllib.request import urlopen
import datetime
import json
import xml.etree.ElementTree as ET

CAL_RSS_URL ="https://www.das-labor.org/termine.rss"
MAX_NUMBER_EVENTS = 3

class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        msg = '📅 Termine der nächsten Tage:\n'

        for date, title, link in self.next_events():
            msg += f'{date} {title}\n {link}\n'

        msg += 'https://wiki.das-labor.org/w/Kalender'
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
            evdat = event_date.strftime('%Y-%m-%d %H:%M')
            events.append( (evdat, title, it_link))

            if len(events) >= MAX_NUMBER_EVENTS:
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
