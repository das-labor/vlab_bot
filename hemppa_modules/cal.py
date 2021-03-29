from modules.common.module import BotModule
from urllib.request import urlopen
import datetime

CAL_RSS_URL ="https://www.das-labor.org/termine.rss"
MAX_NUMBER_EVENTS = 5

class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        events = '📅 Termine der nächsten Tage:\n'
        num_events = 0
        for line in urlopen(CAL_RSS_URL, timeout=5).readlines():
            lined = line.decode()
            if '<description>' in lined and '(' in lined:
                event_date, title = self.extract(lined)
                evdat = event_date.strftime('%Y-%m-%d %H:%M')
                events += f'{evdat} {title}\n'
                today = datetime.datetime.now()
                past = today - datetime.timedelta(days=-10)
                num_events += 1

            if num_events >= MAX_NUMBER_EVENTS:
                break

        events += 'https://wiki.das-labor.org/w/Kalender'
        await bot.send_text(room, events)
        
    def help(self):
        return "Die nächsten Labor-Termine"

    def extract(self, date_title_line):
        'Extract date and title of event from string'

        # example: <description>31.03.2021 (Mi) 19:00 - Workshop Labor-Selbstverständnis VI (Online Event)</description>

        date_title = date_title_line.split('<description>')[1].  \
            split('</description>')[0]. \
            split('-')
        title = '-'.join(date_title[1:])
        # expecting something like: 31.03.2021 (Mi) 19:00
        date = date_title[0].split('(')[0] + date_title[0].split(')')[1]
        dtformat = '%d.%m.%Y %H:%M'
        dt = datetime.datetime.strptime(date.strip(), dtformat)
        return dt, title
