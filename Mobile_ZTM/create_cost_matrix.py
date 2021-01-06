import os
import django
import numpy as np
import time
import json
import concurrent.futures
import requests
from datetime import datetime, timedelta
from pyproj import Geod
from django.utils.timezone import make_aware
from algorithm.constants import (STOPS_LIST_URL, ROUTES_URL, AVERAGE_HUMAN_SPEED, USER_DATE, USER_TIME, MAX_WALK_TIME,
                                 MAX_WALK_DISTANCE, JSON_TIMETABLES_PATH, DATES_RANGE, USER_START, USER_END,
                                 MAX_CHANGE_TIME, MAX_WAIT_TIME, LATS_DIFF, LON_DIFF)

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
#  bugs in multiprocessing - doesnt' download all the data

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
        self.walking_label_dict = {}
        self.cost_dict = {}
        self.cost_matrix = []
        self.cost_matrix_size = 0
        self.user_date = user_date
        self.user_time = user_time
        self.start_stop_id = self.convert_user_input_to_stop_id(user_start_input)
        self.end_stop_id = self.convert_user_input_to_stop_id(user_end_input)

    @staticmethod
    def timedelta_to_minutes(timedelta_obj):
        return (timedelta_obj.seconds // 60) % 60

    # returns cost_matrix[row][col] cost
    def return_cost_matrix_cost(self, row_, col_):
        return self.cost_matrix[row_][col_][0] if self.cost_matrix[row_][col_][1] == -1 else self.cost_matrix[row_][col_][0] + self.cost_matrix[row_][col_][1]

    @staticmethod
    def convert_user_input_to_stop_id(user_input):
        """ function returns stopId of stop equivalent to user input """
        # stop_id = Stop.objects.filter(stopDesc=user_input).values("stopId")[0]["stopId"]
        # print(f"stop id is {stop_id}")
        # FIXME
        #  mocked for test purposes
        if user_input == USER_START:
            # return 292
            # return 201
            return 8227
        if user_input == USER_END:
            # return 2154
            # return 2231
            return 124

    def convert_cost_dict_to_cost_matrix(self):
        # cost_matrix[row][col][1] values:
        #   -1            (int)              if transport unchanged
        #   wait_time     (unsigned int)     if transport changed
        self.cost_matrix = np.full((self.cost_matrix_size, self.cost_matrix_size, 2), [0, -1])
        for key in self.cost_dict:
            row_index = key[:int(key.find("+"))]
            col_index = key[int(key.find("+")) + 1:]
            self.cost_matrix[int(row_index)][int(col_index)] = self.cost_dict[key]

    def find_label_dict_key_with_cost_matrix_label(self, cost_matrix_label):
        label_dict = self.stops_label_dict if cost_matrix_label in map(lambda x: x["cost_matrix_label"],
                                                                       list(self.stops_label_dict.values())) \
            else self.walking_label_dict

        key = list(label_dict.keys())[list(map(lambda x: x["cost_matrix_label"],
                                               list(label_dict.values()))).index(cost_matrix_label)]
        return key

    def create_cost_matrix(self, change_no):
        change_counter = 0
        self.add_transport_costs_for_first_time()
        print(f"added transport cost 1 st time. cost matrix size: {self.cost_matrix_size}, {self.cost_matrix_size}")
        while not self.end_nodes and change_counter//2 != change_no:
            if not change_counter % 2:
                self.add_walking_costs()
                print(f"added walking cost. cost matrix size: {self.cost_matrix_size}, {self.cost_matrix_size}")
            else:
                self.add_transport_costs()
                print(
                    f"added tranport cost another time. cost matrix size: {self.cost_matrix_size}, {self.cost_matrix_size}")
            change_counter += 1

        self.convert_cost_dict_to_cost_matrix()

    def add_transport_costs(self):
        walked_in_stops_list = [self.stops_label_dict[stop_key] for stop_key in self.stops_label_dict if self.stops_label_dict[stop_key]["walked_in"]]
        walked_in_stops_list.extend([self.walking_label_dict[stop_key] for stop_key in self.walking_label_dict if self.walking_label_dict[stop_key]["walked_in"]])
        for walked_in_stop_dict in walked_in_stops_list:
            route_all_stops = Timetable.objects.filter(date=self.user_date,
                                                       route__routeId=walked_in_stop_dict["route_id"],
                                                       busServiceName=walked_in_stop_dict["bus_service_name"],
                                                       order=walked_in_stop_dict["order"])

            last_route_stop_sequence = route_all_stops.last().stopSequence
            for stop_sequence in range(walked_in_stop_dict["stop_sequence"], last_route_stop_sequence):
                self.add_transport_costs_to_cost_dict(stop_sequence, route_all_stops, 1)

        for label_key in self.stops_label_dict:
            self.stops_label_dict[label_key]["walked_in"] = False
        for walking_label_key in self.walking_label_dict:
            self.walking_label_dict[walking_label_key]["walked_in"] = False

    def add_transport_costs_for_first_time(self):
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
                if stop_sequence == timetable.stopSequence:
                    self.add_transport_costs_to_cost_dict(stop_sequence, route_all_stops, 1)
                else:
                    self.add_transport_costs_to_cost_dict(stop_sequence, route_all_stops, 1)

    def add_transport_costs_to_cost_dict(self, stop_sequence, route_all_stops, step):
        current_stop_timetable = route_all_stops[stop_sequence]
        next_stop_timetable = route_all_stops[stop_sequence + step]
        stops_delta_time = next_stop_timetable.arrivalTime - current_stop_timetable.arrivalTime
        time_ = CostMatrix.timedelta_to_minutes(stops_delta_time)
        current_stop_key = str(current_stop_timetable.route.routeId) + "|" + str(current_stop_timetable.stop.stopId)
        if current_stop_key not in self.stops_label_dict and current_stop_key not in self.walking_label_dict:
            self.add_stop_label(current_stop_timetable, self.stops_label_dict, current_stop_key)
        # FIXME check if second add_stop_label is necessary (duplication bcs of for loop in add_transport_costs)
        next_stop_key = str(next_stop_timetable.route.routeId) + "|" + str(next_stop_timetable.stop.stopId)
        if next_stop_key not in self.stops_label_dict and next_stop_key not in self.walking_label_dict:
            self.add_stop_label(next_stop_timetable, self.stops_label_dict, next_stop_key)
        # FIXME check if cost already not in dict, if yes - pick smaller
        current_stop_label_dict = self.walking_label_dict if current_stop_key in self.walking_label_dict else self.stops_label_dict
        next_stop_label_dict = self.walking_label_dict if next_stop_key in self.walking_label_dict else self.stops_label_dict
        cost_dict_key = str(current_stop_label_dict[str(current_stop_timetable.route.routeId) + "|" +
                                                  str(current_stop_timetable.stop.stopId)]["cost_matrix_label"]) + "+" + \
                        str(next_stop_label_dict[str(next_stop_timetable.route.routeId) + "|" +
                                                  str(next_stop_timetable.stop.stopId)]["cost_matrix_label"])
        self.cost_dict[cost_dict_key] = [time_, -1]

    def add_stop_label(self, stop_, label_dict, key, walked_in=False):
        """
        label_dict
        {
            route_id|stop_id:
                {
                    cost_matrix_label: int,
                    stop_id: int,
                    route_id: int,
                    stop_lat: float,
                    stop_lon: float,
                    time_arrival: datetime.datetime,
                    walked_in: bool,
                    stop_sequence: int,
                    bus_service_name: int,
                    order: int
                }
        }
        """
        value = {
            "cost_matrix_label": self.cost_matrix_size,
            "stop_id": stop_.stop.stopId,
            "route_id": stop_.route.routeId,
            "stop_lat": stop_.stop.stopLat,
            "stop_lon": stop_.stop.stopLon,
            "time_arrival": stop_.arrivalTime,
            "walked_in": walked_in,
            "stop_sequence": stop_.stopSequence,
            "bus_service_name": stop_.busServiceName,
            "order": stop_.order
        }
        label_dict[key] = value
        self.cost_matrix_size += 1
        if stop_.stop.stopId == self.end_stop_id:
            self.end_nodes.append(key)

    def add_walking_costs(self):
        geod = Geod(ellps="WGS84")
        for stop_key in self.stops_label_dict:

            stop_dict = self.stops_label_dict[stop_key]
            stops_around = Timetable.objects.filter(stop__stopLat__range=(stop_dict["stop_lat"] - LATS_DIFF,
                                                                          stop_dict["stop_lat"] + LATS_DIFF),
                                                    stop__stopLon__range=(stop_dict["stop_lon"] - LON_DIFF,
                                                                          stop_dict["stop_lon"] + LON_DIFF),
                                                    arrivalTime__range=(stop_dict["time_arrival"] - MAX_CHANGE_TIME,
                                                                        stop_dict["time_arrival"] + MAX_CHANGE_TIME),
                                                    date=USER_DATE)

            for stop_around in stops_around:
                # if change to the same routeId - continue to next loop iteration
                if stop_around.route.routeId == stop_dict["route_id"]:
                    continue

                # calculating euclidean distance between 2 stops
                lons = [stop_dict["stop_lon"], stop_around.stop.stopLon]
                lats = [stop_dict["stop_lat"], stop_around.stop.stopLat]

                walk_distance = geod.line_length(lons, lats)

                # calculating average time to walk from stop1 to stop
                walk_time = walk_distance / AVERAGE_HUMAN_SPEED

                # if we can't walk on time to stop_around - continue to next loop iteration
                if stop_dict["time_arrival"] + timedelta(minutes=walk_time) > stop_around.arrivalTime:
                    continue

                stop_around_label_key = str(stop_around.route.routeId) + "|" + str(stop_around.stop.stopId)

                wait_time_ = -1

                # calculate time user has to wait for new transport if stop around is not user endpoint
                if stop_around.stop.stopId != self.end_stop_id:
                    after_walk_datetime = stop_dict["time_arrival"] + timedelta(minutes=walk_time)
                    wait_time_timedelta = stop_around.arrivalTime - after_walk_datetime
                    if wait_time_timedelta > MAX_WAIT_TIME:
                        continue
                    wait_time_ = CostMatrix.timedelta_to_minutes(wait_time_timedelta)

                    summed_time = walk_time + wait_time_
                else:
                    summed_time = walk_time

                # if stop_around_label_key in self.stops_label_dict or stop_around_label_key in self.walking_label_dict:
                #     label_dict = self.walking_label_dict if stop_around_label_key in self.walking_label_dict else self.stops_label_dict
                #     cost_dict_key = str(stop_dict["cost_matrix_label"]) + "+" + str(label_dict[stop_around_label_key]["cost_matrix_label"])
                #     # dost_dict values are the same type as cost_matrix[row][col] values
                #     cost_dict_cost = self.cost_dict[cost_dict_key][0]
                #     # if we have wait_time value != -1
                #     if self.cost_dict[cost_dict_key][1] != -1:
                #         cost_dict_cost += self.cost_dict[cost_dict_key][1]
                #
                #     # if new cost (summed_time) is smaller then previous cost (cost_dict_cost)
                #     # in one possible example if its faster to walk then ride
                #     # then change cost of this node
                #     if summed_time < cost_dict_cost:
                #         print(f"summed time is {summed_time}, cost_dict_cost is {cost_dict_cost}")
                #         self.cost_dict[cost_dict_key] = [walk_time, wait_time_]
                #         self.stops_label_dict[stop_around_label_key]["walked_in"] = True

                # else:
                # adding new node to walking_label_dict
                if stop_around_label_key not in self.stops_label_dict and stop_around_label_key not in self.walking_label_dict:
                    self.add_stop_label(stop_around, self.walking_label_dict, stop_around_label_key, walked_in=True)
                label_dict = self.walking_label_dict if stop_around_label_key in self.walking_label_dict else self.stops_label_dict
                cost_dict_key = str(stop_dict["cost_matrix_label"]) + "+" + \
                                str(label_dict[stop_around_label_key]["cost_matrix_label"])
                # adding new cost to cost_dict
                self.cost_dict[cost_dict_key] = [walk_time, wait_time_]


# """ downloading stop, route and timetable databases for one day (today's date) """
# date_ = get_today_date()
# load_databases(date_)


start = time.time()
print("Started creating cost matrix")

cost_matrix_obj = CostMatrix(USER_DATE, USER_TIME, USER_START, USER_END)

# create cost_matrix with maximum 1 change of transport
cost_matrix_obj.create_cost_matrix(1)

iteration = 50

size = cost_matrix_obj.cost_matrix_size

nodes = size
ants = 50

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
        cost = cost_matrix_obj.return_cost_matrix_cost(row, col)
        if cost:
            visibility[row][col] = 1 / cost

end = time.time()
print(f"Creating cost matrix finished. Elapsed time: {end - start}")
print(f"Cost matrix size: {size}x{size}")

start = time.time()
print("Started aco algorithm")

# params
# num_iteration, ants, nodes, visibility, cost_matrix_object, e, alpha, beta
route_dict_, best_route_, dist_min_cost_, endpoint_walk = aco_algorithm(iteration, ants, nodes, visibility,
                                                         cost_matrix_obj, e, alpha, beta)
# TODO check if route_dict is not useless
print(f"Finding path from {USER_START} to {USER_END}")
# print('route of all the ants at the end :')
# for key_ in route_dict_:
#     print(f"{key_}: {route_dict_[key_]}")

if not best_route_:
    print("Could not find connection")
else:
    print('Best path (labeled): ', best_route_)

    current_time = USER_TIME
    print('Best path (unlabeled): ')

    for counter, node_label in enumerate(best_route_):
        key_label = cost_matrix_obj.find_label_dict_key_with_cost_matrix_label(node_label)
        route_id = key_label[:key_label.find("|")]
        stop_id = key_label[key_label.find("|") + 1:]

        if counter:
            previous_node_label = best_route_[counter - 1]
            transport_time, wait_time = cost_matrix[previous_node_label][node_label]

            current_time += timedelta(minutes=int(transport_time))

            if wait_time == -1:
                print(f"{counter}. Route: {route_id}, {Stop.objects.get(stopId=stop_id)}, "
                      f"date: {USER_DATE.date()}, time: {current_time.time()}")
            else:
                current_time += timedelta(minutes=int(wait_time))
                print(f"{counter}. On foot. Route: {route_id}, {Stop.objects.get(stopId=stop_id)},"
                      f" date: {USER_DATE.date()}, walk: {transport_time}, wait: {wait_time}, time: {current_time.time()}")
        else:
            print(f"{counter}. Route: {route_id}, {Stop.objects.get(stopId=stop_id)}, "
                  f"date: {USER_DATE.date()}, time: {current_time.time()}")

    print(f"endpoint_walk time is: {endpoint_walk}")
    print(f"endpoints are: ")
    for key_label in cost_matrix_obj.end_nodes:
        route_id = key_label[:key_label.find("|")]
        stop_id = key_label[key_label.find("|") + 1:]
        print(f"Route: {route_id}, {Stop.objects.get(stopId=stop_id)}, ")
    print(f"Summed cost of the best path: {dist_min_cost_}")

end = time.time()
print(f"Algorithm finished. Elapsed time: {end - start}")
