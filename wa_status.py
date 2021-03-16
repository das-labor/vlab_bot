from urllib.request import urlopen
from config import METRICS_URL, ROOM_PREFIX

NUM_CLIENTS_MARKER = 'workadventure_nb_clients_per_room'

def number_of_clients(room):
    'Return the numnber of clients in the given room inside a WA instance.'
    with urlopen(METRICS_URL) as f:
        lines = f.readlines()

    for line in lines:
        line_str = line.decode()
        if NUM_CLIENTS_MARKER in line_str and \
            ROOM_PREFIX+room in line_str:

            # line of format
            # workadventure_nb_clients_per_room{room="_/global/das-labor.github.io/workadv_das-labor/main.json"} 20
            number_of_clients_online = int(line_str.split('} ')[1])
            return number_of_clients_online
