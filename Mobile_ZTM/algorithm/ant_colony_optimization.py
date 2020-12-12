import numpy as np


def aco_algorithm(num_iteration, ants, nodes, visibility, cost_matrix_object, e, alpha, beta):

    cost_matrix = cost_matrix_object.cost_matrix
    stops_label_dict = cost_matrix_object.stops_label_dict
    start_nodes = cost_matrix_object.start_nodes
    end_nodes = cost_matrix_object.end_nodes

    # FIXME consider multiple starting nodes
    #  now we are taking into consideration only first possible start point
    start = stops_label_dict[start_nodes[0]]

    possible_ends = [stops_label_dict[possible_end] for possible_end in end_nodes]
    print(f"possible ends are: {type(possible_ends[0])}")
    # initializing pheromone present at the paths to stops
    pheromone = .1 * np.ones((ants, nodes))

    route_dict = {}
    best_route = []
    dist_min_cost = 0

    for ite in range(num_iteration):
        print(f"{ite} iteration")

        for i in range(ants):

            # initial starting position of every ant
            route = [start]

            temp_visibility = np.array(visibility)  # creating a copy of visibility

            node = route[0]

            while node not in possible_ends:
                print(f"node is {node}")
                cur_loc = node

                temp_visibility[:, cur_loc] = 0  # making visibility of the current node equals zero

                p_feature = np.power(pheromone[cur_loc, :], beta)  # calculating pheromone feature
                v_feature = np.power(temp_visibility[cur_loc, :], alpha)  # calculating visibility feature

                p_feature = p_feature[:, np.newaxis]  # adding axis to make a size[5,1]
                v_feature = v_feature[:, np.newaxis]  # adding axis to make a size[5,1]

                combine_feature = np.multiply(p_feature, v_feature)  # calculating the combine feature

                total = np.sum(combine_feature)  # sum of all the feature

                # finding probability of element probabilities(i) = combine_feature(i)/total
                probabilities = combine_feature / total

                cumulative_probabilities = np.cumsum(probabilities)  # calculating cumulative sum

                r = np.random.random_sample()  # random number in [0,1)

                # finding the next node having probability higher then random number (r)
                node = np.nonzero(cumulative_probabilities > r)[0][0]

                route.append(node)

            route_dict[i] = route

        dist_cost = np.zeros((ants, 1))  # initializing total distance with zero

        for key in route_dict:
            route_cost = 0
            for counter, node in enumerate(route_dict[key][:-1]):
                # calculating total tour distance
                route_cost = route_cost + cost_matrix[int(node) - 1, int(route_dict[key][counter+1]) - 1][0]

            dist_cost[key] = route_cost  # storing distance of tour for 'i'th ant at location 'i'

        dist_min_loc = np.argmin(dist_cost)  # finding location of minimum of dist_cost
        dist_min_cost = dist_cost[dist_min_loc]  # finding min of dist_cost

        best_route = route_dict[dist_min_loc]  # initializing current traversed as best route
        pheromone = (1 - e) * pheromone  # evaporation of pheromone with (1-e)

        for key in route_dict:
            for counter, node in enumerate(route_dict[key][:-1]):
                dt = 1 / dist_cost[key]
                pheromone[int(node) - 1, int(route_dict[key][counter+1]) - 1] += dt
                # updating the pheromone with delta distance (dt)
                # dt will be greater when distance will be smaller
    return route_dict, best_route, dist_min_cost
