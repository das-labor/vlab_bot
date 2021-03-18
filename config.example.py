# copy this file to config.py and change settings
#

EMAIL = "bot@example.org"
USERNAME = "@bot:matrix.org"
PASSWORD = "xxxxxx"
SERVER = "https://example.org"

# Room to join
ROOM = "!123:matrix.org"

# number of seconds to wait between update checks
SLEEP_TIME = 10

# URL to get metrics of WA pusher
METRICS_URL = "https://pusher.wa.binary-kitchen.de/metrics"

# Kind of _/global/example.org/
# the part before map.json
#
ROOM_PREFIX = "_/global/das-labor.github.io/workadv_das-labor/"

# Run in a loop or just once - e.g. used for cronjob
RUN_IN_LOOP = True

# Whether to send messages - for debugging
SEND_MESSAGES = True

# Minimal number of seconds since last message
MIN_SECONDS_SINCE_LAST_MESSAGE = 60 * 5

# Threshold: number of clients seen in given time period
MIN_NUM_CLIENTS_SEEN = 10
TIME_PERIOD_MINUTES = 10