import datetime
from django.utils.timezone import make_aware
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Mobile_ZTM.settings')
django.setup()

AVERAGE_HUMAN_SPEED = 5      # [km/h]
AVERAGE_HUMAN_SPEED /= 60    # [km/min]
AVERAGE_HUMAN_SPEED *= 1000  # [m/min]      = 83.(3) m/min
MAX_WALK_TIME = 15           # [min]
MAX_WALK_DISTANCE = AVERAGE_HUMAN_SPEED*MAX_WALK_TIME   # ~1250 m
MAX_WAIT_TIME = datetime.timedelta(minutes=15)
MAX_CHANGE_TIME = datetime.timedelta(minutes=MAX_WALK_TIME)+MAX_WAIT_TIME
DATES_RANGE = 7

LATS_DIFF = 0.01123
LON_DIFF = 0.01928

STOPS_LIST_URL = "https://ckan.multimediagdansk.pl/dataset/c24aa637-3619-4dc2-a171-a23eec8f2172/resource/4c4025f0-01bf-41f7-a39f-d156d201b82b/download/stops.json"
ROUTES_URL = "https://ckan.multimediagdansk.pl/dataset/c24aa637-3619-4dc2-a171-a23eec8f2172/resource/22313c56-5acf-41c7-a5fd-dc5dc72b3851/download/routes.json"
JSON_TIMETABLES_PATH = "https://ckan.multimediagdansk.pl/dataset/c24aa637-3619-4dc2-a171-a23eec8f2172/resource/a023ceb0-8085-45f6-8261-02e6fcba7971/download/stoptimes.json"

"""------------------------------------------------------------------------------------------------------------------"""
# First test
routeId = 3

USER_DATE = datetime.datetime(2020, 12, 6)
# data oznacza ze tego samego dnia
USER_TIME = make_aware(datetime.datetime(1899, 12, 30, 3, 56))
# start stopId = 292
USER_START = 'Zajezdnia Nowy Port (techniczny)'
# end stopId = 2154
USER_END = "Węzeł Kliniczna"
"""------------------------------------------------------------------------------------------------------------------"""
# Second test
# routeId = 6
#
# USER_DATE = datetime.datetime(2020, 12, 6)
# # data oznacza ze tego samego dnia
# USER_TIME = make_aware(datetime.datetime(1899, 12, 30, 8, 56))
# # start stopId = 201
# USER_START = 'Jelitkowo'
# # end stopId = 2231
# USER_END = "Łostowice Świętokrzyska"
"""------------------------------------------------------------------------------------------------------------------"""
# Third test
routeId = 3

# USER_DATE = datetime.datetime(2020, 12, 6)
# # data oznacza ze tego samego dnia
# USER_TIME = make_aware(datetime.datetime(1899, 12, 30, 13, 22))
# # start stopId = 8227
# USER_START = 'Gdynia Dąbrowa Centrum'
# # end stopId = 124
# USER_END = "Zaspa SKM"
