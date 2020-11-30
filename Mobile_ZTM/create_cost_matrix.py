import os
import django
import numpy as np
import time
import json
import concurrent.futures
import requests
from datetime import datetime, timedelta
from algorithm.constants import (STOPS_LIST_URL, ROUTES_URL, AVERAGE_HUMAN_SPEED, USER_DATE, USER_TIME,
                       MAX_WALK_TIME, JSON_TIMETABLES_PATH, DATES_RANGE)
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Mobile_ZTM.settings')
django.setup()

from algorithm.models import Stop, Route, Timetable
from algorithm.ant_colony_optimization import aco_algorithm


def calculate_date_range(dates_range):
    today_date = datetime.now()
    dates_ = list(map(lambda x: x.strftime("%Y-%m-%d"), [today_date + timedelta(days=x) for x in range(dates_range)]))
    return dates_


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

def load_stops_to_database(dates_list):
    start = time.time()
    print("Started loading stops to database")
    data = load_json_from_url(STOPS_LIST_URL)
    for date_ in dates_list:
        date_datetime = datetime.strptime(date_, "%Y-%m-%d")
        for stop_dict in data[date_]["stops"]:
            stop = Stop(stopId=stop_dict["stopId"], stopLat=stop_dict["stopLat"], stopLon=stop_dict["stopLon"],
                        stopDesc=stop_dict["stopDesc"], onDemand=stop_dict["onDemand"], date=date_datetime)
            stop.save()
    end = time.time()
    print(f"Loading stops to database finished. Elapsed time: {end - start}")


def update_stops_database():
    pass


def load_routes_to_database(dates_list):
    start = time.time()
    print("Started loading routes to database")
    data = load_json_from_url(ROUTES_URL)
    for date_ in dates_list:
        date_datetime = datetime.strptime(date_, "%Y-%m-%d")
        for route_dict in data[date_]["routes"]:
            route = Route(routeId=route_dict["routeId"], routeShortName=route_dict["routeShortName"],
                          routeLongName=route_dict["routeLongName"], date=date_datetime)
            route.save()
    end = time.time()
    print(f"Loading routes to database finished. Elapsed time: {end - start}")


def update_routes_database():
    pass


def load_timetable(timetable_url_):

    timetable_data = load_json_from_url(timetable_url_)

    for stop_dict in timetable_data["stopTimes"]:
        stop_arrival = stop_dict["arrivalTime"]
        stop_datetime = datetime.strptime(stop_arrival, "%Y-%m-%dT%H:%M:%S")
        date = stop_dict["date"]
        date_datetime = datetime.strptime(date, "%Y-%m-%d")

        timetable = Timetable(stop=Stop.objects.get(stopId=stop_dict["stopId"], date=date_datetime),
                              route=Route.objects.get(routeId=stop_dict["routeId"], date=date_datetime),
                              stopSequence=stop_dict["stopSequence"],
                              busServiceName=stop_dict["busServiceName"], order=stop_dict["order"],
                              arrivalTime=stop_datetime, date=date_datetime)
        timetable.save()


def load_timetables_to_database():
    start = time.time()
    print("Started loading timetables to database")
    data = load_json_from_url(JSON_TIMETABLES_PATH)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for line in data:
            for timetable_url in data[line]:
                executor.submit(load_timetable, timetable_url)

    end = time.time()
    print(f"Loading timetables to database finished. Elapsed time: {end - start}")


def update_timetables_database():
    pass


def load_databases(dates_list):
    load_stops_to_database(dates_list)
    load_routes_to_database(dates_list)
    load_timetables_to_database()


def update_databases():
    update_stops_database()
    update_routes_database()
    update_timetables_database()


"""-----------------------------------------------------------------------------------------------------------"""
# TODO add this to cost_matrix class ?


def create_stops_label_dict(date):
    stops_label_dict = {}
    counter = 0
    for stop_id in Stop.objects.filter(date=date).values("stopId"):
        routes = Timetable.objects.filter(stop__stopId=stop_id, date=date).values('routeId').annotate(dcount=Count('routeId'))
        for route_dict in routes:
            for key in route_dict:
                if key == 'route__routeId':
                    label_key = str(route_dict[key]) + str(stop_id)
                    stops_label_dict[label_key] = counter
                    counter += 1

    return stops_label_dict


# TODO return matrix and print it to debug
def create_cost_matrix(date):
    start = time.time()
    print("starting creating cost matrix")
    stops_label_dict = create_stops_label_dict(date)
    size = len(stops_label_dict)
    # filling cost_matrix with initial values - lists [0, 'transport unchanged']
    cost_matrix = np.full((size, size, 2), [0, 'transport unchanged'])
    cost_matrix = add_costs(date, USER_TIME, 213, 423, cost_matrix, stops_label_dict)
    end = time.time()
    print(f"creating cost matrix finished. Elapsed time: {end - start}")
    print(cost_matrix)
    return cost_matrix, size


# TODO end - value is not used
def add_costs(user_date, user_time, start, end, cost_matrix, stops_label_dict):
    for timetable in Timetable.objects.filter(stop__stopId=start, date=user_date,
                                              arrivalTime__range=(user_time-timedelta(minutes=10),
                                                                  user_time+timedelta(minutes=10))):
        route_all_stops = Timetable.objects.filter(date=user_date, route__routeId=timetable.route__routeId,
                                                   busServiceName=timetable.busServiceName, order=timetable.order)
        last_route_stop_sequence = route_all_stops[-1].stopSequence
        for stop_sequence in range(timetable.stopSequence, last_route_stop_sequence):
            cost_matrix = add_transport_costs(stop_sequence, route_all_stops, stops_label_dict, cost_matrix, 1)
        for stop_sequence in range(timetable.stopSequence, 0, -1):
            cost_matrix = add_transport_costs(stop_sequence, route_all_stops, stops_label_dict, cost_matrix, -1)
    return cost_matrix


def add_transport_costs(stop_sequence, route_all_stops, stops_label_dict, cost_matrix, step):
    stop = route_all_stops[stop_sequence]
    next_stop = route_all_stops[stop_sequence + step]
    stops_delta_time = next_stop.arrivalTime - stop.arrivalTime
    time_ = (stops_delta_time.seconds // 60) % 60
    row_index = stops_label_dict[str(stop.route.routeId) + str(stop.stop.stopId)]
    col_index = stops_label_dict[str(next_stop.route.routeId) + str(next_stop.stop.StopId)]
    cost_matrix[row_index][col_index][0] = time_
    return cost_matrix

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


# dates = calculate_date_range(DATES_RANGE)
# load_databases(dates)


cost_matrix, size = create_cost_matrix(USER_DATE)

iteration = 100

ants = nodes = size

# initialization part

e = .5        # evaporation rate
alpha = 1     # pheromone factor
beta = 2      # visibility factor

# calculating the visibility of the next city visibility(i,j) = 1/cost_matrix(i,j)

visibility = np.zeros((size, size))

for row in range(size):
    for col in range(size):
        if int(cost_matrix[row][col]):
            visibility[row][col] = 1/int(cost_matrix[row][col][0])

start = time.time()
print("Started agorithm")

# FIXME
#  Change params of function to test algorithm

# params
# num_iteration, start, end, ants, nodes, visibility, cost_matrix, e, alpha, beta
final_route_dict, final_best_route, final_dist_min_cost = aco_algorithm(iteration, 213, 423)

print(f"finding path from {213} to {423}")
print('route of all the ants at the end :')
for key_ in final_route_dict:
    print(f"{key_}: {final_route_dict[key_]}")
print('best path :', final_best_route)
print('cost of the best path', int(final_dist_min_cost[0]) + cost_matrix[int(final_best_route[-2]) - 1, 0])
end = time.time()
print(f"Loading timetables to database finished. Elapsed time: {end - start}")