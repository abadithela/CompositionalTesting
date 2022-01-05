#############################################################################
#                                                                           #
# Auxiliary Game Graph Construction for Intersection Example                #
# to construct partial order for receding horizon approach                  #
# Josefine Graebener, Apurva Badithela                                      #
# Caltech, January 2022                                                     #
#                                                                           #
#############################################################################
import sys
sys.path.append('..')
import numpy as np
import networkx as nx
from ipdb import set_trace as st
from collections import OrderedDict as od

def create_intersection_from_file(intersectionfile):
    map = od()
    f = open(intersectionfile, 'r')
    lines = f.readlines()
    len_y = len(lines)
    for i,line in enumerate(lines):
        for j,item in enumerate(line):
            if item != '\n':
                map[i,j] = item
    # make dictionary that maps each crosswalk state to a grid cell
    # currenly manual -> TODO crosswalk also automatically from file
    crosswalk = dict()
    start_cw = 2
    end_cw = 6
    y = 2
    for i, num in enumerate(range(2*start_cw,2*(end_cw+1))):
        crosswalk.update({i: (int(np.floor(num/2)), y)})
    return map, crosswalk

def find_next_state_dict(state_dict):
    next_state_dict = dict()
    for state in state_dict:
        if state_dict[state] != '*':
            new_states = []
            new_states.append(state)
            if state_dict[state] == '←' and state[1] > 0:
                new_state = (state[0]-1, state[1])
                new_states.append(new_state)
            if state_dict[state] == '↓' and 7 > state[0]:
                new_state = (state[0], state[1]+1)
                new_states.append(new_state)
            if state_dict[state] == '↑' and state[0] > 0:
                new_state = (state[0], state[1]-1)
                new_states.append(new_state)
            if state_dict[state] == '+':
                if state[0] == 3 and state[1] == 3:
                    new_state = (state[0]-1, state[1])
                    new_states.append(new_state)
                    new_state = (state[0], state[1]+1)
                if state[0] == 4 and state[1] == 3:
                    new_state = (state[0]+1, state[1])
                    new_states.append(new_state)
                    new_state = (state[0], state[1]+1)
                if state[0] == 3 and state[1] == 4:
                    new_state = (state[0]-1, state[1])
                    new_states.append(new_state)
                    new_state = (state[0], state[1]-1)
                if state[0] == 4 and state[1] == 4:
                    new_state = (state[0]+1, state[1])
                    new_states.append(new_state)
                    new_state = (state[0], state[1]-1)
                new_states.append(new_state)
            next_state_dict.update({state: new_states})
    return next_state_dict

def find_next_sys_states(state_dict, next_state_dict, state, crosswalk):
    next_states = [[],[]]
    tester_state = state[1:]
    # st()
    next_car_states = []
    # Find the possible tester car actions
    if tester_state[0] in state_dict:
        next_car_states = next_state_dict[tester_state[0]]

    # Find the possible tester pedestrian actions
    next_ped_states = []
    next_ped_states.append(tester_state[1])
    if tester_state[1] != 0:
        next_ped_states.append(tester_state[1]-1)
    if tester_state[1] != 6:
        next_ped_states.append(tester_state[1]+1)

    # put the combinations back together leaving the tester states untouched
    next_sys_state_combinations = []
    for kk in next_car_states:
        for jj in next_ped_states:
            if kk != state[0] and kk != crosswalk[jj] and state[0] != crosswalk[jj]:
                next_sys_state_combinations.append((state[0], kk, jj))

    return next_sys_state_combinations

def find_next_tester_states(state,next_state_dict,crosswalk):
    next_states = [[],[]]
    # Find the possible system actions
    if state[0] in next_state_dict:
        next_states = next_state_dict[state[0]]

    # put the combinations back together leaving the tester states untouched
    next_tester_combinations = []
    for jj in next_states:
        if jj != state[1] and jj != crosswalk[state[2]]:
                next_tester_combinations.append((jj,state[1],state[2]))
    return next_tester_combinations

def get_game_graph(state_dict, crosswalk):
    x_max_sys = 7
    x_min_sys = 3
    y_max_sys = 4
    y_min_sys = 0
    sys_states = []
    for ii in range(x_min_sys, x_max_sys + 1):
        for jj in range(y_min_sys, y_max_sys + 1):
            if (ii,jj) in state_dict:
                if state_dict[(ii,jj)] == '↑' or state_dict[(ii,jj)] == '←' or state_dict[(ii,jj)] == '+':
                    sys_states.append((ii,jj))
    x_max_test = 7
    x_min_test = 0
    y_test = 3
    tester_states = []
    for ii in range(x_min_test, x_max_test + 1):
            if (ii,y_test) in state_dict:
                tester_states.append((ii,y_test))

    ped_cw_loc_min = 0
    ped_cw_loc_max = 7
    ped_states = []
    for ii in range(x_min_test, x_max_test + 1):
            if (ii) in crosswalk:
                ped_states.append((ii))

    nodes = []
    for sys_state in sys_states:
        for tester_state in tester_states:
            for ped_state in ped_states:
                if sys_state != tester_states and crosswalk[ped_state] != sys_state and crosswalk[ped_state] != tester_states:
                    nodes.append(((sys_state), (tester_state), (ped_state)))

    nstates = len(nodes)
    G = nx.DiGraph()
    V = np.linspace(1, 2 * nstates, 2 * nstates)
    V = V.astype(int)
    G.add_nodes_from(V)
    # st()
    state2vertex = dict()
    sys_state2vertex = dict()
    test_state2vertex = dict()
    # Now loop through the states to match with the numbered graph nodes
    for i,state in enumerate(nodes):
        sys_state2vertex.update({state: i + 1})
        test_state2vertex.update({state: i + 1 + nstates})
    next_state_dict = find_next_state_dict(state_dict)

    # Now loop through the states and create the edges
    edge_dict = dict()
    for state in nodes:
        # For each state depending on if it is a tester or system state, find the next state
        next_sys_states = find_next_sys_states(state_dict,next_state_dict, state, crosswalk)
        next_test_states = find_next_tester_states(state, next_state_dict, crosswalk)
        next_vertices = []
        next_sys_vertices = []
        next_test_vertices = []
        for next_sys_state in next_sys_states:
            try:
                next_sys_vertices.append(sys_state2vertex[next_sys_state])
            except:
                pass
        for next_test_state in next_test_states:
            try:
                next_test_vertices.append(test_state2vertex[next_test_state])
            except:
                pass
        # Make the flip from system state to tester state
        edge_dict.update({sys_state2vertex[state]: next_test_vertices})
        edge_dict.update({test_state2vertex[state]: next_sys_vertices})
    # initialize edges in networkx graph
    for key in edge_dict.keys():
        for item in edge_dict[key]:
            G.add_edge(key,item)
    return G, sys_state2vertex, test_state2vertex

def get_auxiliary_game_graph(G, sys_state2vertex, test_state2vertex):
    # define states for phi_1 and phi_2
    system_wait_state = (4,4) # State of the system when intersection is not free
    system_goal_state = (3,0)
    tester_car_intersection_states = [(1,3), (2,3), (3,3)] # States of the tester car where the system needs to wait
    tester_car_not_intersection_states = [(0,3), (4,3), (5,3), (6,3), (7,3)]
    tester_pedestrian_crosswalk_states = [0,1,2,3]
    tester_pedestrian_not_crosswalk_states = [4,5,6,7]

    # Find the states which satisfy the test specs
    g1_states = []
    for tester_state in tester_car_intersection_states:
        for ped_state in tester_pedestrian_not_crosswalk_states:
            g1_states.append(((system_wait_state), tester_state, ped_state))
    g2_states = []
    for ped_state in tester_pedestrian_crosswalk_states:
        for tester_state in tester_car_not_intersection_states:
            g2_states.append(((system_wait_state), tester_state, ped_state))
    # TODO: make sure g1 and g2 states dont have an overlap!

    # Find final goal states for terminal condition
    goal_states = []
    all_tester_states = tester_car_intersection_states + tester_car_not_intersection_states
    all_ped_states = tester_pedestrian_crosswalk_states + tester_pedestrian_not_crosswalk_states
    for car_state in all_tester_states:
        for ped_state in all_ped_states:
            goal_states.append(((system_goal_state), (car_state), ped_state))

    # create the graph copies to connect
    G_1, G_2, G_T = copy_graphs(G)

    # connect the graph layers
    # connect from G to G_1
    G_c1 = nx.compose(G,G_1)
    for state in g2_states:
        sys_state_num = sys_state2vertex[state] # g2 is always a system state
        G_c1.remove_edges_from(list(G.out_edges(sys_state_num))) # remove all edges from the node in the G graph
        G_c1.add_edge(sys_state_num, str(sys_state_num)+'_1') # add edge from the node in G to the node in G_1
    # connect from G_c1 to G_2
    G_c2 = nx.compose(G_c1,G_2)
    for state in g1_states:
        sys_state_num = sys_state2vertex[state] # g1 is always a system state
        G_c2.remove_edges_from(list(G.out_edges(sys_state_num))) # remove all edges from the node in the G graph
        G_c2.add_edge(sys_state_num, str(sys_state_num)+'_2') # add edge from the node in G to the node in G_1
    # now connect G_c2 to G_T (terminal graph)
    G_aux = nx.compose(G_c2,G_T)
    for state in g2_states:
        sys_state_num = sys_state2vertex[state] # g2 is always a system state
        G_c1.remove_edges_from(list(G.out_edges(str(sys_state_num)+'_2'))) # remove all edges from the node in the G graph
        G_c1.add_edge(str(sys_state_num)+'_2', str(sys_state_num)+'_T') # add edge from the node in G to the node in G_1
    for state in g1_states:
        sys_state_num = sys_state2vertex[state] # g2 is always a system state
        G_c1.remove_edges_from(list(G.out_edges(str(sys_state_num)+'_1'))) # remove all edges from the node in the G graph
        G_c1.add_edge(str(sys_state_num)+'_1', str(sys_state_num)+'_T') # add edge from the node in G to the node in G_1
    # now include 'goal' state in G_aux
    G_aux.add_node('goal') # add the goal state that is connected to nodes in G_T
    for state in goal_states:
        sys_state_num = sys_state2vertex[state] # goal state can be system or tester state
        tester_state_num = test_state2vertex[state]
        G_aux.remove_edges_from(list(G.out_edges(str(sys_state_num)+'_T'))) # remove all edges from the node in the G graph
        G_aux.remove_edges_from(list(G.out_edges(str(tester_state_num)+'_T')))
        G_aux.add_edge(str(sys_state_num)+'_T', 'goal') # add edge from the node in G to the node in G_T
        G_aux.add_edge(str(sys_state_num)+'_T', 'goal')

    return G_aux # Return the auxiliary game graph

def copy_graphs(G):
    G_1 = nx.relabel_nodes(G, lambda x: str(x)+'_1')
    G_2 = nx.relabel_nodes(G, lambda x: str(x)+'_2')
    G_T = nx.relabel_nodes(G, lambda x: str(x)+'_T')
    return G_1, G_2, G_T


if __name__ == '__main__':
    goal_loc = (3,0)

    intersectionfile = 'intersectionfile.txt'
    map, crosswalk = create_intersection_from_file(intersectionfile)
    G, sys_state2vertex, test_state2vertex = get_game_graph(map, crosswalk)
    G_aux = get_auxiliary_game_graph(G, sys_state2vertex, test_state2vertex)
    st()
