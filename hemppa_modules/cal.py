from modules.common.module import BotModule
from urllib.request import urlopen
import datetime
import json
import xml.etree.ElementTree as ET
import os
from .db import Database
import re
from dataclasses import dataclass

MAIN_ROOM_ID = os.environ["VLAB_BOT_MAIN_ROOM_ID"]

@dataclass
class Event:
    date: datetime.datetime
    title: str
    link: str


class CalDB(Database):
    def init_tables(self):
        with self.dbconn:
            self.dbconn.executescript('''
            CREATE TABLE IF NOT EXISTS cal_urltype (
                name TEST PRIMARY KEY
            );
            INSERT OR IGNORE INTO cal_urltype(name) VALUES ('frab'),('labor_rss'),('ical'),('custom');
            CREATE TABLE IF NOT EXISTS cal_subscription (
                url TEXT PRIMARY KEY,
                type TEXT,
                FOREIGN KEY (type) REFERENCES cal_urltype(name)
            );
            ''')
            # TODO deprecated - remove labor_rss if ical version works
            self.dbconn.commit()

    def add_subscription(self, url, url_type):
        query = 'INSERT INTO cal_subscription (url, type) VALUES (?,?)'
        self.query(query, (url,url_type))

    def delete_subscription(self, url):
        query = 'DELETE FROM cal_subscription WHERE url=?'
        self.query(query, (url,))

    def read_subscriptions(self):
        'Return a list of (url,type) of subscriptions.'
        return [(row[0],row[1]) for row in self.query(
            "SELECT url,type FROM cal_subscription"
        )]

# TODO Make this a polling service

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.poll_interval = 6 * 10 # * 10 seconds
        self.main_room = MAIN_ROOM_ID
        self.db = CalDB()

    async def matrix_message(self, bot, room, event):
        args = event.body.split()

        if len(args)==1:
            msg = '📅 Die nächsten Termine:\n'
            for ev in self.next_events(num=3):
                msg += f'{ev.date} {ev.title}\n{ev.link}\n'

        if len(args)==2 and args[1]=='ls':
            interval = (self.poll_interval * 10) // 60
            msg = f"Hier schaue ich alle {interval} Minuten nach Terminen:\n"
            for url, atype in self.db.read_subscriptions():
                msg += f'- {url} ({atype}) \n'

        if len(args)==4 and args[1]=='add':
            bot.must_be_owner(event)
            _cal, cmd, atype, url = args
            self.db.add_subscription(url, atype)
            msg = f'Added {url} of type {atype}'

        if len(args)==3 and args[1]=='rm':
            bot.must_be_owner(event)
            url = args[2]
            self.db.delete_subscription(url)
            msg = f'Deleted subscription {url}'

        await bot.send_text(room, msg)

    async def matrix_poll(self, bot, pollcount):
        'called every 10 seconds'
        if pollcount % self.poll_interval != 0:
            return

        self.logger.debug('polling events')
        for ev in self.next_events(num=5):
            time_until_event = ev.date - datetime.datetime.now()
            if 0 < time_until_event.total_seconds() < self.poll_interval * 10:
                room = bot.get_room_by_id(self.main_room)
                if room is None:
                    return

                msg = f"⏰ Gleich: {ev.title} ({ev.date})\n{ev.link}"
                self.logger.debug(f'notify event: {msg}')
                await bot.send_text(room, msg)
        self.logger.debug('polling events finished')

    def next_events(self, num=3):
        'return the next num events (date, title, link) sorted by date.'
        events = []
        for url,atype in self.db.read_subscriptions():
            try:
                self.logger.debug(f'fetching {atype} events from {url}')
                if atype == 'labor_rss': events += self._fetch_labor_rss(url)  # TODO deprecated - remove if ical version works
                elif atype == 'frab': events += self._fetch_frab(url)
                elif atype == 'ical': events += self._fetch_ical(url)
                elif atype == 'custom': events += self._fetch_custom(url)
                else:
                    self.logger.warn(f'Type unknown {atype} {url}')
            except Exception as e:
                self.logger.error(f'Error during handling of {url}: {e}')

        # only consider future events
        events_future = [e for e in events if e.date > datetime.datetime.now()]
        # sort events by date
        events_sorted = sorted(events_future, key=lambda e: e.date)
        return events_sorted[:num]

    def _fetch_custom(self, url):
        'fetch and return list of events from url.'

        # temporary custom filter for the following url
        if url != 'https://di.c3voc.de/sessions-liste':
            return []

        url_export = url + '?do=export_raw'
        with urlopen(url_export, timeout=5) as resp:
            lines = [l.decode().strip() for l in resp.readlines()]

        events = []
        re_date = re.compile('.*(\d\.\d\.).*')
        re_time = re.compile('.* (\d+:\d+).* ')
        dtformat = '%d.%m.%Y-%H:%M'
        year = datetime.datetime.now().year
        ev_date, ev_time, ev_title = None, None, None
        for line in lines:
            match = re_date.match(line)
            if match and len(match.groups())>0:
                ev_date = match.group(1)
                
            match = re_time.match(line)
            if match and len(match.groups())>0:
                ev_time = match.group(1)
                title = line.split('|')[2]
                title = title.replace('**','').replace('\\\\','|')
                ev_title = title[:140]
                if len(title)!=len(ev_title): ev_title += '...'

            if ev_date and ev_time and ev_title:
                dat_string = f'{ev_date}{year}-{ev_time}'
                d = datetime.datetime.strptime(dat_string, dtformat)
                events.append(Event(d, ev_title, url))
                ev_time, ev_title = None, None
                #self.logger.debug(f' event added {events[-1]}')

        return events

    def _fetch_frab(self, frab_url):
        'fetch and return list of event from frab_url.'
        events = []
        with urlopen(frab_url, timeout=5) as resp:
            frab = json.load(resp)

        for day in frab['schedule']['conference']['days']:
            for conf_room in day['rooms']:
                for room_ev in day['rooms'][conf_room]:
                    if 'date' not in room_ev or \
                        'title' not in room_ev or \
                        'url' not in room_ev:
                        continue

                    re_title, re_url = room_ev['title'], room_ev['url']
                    re_date = room_ev['date']

                    evt_time = datetime.datetime.fromisoformat(re_date)
                    # remove time zone in order to allow time substraction
                    evt_time = evt_time.replace(tzinfo=None)
                    now = datetime.datetime.now()
                    if evt_time > now:
                        events.append(Event( evt_time, re_title, re_url))

        return events

    def _fetch_ical(self, ical_url):
        'fetch and return events from ical url. not ical feature complete'
        # Handling entries of the form
        # 
        # BEGIN:VEVENT
        # SUMMARY:Chillout Friday (Online Event)
        # URL:https://wiki.das-labor.org/w/Chillout_Friday#_01569f0490f65740e8510125131f1>
        # UID:https://wiki.das-labor.org/w/Chillout_Friday#_01569f0490f65740e8510125131f1>
        # DTSTART:20210604T190000
        # DTSTAMP:20210325T185735
        # SEQUENCE:34834
        # END:VEVENT

        with urlopen(ical_url, timeout=5) as resp:
            lines = [l.decode().strip() for l in resp.readlines()]

        # expected date format: 20210604T190000
        dformat = '%Y%m%dT%H%M00'
        events = []
        for line in lines:
            if line == "BEGIN:VEVENT":
                date,title,link = None,None,None
            elif line.startswith('SUMMARY:'):
                title = ':'.join(line.split(':')[1:])
            elif line.startswith('URL:'):
                link = ':'.join(line.split(':')[1:])
            elif line.startswith('DTSTART:'):
                # expecting DTSTART:20210604T190000
                datestring = line.split(':')[1]
                if 'T' not in datestring:
                    # Time for event missing - ignoring
                    date = None
                    continue
                date = datetime.datetime.strptime(datestring, dformat)
                if date < datetime.datetime.now():
                    # ignoring events in the past
                    date = None
            elif line == "END:VEVENT":
                if date!=None and title!=None and link!=None:
                    events.append(Event(date,title,link))

        return events

    # TODO deprecated - remove if ical version works
    def _fetch_labor_rss(self, url):
        'fetch events from url.'
        events = []
        tree = ET.parse(urlopen(url, timeout=5))
        root = tree.getroot()
        now = datetime.datetime.now()
        for item in root.iter('item'):
            it_desc = item.find('description').text
            it_link = item.find('link').text

            event_date, title = self._labor_extract(it_desc)
            # only collect future events
            if event_date > now:
                events.append(Event(event_date, title, it_link))

        return events 

    # TODO deprecated - remove if ical version works
    def _labor_extract(self, date_title_line):
        'Extract date and title of event from string in labor rss'

        # example: 31.03.2021 (Mi) 19:00 - Workshop Labor-Selbstverständnis VI (Online Event)

        date_title = date_title_line.split('-')
        title = '-'.join(date_title[1:])
        # expecting something like: 31.03.2021 (Mi) 19:00
        date = date_title[0].split('(')[0] + date_title[0].split(')')[1]
        dtformat = '%d.%m.%Y %H:%M'
        dt = datetime.datetime.strptime(date.strip(), dtformat)
        return dt, title

    def help(self):
        return "📅 Ich schaue regelmäßig nach anstehenden Terminen."

    def long_help(self, bot, event, **kwargs):
        text = self.help() + \
            f' Ich schaue alle {self.poll_interval * 10 // 60} Minuten an ' + \
            'verschiedenen Orten nach anstehenden Terminen. Diese Orte ' + \
            'können mit ls, add, rm verändert werden.\n' + \
            '!cal ls: listet die aktuellen Orte/URLs auf\n'

        if bot.is_owner(event):
            text += \
                '!cal add TYPE URL: fügt eine URL ' + \
                'hinzu. Mögliche Werte für TYPE sind frab, ical, custom.\n' + \
                '!cal rm URL: entfernt eine URL'

        return text