import numpy as np
from numpy import inf

START = 1
END = 6

cost_matrix = np.array([[0, 2, 0, 2, 0, 0],
                        [0, 0, 3, 0, 0, 0],
                        [0, 0, 0, 0, 0, 4],
                        [0, 0, 0, 0, 4, 0],
                        [0, 0, 0, 0, 0, 2],
                        [0, 0, 0, 0, 0, 0]])


iteration = 100
ants = 6
nodes = 6

# initialization part

e = .5        # evaporation rate
alpha = 1     # pheromone factor
beta = 2      # visibility factor

# calculating the visibility of the next city visibility(i,j) = 1/cost_matrix(i,j)

# FIXME
#  fix RuntimeWarning: divide by zero encountered in true_divide

visibility = 1/cost_matrix
visibility[visibility == inf] = 0


def aco_algorithm(num_iteration, start, end):
    # initializing pheromone present at the paths to the cities

    pheromone = .1 * np.ones((ants, nodes))

    route_dict = {}
    best_route = []
    dist_min_cost = 0

    for ite in range(num_iteration):

        # initial starting position of every ants
        route = [start]

        for i in range(ants):

            route = [start]

            temp_visibility = np.array(visibility)  # creating a copy of visibility

            node = route[0]

            while node != end:

                cur_loc = int(node - 1)  # current node of the ant

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
                node = np.nonzero(cumulative_probabilities > r)[0][0] + 1

                route.append(node)

            route_dict[i] = route

        dist_cost = np.zeros((ants, 1))  # initializing total distance with zero

        for key in route_dict:
            route_cost = 0
            for counter, node in enumerate(route_dict[key][:-1]):
                # calculating total tour distance
                route_cost = route_cost + cost_matrix[int(node) - 1, int(route_dict[key][counter+1]) - 1]

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


if __name__ == "__main__":
    final_route_dict, final_best_route, final_dist_min_cost = aco_algorithm(iteration, START, END)

    print(f"finding path from {START} to {END}")
    print('route of all the ants at the end :')
    for key_ in final_route_dict:
        print(f"{key_}: {final_route_dict[key_]}")
    print('best path :', final_best_route)
    print('cost of the best path', int(final_dist_min_cost[0]) + cost_matrix[int(final_best_route[-2]) - 1, 0])
