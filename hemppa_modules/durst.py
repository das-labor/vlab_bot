import xml.etree.ElementTree as ET
from urllib.request import urlopen, quote
from modules.common.module import BotModule

PAGE_URL = 'https://wiki.das-labor.org/w/Spezial:Exportieren?pages=' + quote('Getränke')
NS = '{http://www.mediawiki.org/xml/export-0.10/}'
PATH = f'{NS}page/{NS}revision/{NS}text'

class MatrixModule(BotModule):
    def __init__(self,name):
        super().__init__(name)
        self.default_minimal_inventory = 5

    async def matrix_message(self, bot, room, event):
        min_inventory = self.default_minimal_inventory

        args = event.body.split()
        if len(args) == 2:
            # !durst NUMBER
            min_inventory = int(args[1])
        
        await bot.send_text(room, self._check_inventory(min_inventory))

    def _check_inventory(self, minimal_inventory):
        root = ET.parse(urlopen(PAGE_URL, timeout=5)).getroot()
        page = root.find(PATH)

        inInventory = False
        answer = f'🥛 Getränke mit geringem Bestand (<{minimal_inventory}):\n'
        for line in page.text.split('\n'):
            if 'Bestandsliste' in line: inInventory = True
            if inInventory and '||' in line:
                # assuming lines: '| Club Mate || 87 || 20 || 1.00 || 10.21'
                sorte, bestand, _ = line.strip().split('||', maxsplit=2)
                if bestand.strip() == '': continue  # ignore empty lines
                sorte = sorte[1:].strip()  # remove heading '|'
                if int(bestand) < minimal_inventory:
                    answer += f'- {sorte} ({bestand})\n'

        answer += 'https://wiki.das-labor.org/w/Getr%C3%A4nke'
        return answer

    def help(self):
        return "🥛 Infos über die Getränkeliste - !durst [NUM]"
