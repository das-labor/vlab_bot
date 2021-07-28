from modules.common.pollingservice import PollingService
from urllib.request import urlopen

class MatrixModule(PollingService):
    def __init__(self, name):
        super().__init__(name)
        self.cityid_incidence = {}
        self.template = 'The incidence for {city} changed to {incidence}'

    async def poll_implementation(self, bot, account, roomid, send_messages):
        city, city_id = account.split(':')

        datasource = f'https://www.lzg.nrw.de/covid19/daten/covid19_{city_id}.csv'
        self.logger.debug(f'Fetching data for {city} from {datasource}')
        with urlopen(datasource, timeout=5) as response:
            lines = response.readlines()

        fieldname_7day_incidence = 'rateM7Tage'
        headline = str(lines[0]).split(',')
        idx_7day_incidence = headline.index(fieldname_7day_incidence)
        incidence = float(
            str(lines[-1], encoding='UTF8').split(',')[idx_7day_incidence])
        self.logger.debug(f'Incidence for {city}: {incidence}')

        if city_id not in self.cityid_incidence or incidence != self.cityid_incidence[city_id]:
            text = self.template.format(city=city, incidence=incidence)
            await bot.send_text(bot.get_room_by_id(roomid), text)
            self.cityid_incidence[city_id] = incidence
            bot.save_settings()

    def get_settings(self):
        data = super().get_settings()
        data['cityid_incidence'] = self.cityid_incidence
        data['template'] = self.template
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('cityid_incidence'):
            self.cityid_incidence = data['cityid_incidence']
        if data.get('template'):
            self.template = data['template']

    def help(self):
        return "Notify about changes in incidence."

    def long_help(self, bot, event, **kwargs):
        return self.help() + \
            ' This is a polling service. Therefore there are additional ' + \
            'commands: list, debug, poll, clear, add, del\n' + \
            '!corona add CITY:ID will add CITY with ID to the polling database.\n' +\
            'e.g. Bochum:5911, Dortmund:5913, Herne:5916, Essen:5113, ' + \
            'Recklinghausen:5562 Look at https://www.lzg.nrw.de to find out more ids. ' +\
            f'I will check for changes roughly every {self.poll_interval_min} minutes.' +\
            f'The service will use the following template:\n"{self.template}"'
