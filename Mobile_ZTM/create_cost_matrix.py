import os
import django
import numpy as np
import time
import json
import concurrent.futures
import requests
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from algorithm.constants import (STOPS_LIST_URL, ROUTES_URL, AVERAGE_HUMAN_SPEED, USER_DATE, USER_TIME,
                                 MAX_WALK_TIME, JSON_TIMETABLES_PATH, DATES_RANGE, USER_START, USER_END)
# import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Mobile_ZTM.settings')
django.setup()

from algorithm.models import Stop, Route, Timetable
from algorithm.ant_colony_optimization import aco_algorithm


def calculate_date_range(dates_range):
    today_date = datetime.now()
    dates_ = list(map(lambda x: x.strftime("%Y-%m-%d"), [today_date + timedelta(days=x) for x in range(dates_range)]))
    return dates_


def get_today_date():
    today_date = datetime.now()
    date_ = today_date.strftime("%Y-%m-%d")
    return date_


def load_json_from_url(url):
    response = requests.get(url)
    print(f"got response from {url}")
    data = json.loads(response.text)
    print(f"data loaded from {url}")
    return data


# TODO 1
#  add measure_time decorator to load functions

# TODO 2
#  add multiprocessing to timetable loading

# TODO 3
#  implement update databases methods

def load_stops_to_database(date):
    start = time.time()
    print("Started loading stops to database")
    data = load_json_from_url(STOPS_LIST_URL)
    date_datetime = datetime.strptime(date, "%Y-%m-%d")
    for stop_dict in data[date]["stops"]:
        stop = Stop(stopId=stop_dict["stopId"], stopLat=stop_dict["stopLat"], stopLon=stop_dict["stopLon"],
                    stopDesc=stop_dict["stopDesc"], onDemand=stop_dict["onDemand"], date=date_datetime)
        stop.save()

    end = time.time()
    print(f"Loading stops to database finished. Elapsed time: {end - start}")


def update_stops_database():
    pass


def load_routes_to_database(date):
    start = time.time()
    print("Started loading routes to database")
    data = load_json_from_url(ROUTES_URL)
    date_datetime = datetime.strptime(date, "%Y-%m-%d")
    for route_dict in data[date]["routes"]:
        route = Route(routeId=route_dict["routeId"], routeShortName=route_dict["routeShortName"],
                      routeLongName=route_dict["routeLongName"], date=date_datetime)
        route.save()
    end = time.time()
    print(f"Loading routes to database finished. Elapsed time: {end - start}")


def update_routes_database():
    pass


# def load_timetable(timetable_url_):
#
#     timetable_data = load_json_from_url(timetable_url_)
#
#     for stop_dict in timetable_data["stopTimes"]:
#         stop_arrival = stop_dict["arrivalTime"]
#         # make_aware converts datetime timezone naive object to timezone aware object
#         # it avoids RuntimeWarning:
#         # DateTimeField Timetable.arrivalTime received a naive datetime while time zone support is active.
#         stop_datetime = make_aware(datetime.strptime(stop_arrival, "%Y-%m-%dT%H:%M:%S"))
#         date = stop_dict["date"]
#         date_datetime = datetime.strptime(date, "%Y-%m-%d")
#
#         timetable = Timetable(stop=Stop.objects.get(stopId=stop_dict["stopId"], date=date_datetime),
#                               route=Route.objects.get(routeId=stop_dict["routeId"], date=date_datetime),
#                               stopSequence=stop_dict["stopSequence"],
#                               busServiceName=stop_dict["busServiceName"], order=stop_dict["order"],
#                               arrivalTime=stop_datetime, date=date_datetime)
#         timetable.save()


def load_timetables_to_database(date):
    start = time.time()
    print("Started loading timetables to database")
    data = load_json_from_url(JSON_TIMETABLES_PATH)
    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     for line in data:
    #         for timetable_url in data[line]:
    #             executor.submit(load_timetable, timetable_url)
    for line in data:
        for timetable_url in data[line]:

            if date not in timetable_url:
                continue

            timetable_data = load_json_from_url(timetable_url)

            for stop_dict in timetable_data["stopTimes"]:
                stop_arrival = stop_dict["arrivalTime"]
                # make_aware converts datetime timezone naive object to timezone aware object
                # it avoids RuntimeWarning:
                # DateTimeField Timetable.arrivalTime received a naive datetime while time zone support is active.
                stop_datetime = make_aware(datetime.strptime(stop_arrival, "%Y-%m-%dT%H:%M:%S"))
                date = stop_dict["date"]
                date_datetime = datetime.strptime(date, "%Y-%m-%d")

                timetable = Timetable(stop=Stop.objects.get(stopId=stop_dict["stopId"], date=date_datetime),
                                      route=Route.objects.get(routeId=stop_dict["routeId"], date=date_datetime),
                                      stopSequence=stop_dict["stopSequence"],
                                      busServiceName=stop_dict["busServiceName"], order=stop_dict["order"],
                                      arrivalTime=stop_datetime, date=date_datetime)
                timetable.save()

    end = time.time()
    print(f"Loading timetables to database finished. Elapsed time: {end - start}")


def update_timetables_database():
    pass


def load_databases(date):
    load_stops_to_database(date)
    load_routes_to_database(date)
    load_timetables_to_database(date)


def update_databases():
    update_stops_database()
    update_routes_database()
    update_timetables_database()


"""-----------------------------------------------------------------------------------------------------------"""


class CostMatrix:
    def __init__(self, user_date, user_time, user_start_input, user_end_input):
        self.start_nodes = []
        self.end_nodes = []
        self.stops_label_dict = {}
        self.cost_dict = {}
        self.cost_matrix = []
        self.cost_matrix_size = 0
        self.user_date = user_date
        self.user_time = user_time
        self.start_stop_id = self.convert_user_input_to_stop_id(user_start_input)
        self.end_stop_id = self.convert_user_input_to_stop_id(user_end_input)

    @staticmethod
    def convert_user_input_to_stop_id(user_input):
        """ function returns stopId of stop equivalent to user input """
        # stop_id = Stop.objects.filter(stopDesc=user_input).values("stopId")[0]["stopId"]
        # print(f"stop id is {stop_id}")
        # FIXME
        #  mocked for test purposes
        if user_input == USER_START:
            return 292
        if user_input == USER_END:
            return 2154

    def convert_cost_dict_to_cost_matrix(self):
        self.cost_matrix = np.full((self.cost_matrix_size, self.cost_matrix_size, 2), [0, "transport unchanged"])
        for key in self.cost_dict:
            row_index = key[:int(key.find("+"))]
            col_index = key[int(key.find("+")) + 1:]
            self.cost_matrix[int(row_index)][int(col_index)] = self.cost_dict[key]

    def create_cost_matrix(self):
        self.add_transport_costs()
        # self.add_walking_costs()
        """ .... """
        self.convert_cost_dict_to_cost_matrix()

    def add_transport_costs(self):
        for timetable in Timetable.objects.filter(stop__stopId=self.start_stop_id, date=self.user_date,
                                                  arrivalTime__range=(self.user_time - timedelta(minutes=10),
                                                                      self.user_time + timedelta(minutes=10))):

            # route_all_stops are by default ordered by stopSequence
            # in case something changes fix it there
            route_all_stops = Timetable.objects.filter(date=self.user_date, route__routeId=timetable.route.routeId,
                                                       busServiceName=timetable.busServiceName, order=timetable.order)

            # adding starting stopId and routeId to start_nodes in format represented by stops_label_dict keys
            if str(timetable.route.routeId) + "|" + str(timetable.stop.stopId) not in self.start_nodes:
                self.start_nodes.append(str(timetable.route.routeId) + "|" + str(timetable.stop.stopId))

            last_route_stop_sequence = route_all_stops.last().stopSequence
            for stop_sequence in range(timetable.stopSequence, last_route_stop_sequence):
                self.add_transport_costs_to_cost_dict(stop_sequence, route_all_stops, 1)

    def add_transport_costs_to_cost_dict(self, stop_sequence, route_all_stops, step):
        current_stop_timetable = route_all_stops[stop_sequence]
        next_stop_timetable = route_all_stops[stop_sequence + step]
        stops_delta_time = next_stop_timetable.arrivalTime - current_stop_timetable.arrivalTime
        time_ = (stops_delta_time.seconds // 60) % 60
        self.add_stop_label(current_stop_timetable)
        self.add_stop_label(next_stop_timetable)
        cost_dict_key = str(self.stops_label_dict[str(current_stop_timetable.route.routeId) + "|" + str(current_stop_timetable.stop.stopId)]) + "+" + \
                        str(self.stops_label_dict[str(next_stop_timetable.route.routeId) + "|" + str(next_stop_timetable.stop.stopId)])
        self.cost_dict[cost_dict_key] = [time_, "transport unchanged"]

    def add_stop_label(self, stop_):
        if str(stop_.route.routeId) + "|" + str(stop_.stop.stopId) not in self.stops_label_dict:
            self.stops_label_dict[str(stop_.route.routeId) + "|" + str(stop_.stop.stopId)] = self.cost_matrix_size
            self.cost_matrix_size += 1
            if stop_.stop.stopId == self.end_stop_id:
                self.end_nodes.append(str(stop_.route.routeId) + "|" + str(stop_.stop.stopId))

    def add_walking_costs(self):
        pass


# def add_walking_paths(cost_matrix):
#     start = time.time()
#     print("Starting add_walking_paths")
#     for stop_1_Id in self.stops_label_dict:
#         for stop_2_Id in self.stops_label_dict:
#             if self.cost_matrix[self.stops_label_dict[stop_1_Id][0]][self.stops_label_dict[stop_2_Id][0]][0] == 0:
#                 # passing stop coordinates to numpy arrays
#                 stop_1_coords = np.array((self.stops_label_dict[stop_1_Id][1], self.stops_label_dict[stop_1_Id][2]))
#                 stop_2_coords = np.array((self.stops_label_dict[stop_2_Id][1], self.stops_label_dict[stop_2_Id][2]))
#                 # calculating euclidean distance
#                 distance = np.linalg.norm(stop_2_Id - stop_1_Id)
#                 # calculating time
#                 time_ = distance/AVERAGE_HUMAN_SPEED
#                 if time_ < MAX_WALK_TIME:
#                     self.cost_matrix[self.stops_label_dict[stop_1_Id][0]][self.stops_label_dict[stop_2_Id][0]][0] = time_
#                     self.cost_matrix[self.stops_label_dict[stop_1_Id][0]][self.stops_label_dict[stop_2_Id][0]][1] = "transport changed"
#     end = time.time()
#     print(f"add_walking_paths finished. Elapsed time: {end - start}")
#     return cost_matrix

# """ downloading stop, route and timetable databases for one day (today's date) """
# date_ = get_today_date()
# load_databases(date_)

start = time.time()
print("Started creating cost matrix")

cost_matrix_obj = CostMatrix(USER_DATE, USER_TIME, USER_START, USER_END)
cost_matrix_obj.create_cost_matrix()

iteration = 100

size = len(cost_matrix_obj.stops_label_dict)

ants = nodes = size

cost_matrix = cost_matrix_obj.cost_matrix
stops_label_dict = cost_matrix_obj.stops_label_dict

# initialization part

e = .5  # evaporation rate
alpha = 1  # pheromone factor
beta = 2  # visibility factor

# calculating the visibility of the next city visibility(i,j) = 1/cost_matrix(i,j)

visibility = np.zeros((size, size))

for row in range(size):
    for col in range(size):
        if int(cost_matrix[row][col][0]):
            visibility[row][col] = 1 / int(cost_matrix[row][col][0])

end = time.time()
print(f"Creating cost matrix finished. Elapsed time: {end - start}")
print(f"Cost matrix size: {size}x{size}")

start = time.time()
print("Started aco algorithm")

# params
# num_iteration, ants, nodes, visibility, cost_matrix_object, e, alpha, beta
route_dict_, best_route_, dist_min_cost_, dist_min_costs_arr_ = aco_algorithm(iteration, size, size, visibility,
                                                                              cost_matrix_obj, e, alpha, beta)

print(f"Finding path from {USER_START} to {USER_END}")
# print('route of all the ants at the end :')
# for key_ in route_dict_:
#     print(f"{key_}: {route_dict_[key_]}")
print('Best path (labeled): ', best_route_)

current_time = USER_TIME
print('Best path (unlabeled): ')

for counter, node_label in enumerate(best_route_):
    key_label = list(stops_label_dict.keys())[list(stops_label_dict.values()).index(node_label)]
    route_id = key_label[:key_label.find("|")]
    stop_id = key_label[key_label.find("|") + 1:]
    if counter:
        current_time += timedelta(minutes=dist_min_costs_arr_[counter-1])
    print(f"{counter}. Route: {route_id}, {Stop.objects.get(stopId=stop_id)}, time: {current_time}")

print(f"Summed cost of the best path: {dist_min_cost_}")

end = time.time()
print(f"Algorithm finished. Elapsed time: {end - start}")
