import numpy as np
from pyproj import Geod

AVERAGE_HUMAN_SPEED = 5      # [km/h]
AVERAGE_HUMAN_SPEED /= 60    # [km/min]
AVERAGE_HUMAN_SPEED *= 1000  # [m/min]      = 83.(3) m/min


def aco_algorithm(num_iteration, ants, nodes, visibility, cost_matrix_object, e, alpha, beta):

    geod = Geod(ellps="WGS84")
    cost_matrix = cost_matrix_object.cost_matrix
    stops_label_dict = cost_matrix_object.stops_label_dict
    walking_label_dict = cost_matrix_object.walking_label_dict
    start_nodes = cost_matrix_object.start_nodes
    end_nodes = cost_matrix_object.end_nodes
    route_dict = {}
    best_route = []
    dist_min_cost = 0
    dist_min_cost_arr = []

    if not start_nodes or not end_nodes:
        return route_dict, best_route, dist_min_cost, dist_min_cost_arr

    # FIXME consider multiple starting nodes
    #  now we are taking into consideration only first possible start point
    start = stops_label_dict[start_nodes[0]]["cost_matrix_label"]

    possible_ends = [stops_label_dict[possible_end]["cost_matrix_label"] for possible_end in end_nodes if possible_end in stops_label_dict]
    possible_ends.extend([walking_label_dict[possible_end]["cost_matrix_label"] for possible_end in end_nodes if possible_end in walking_label_dict])

    # initializing pheromone present at the paths to stops
    pheromone = .1 * np.ones((nodes, nodes))
    # for row in range(cost_matrix_object.cost_matrix_size):
    #     for col in range(cost_matrix_object.cost_matrix_size):
    #         if cost_matrix[row][col][1] == -1 and cost_matrix[row][col][0]:
    #             pheromone[row][col] *= 5

    for ite in range(num_iteration):
        for i in range(ants):
            # initial starting position of every ant
            route = [start]

            temp_visibility = np.array(visibility)  # creating a copy of visibility

            node = route[0]

            while node not in possible_ends:
                cur_loc = node

                temp_visibility[:, cur_loc] = 0  # making visibility of the current node equals zero

                p_feature = np.power(pheromone[cur_loc, :], beta)  # calculating pheromone feature
                v_feature = np.power(temp_visibility[cur_loc, :], alpha)  # calculating visibility feature

                p_feature = p_feature[:, np.newaxis]  # adding axis to make a size[5,1]
                v_feature = v_feature[:, np.newaxis]  # adding axis to make a size[5,1]

                combine_feature = np.multiply(p_feature, v_feature)  # calculating the combine feature

                # checking if ant can go any further - if not - ant come back to start node and
                # tries to search for food again
                # FIXME - Replace with more efficient solution
                if not np.any(combine_feature):
                    # adding walk path to first endnode
                    last_stop_key_label = cost_matrix_object.find_label_dict_key_with_cost_matrix_label(node)
                    endpoint_key_label = end_nodes[0]
                    last_stop_label_dict = walking_label_dict if last_stop_key_label in walking_label_dict else stops_label_dict
                    endpoint_label_dict = walking_label_dict if endpoint_key_label in walking_label_dict else stops_label_dict

                    # calculating euclidean distance between 2 stops
                    lons = [last_stop_label_dict[last_stop_key_label]["stop_lon"], endpoint_label_dict[endpoint_key_label]["stop_lon"]]
                    lats = [last_stop_label_dict[last_stop_key_label]["stop_lat"], endpoint_label_dict[endpoint_key_label]["stop_lat"]]

                    walk_distance = geod.line_length(lons, lats)

                    # calculating average time to walk from stop1 to stop
                    walk_time = walk_distance / AVERAGE_HUMAN_SPEED
                    if walk_time > 100:
                        # for route_node in route[-1:]:
                        #     # delete non optimal graph branch
                        #     pass
                        route = [start]
                        node = route[0]
                        continue
                    else:
                        cost_matrix[node][possible_ends[0]] = [walk_time, 0]
                        route.append(possible_ends[0])
                        break

                total = np.sum(combine_feature)  # sum of all the feature

                # finding probability of element probabilities(i) = combine_feature(i)/total
                probabilities = combine_feature / total

                cumulative_probabilities = np.cumsum(probabilities)  # calculating cumulative sum

                r = np.random.random_sample()  # random number in [0,1)

                # finding the next node having probability higher then random number (r)
                node = np.nonzero(cumulative_probabilities > r)[0][0]

                route.append(node)

            route_dict[i] = route

        dist_cost = {}

        for key in route_dict:
            route_cost = []
            for counter, node in enumerate(route_dict[key][:-1]):
                # calculating total tour distance
                cost = cost_matrix_object.return_cost_matrix_cost(int(node), int(route_dict[key][counter+1]))
                route_cost.append(cost)

            dist_cost[key] = route_cost  # storing distance of tour for 'i'th ant at location 'i'

        dist_cost_sum = {key: sum(route_cost) for key, route_cost in dist_cost.items()}

        dist_min_loc = min(dist_cost_sum, key=dist_cost_sum.get)  # finding location of minimum of dist_cost

        dist_min_cost = dist_cost_sum[dist_min_loc]  # finding min of dist_cost

        best_route = route_dict[dist_min_loc]  # initializing current traversed as best route

        pheromone = (1 - e) * pheromone  # evaporation of pheromone with (1-e)

        for key in route_dict:
            for counter, node in enumerate(route_dict[key][:-1]):
                dt = 1 / dist_cost_sum[key]
                pheromone[int(node), int(route_dict[key][counter+1])] += dt
                # updating the pheromone with delta distance (dt)
                # dt will be greater when distance will be smaller
        if ite < 10:
            print(f"iteration: {ite}, route_dict: {route_dict}")
            print(f"iteration: {ite}, dist_cost_sum: {dist_cost_sum}")
            print(f"iteration: {ite}, best route: {best_route}")
    return route_dict, best_route, dist_min_cost, pheromone
