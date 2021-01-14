import os
import django
import time
import matplotlib.pyplot as plt
import numpy as np
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Mobile_ZTM.settings')
django.setup()

from create_cost_matrix import CostMatrix
from algorithm.models import Stop, Route, Timetable
from algorithm.ant_colony_optimization import aco_algorithm
from algorithm.constants import (STOPS_LIST_URL, ROUTES_URL, AVERAGE_HUMAN_SPEED, USER_DATE, USER_TIME, MAX_WALK_TIME,
                                 MAX_WALK_DISTANCE, JSON_TIMETABLES_PATH, DATES_RANGE, USER_START, USER_END,
                                 MAX_CHANGE_TIME, MAX_WAIT_TIME, LATS_DIFF, LON_DIFF)


start = time.time()
print("Started creating cost matrix")

cost_matrix_obj = CostMatrix(USER_DATE, USER_TIME, USER_START, USER_END)

# create cost_matrix with maximum 1 change of transport
cost_matrix_obj.create_cost_matrix(1)

iteration = 50
display_num = 25

size = cost_matrix_obj.cost_matrix_size

nodes = size
ants = 700

cost_matrix = cost_matrix_obj.cost_matrix
stops_label_dict = cost_matrix_obj.stops_label_dict

# initialization part

e = .5  # evaporation rate
alpha = 2  # visibility factor
beta = 1  # pheromone factor

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


# Defining a Class
# class GraphVisualization:
#
#     def __init__(self):
#         # visual is a list which stores all
#         # the set of edges that constitutes a
#         # graph
#         self.visual = []
#
#         # addEdge function inputs the vertices of an
#
#     # edge and appends it to the visual list
#     def addEdge(self, a, b):
#         temp = [a, b]
#         self.visual.append(temp)
#
#         # In visualize function G is an object of
#
#     # class Graph given by networkx G.add_edges_from(visual)
#     # creates a graph with a given list
#     # nx.draw_networkx(G) - plots the graph
#     # plt.show() - displays the graph
#     def visualize(self):
#         G = nx.Graph()
#         G.add_edges_from(self.visual)
#         nx.draw_networkx(G)
#         plt.show()
#
#
# graph_ = GraphVisualization()
# for row in range(size):
#     for col in range(size):
#         cost = cost_matrix_obj.return_cost_matrix_cost(row, col)
#         if cost:
#             graph_.addEdge(row, col)
#
# graph_.visualize()

start = time.time()
print("Started aco algorithm")

# params
# num_iteration, ants, nodes, visibility, cost_matrix_object, e, alpha, beta
route_dict_, best_route_, dist_min_cost_, = aco_algorithm(iteration, ants, nodes, visibility, cost_matrix_obj, e, alpha, beta, display_num)
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

    print(f"Summed cost of the best path: {dist_min_cost_}")

end = time.time()
print(f"Algorithm finished. Elapsed time: {end - start}")
