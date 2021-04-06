from modules.common.module import BotModule
import random


class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        msg = self.wuerfeln() + "\n" + "https://www.reddit.com/r/de/comments/mkt3a8/w%C3%BCrfeln_mit_armin_erstelle_deinen_eigenen/"
        await bot.send_text(room, msg)

    def wuerfeln(self):
        return "🤡 Was wir jetzt brauchen ist ein/e " + \
            random.choice(["ein", "zwei", "drei", "vier", "fünf", "sechs"]) + '-' + \
            random.choice(["tägige","wöchige","monatige","fache","malige","hebige"]) + "/n " +\
            random.choice(["harte", "softe", "optionale", "intransparente", "alternativlose", "ununmkehrbare"]) + "/n " + \
            random.choice(["Wellenbrecher", "Brücken", "Treppen", "Wende", "Impf", "Ehren"]) + "-" + \
            random.choice(["Lockdown", "Stopp", "Maßnahme", "Kampagne", "Sprint", "Matrix"]) + " bis " + \
            random.choice(["zum Sommer", "auf Weiteres", "zur Bundestagwahl","2030","nach den Abiturprüfungen", "in die Puppen"]) + " zur " + \
            random.choice(["sofortigen","nachhaltigen","allmählichen","unausweichlichen","wirtschaftsschonenden","willkürlichen"]) + " " + \
            random.choice(["Senkung","Steigerung","Beendigung","Halbierung","Vernichtung","Beschönigung"]) + " der " + \
            random.choice(["Infektionszahlen","privaten Treffen", "Wirtschaftsleistung", "Wahlprognosen", "dritten Welle", "Bunderskanzlerin"]) + "."

    def help(self):
        return "Pandemieberatung."
