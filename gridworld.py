#############################################################################
#                                                                           #
# Basic class for grid world traffic simulation                             #
# Josefine Graebener, Apurva Badithela                                      #
# Caltech, March 2021                                                       #
#                                                                           #
#############################################################################
from random import choice
# from mcts import MCTS, Node
import numpy as np
from scene import Scene
from agent import Agent
from map import Map
from winning_set import WinningSet, specs_for_entire_track, make_grspec
import _pickle as pickle
import os
from copy import deepcopy
from ipdb import set_trace as st


class GridWorld:
    def __init__(self,lanes,width, initial_scene, ego_agents=None, env_agents=None, turn=None):
        self.lanes = lanes    # Number of one direction lanes stacked
        self.width = width    # number of gridcells in a lane
        self.initial_scene = initial_scene # dictionary of initial agent conditions
        if ego_agents is not None:
            self.ego_agents = ego_agents #
        else:
            self.ego_agents = [] # empty list of ego agents in system

        if env_agents is not None:
            self.env_agents = env_agents
        else:
            self.env_agents = [] # empty list of env agents in system
        self.actions = {'move': (1,0), 'stay': (0,0), 'mergeR': (1,1), 'mergeL': (1,-1)} # possible actions for ego
        self.env_actions = {'move': (1,0), 'stay': (0,0)} # possible actions for each tester
        self.trace = []
        self.map = Map(lanes,width)
        self.timestep = 0
        # Game conditions of the MCTS:
        if turn is not None:
            self.turn = turn
        else:
            self.turn = "env"
        self.terminal = False # This is when ego finally merges to cell 2; should be set to the ego agent tuple once merge is complete
        self.shield_dict = None
        # self.w_set = None
        self.aut, self.winning_set = self.synthesize_shield()


    '''-----Basic gridworld functions-----'''

    def setup_world(self):
        '''Initializing the gridworld'''
        for i,agent in enumerate(self.initial_scene):
            if agent.name[0:3] =='sys':
                self.ego_agents.append(agent)
            else:
                self.env_agents.append(agent)
        self.print_state()

    def take_next_step(self,agent,action,agent_list):
        '''Given a list of agent positions, update the chosen agent position after the step'''
        # find agent in agentlist
        i = agent_list.index(agent)
        # make this move
        agentpos = (agent[1],agent[2])
        enabled_actions = self.enabled_actions_from_loc(agentpos, agent_list)
        agent_list[i][1] = enabled_actions[action][0]
        agent_list[i][2] = enabled_actions[action][1]
        # check if allowed by shield here
        if self.check_if_state_in_winning_set(agent_list):
            return agent_list
        else:
            st()
            return None
        # st()
        # return agent_list

    def get_actions(self,agent,agent_list):
        '''get all possible actions for an agent from its position'''
        agentpos = (agent[1],agent[2])
        enabled_actions = self.enabled_actions_from_loc(agentpos, agent_list)
        return enabled_actions

    def get_relative_positions(self):
        ego_x = self.ego_agents[0].x
        ego_y = self.ego_agents[0].y
        for agent in self.env_agents:
            agent_x = agent.x - ego_x
            agent_y = agent.y - ego_y
        return (agent_x,agent_y)

    def synthesize_shield(self):
        ego_spec, test_spec = specs_for_entire_track(3)
        gr_spec = make_grspec(test_spec, ego_spec)
        w_set = WinningSet()
        w_set.set_spec(gr_spec)
        aut = w_set.make_compatible_automaton(gr_spec)
        winning_set = w_set.find_winning_set(aut)
        return aut, winning_set

    def check_if_state_in_winning_set(self,agent_list):
        st()
        w_set = WinningSet()
        state = self.map_to_state(agent_list)
        #state = {'x': 1, 'y': 1, 'x1': 3, 'y1':2, 'x2':1, 'y2': 2}  # To check if a state is in the winning set, pass all values in dictionary form. Each dictionary corresponds to one state.
        check_bdd = w_set.check_state_in_winset(self.aut, self.winning_set, state) # Check-bdd is a boolean. True implies that state is in the winning set.
        if check_bdd:
            # print("State is in the winning set")
            return True
        else:
            # print("State is not in the winning set")
            return False

    def load_shield(self): # pass spec to winning set analysis here
        if not self.shield_dict:
            w_set = WinningSet()
            self.shield_dict = w_set.synthesize_shield()
        self.mapping = dict() # positions in (x,y)
        self.mapping.update({(0,1): 's1_t'})
        self.mapping.update({(-1,1): 's5_t'})
        self.mapping.update({(1,1): 's2_t'})
        self.mapping.update({(-1,0): 's0_t'})

    def map_to_state(self, agentlist):
        # automate this
        statedict = {'x': self.ego_agents[0].x, 'y': self.ego_agents[0].y, 'x1': agentlist[0][1], 'y1': agentlist[0][2], 'x2': agentlist[1][1], 'y2': agentlist[1][2]}
        return statedict

    def shield(self, enabled_actions):
        # st()
        # if not self.shield_dict:
        #     self.load_shield()
        # map state names to relative positions
        # rel_pos = self.get_relative_positions()
        # run enabled actions through dict

        # find all children states of this state
        # check if they are allowed in the shield

        ok_actions = self.shield_dict[self.mapping[rel_pos]]
        shielded_actions = dict()
        for action in ok_actions:
            if action in enabled_actions:
                shielded_actions.update({action: enabled_actions[action]})
        return shielded_actions

    def ego_take_input(self, action):
        '''Ego agent takes the step'''
        for agent in self.ego_agents:
            enabled_actions = self.enabled_actions(agent)
            if action in enabled_actions.keys():
                x,y = enabled_actions[action]
                agent.x = x
                agent.y = y
            elif 'move' in enabled_actions.keys():
                ran_act = choice(['move', 'stay'])
                x,y = enabled_actions[ran_act]
                agent.x = x
                agent.y = y
            else:
                x,y = enabled_actions['stay']
                agent.x = x
                agent.y = y

    def enabled_actions_from_loc(self,agentpos,agent_list):
        '''Find the possible actions for an agent from its position'''
        x = agentpos[0]
        y = agentpos[1]
        enabled_actions = dict()
        for action in self.env_actions.keys():
            move_x,move_y = self.env_actions[action]
            act_x = x + move_x
            act_y = y + move_y
            if self.is_cell_free((act_x,act_y),agent_list) and act_y in range(1,3):
                enabled_actions.update({action: (act_x,act_y)})
            enabled_actions.update({'stay': (x,y)})
        # st()
        # shielded_actions = self.shield(enabled_actions)
        # st()
        return enabled_actions

    def enabled_actions(self,agent):
        '''Find possible actions for agent'''
        enabled_actions = dict()
        x = agent.x
        y = agent.y
        for action in self.actions.keys():
            move_x,move_y = self.actions[action]
            act_x = x+move_x
            act_y = y+move_y
            if self.is_cell_free((act_x,act_y)) and act_y in range(1,3):
                enabled_actions.update({action: (act_x,act_y)})
            enabled_actions.update({'stay': (x,y)}) # stay is always included
        return enabled_actions


    def is_cell_free(self, cellxy, agent_list = None):
        '''check if the cell is free'''
        x,y = cellxy
        if not agent_list:
            agents = self.ego_agents + self.env_agents
            for agent in agents:
                if agent.x == x and agent.y == y:
                    return False
        else:
            for pos in agent_list: # check all env agents
                if pos[1] == x and pos[2] == y:
                    return False
            for agent in self.ego_agents:
                if agent.x == x and agent.y == y:
                    return False
        return True

    def agent_take_step(self,agent,action):
        '''For known action, take the step (used for find children in tree search)'''
        enabled_actions = self.enabled_actions(agent)
        x,y = enabled_actions[action]
        agent.x = x
        agent.y = y

    def env_take_step(self, agent, action):
        '''Take the step for env, used for actually taking the actions during execution'''
        enabled_actions = self.enabled_actions(agent)
        if action in enabled_actions:
            x,y = enabled_actions[action]
            agent.x = x
            agent.y = y
        else:
            x,y = enabled_actions['stay']
            agent.x = x
            agent.y = y

    def is_terminal(self):
        '''Returns if the state is terminal'''
        for agent in self.ego_agents:
            if agent.y == agent.goal or agent.x == self.width:
                self.terminal = True
            else:
                self.terminal = False
        return self.terminal

    def check_terminal(self, agent):
        '''Returns if the state is terminal'''
        if agent.y == agent.goal:
            self.terminal = True
        else:
            self.terminal = False
        return self.terminal

    def print_state(self):
        '''Print the current state of all agents in the terminal'''
        agents = self.ego_agents + self.env_agents
        for i in range(1,self.lanes+1):
            lanestr = []
            for k in range(1,self.width+1):
                occupied = False
                for agent in agents:
                    if agent.x == k and agent.y == i:
                        lanestr.append('|'+str(agent.name[0]))
                        occupied = True
                if not occupied:
                    lanestr.append('| ') # no car in this cell
            lanestr.append('| ')
            print(''.join(lanestr))
        print('\n')

    ''' MCTS functions '''

    def get_children_gridworlds(self):
        # st()
        '''Find all children nodes from the current node for env action next'''
        # prep the agent data
        ego_pos = (self.ego_agents[0].x, self.ego_agents[0].y)
        agent_list_original = [[agent.name, agent.x, agent.y, agent.v, agent.goal] for agent in self.env_agents]
        agent_list_original = sorted(agent_list_original, key = lambda item: item[1]) # sorted by x location
        agent_list_original.reverse()
        list_of_agentlists = [agent_list_original]
        for i in range(0,len(agent_list_original)):
            list_of_agentlists_mod = []
            for agent_list in list_of_agentlists:
                agent = agent_list[i]
                actions = self.get_actions(agent,agent_list)
                for action in actions:
                    agent_list_copy = deepcopy(agent_list)
                    agent_list_copy = self.take_next_step(agent,action,agent_list_copy)
                    if agent_list_copy is not None:
                        list_of_agentlists_mod.append(agent_list_copy)
                list_of_agentlists = list_of_agentlists_mod
        list_of_gridworlds = [make_gridworld(agentlist,self.ego_agents) for agentlist in list_of_agentlists]
        return list_of_gridworlds

    def find_random_child(self):
        '''Pick a random child node'''
        if self.terminal:
            return None
        children = self.find_children()
        ran_child = choice(list(children))
        return ran_child

    def spec_check(self):
        '''Check if test spec is satisfied'''
        tester_list = []
        ego_list = []
        for tester in self.env_agents:
            tester_list.append((tester.x,tester.y))
        for ego in self.ego_agents:
            ego_list.append((ego.x,ego.y))
        for ego in ego_list:
            if (ego[0]-1,ego[1]) in tester_list and (ego[0]+1,ego[1]) in tester_list:
                return True
        return False

    def reward(self):
        '''Get reward for run'''
        # comp_reward = 5
        if not self.terminal:
            raise RuntimeError("reward called on nonterminal gridworld")
        else:
            # if self.spec_check():
            for agent in self.ego_agents:
            #agent = self.ego_agents["ego"]
                if agent.y == agent.goal:
                    # if self.spec_check():
                    return agent.x
                    # return 0#agent.x
                elif agent.x == self.width:
                    return 0 # No reward for causing the ego player to lose


    def find_children(self):
        # st()
        '''Find all children for a node'''
        if self.terminal:
            return set()
        if self.turn=="env":
            #agent = 'ag_env'
            children = set()
            count = 1
            for gi in self.get_children_gridworlds():
                children.add(gi)
        else:
            for agent in self.ego_agents:
                #agent = 'ego'
                enabled_actions = self.enabled_actions(agent)
                children = set()
                count = 1
                for ai in enabled_actions:
                    x,y = enabled_actions[ai]
                    ego_agents = [Agent(name=agent.name, x=x,y=y,v=agent.v, goal=agent.goal)]
                    gi = GridWorld(self.lanes, self.width, self.initial_scene,ego_agents=ego_agents, env_agents=self.env_agents)
                    count = count+1
                    children.add(gi)
        return children

def make_gridworld(agentdata,egodata):
    '''Create a gridworld from a list of agents'''
    env_agents = [Agent(name=agent[0], x=agent[1],y=agent[2],v=agent[3], goal=agent[4]) for agent in agentdata]
    gi = GridWorld(2, 10, [],ego_agents=egodata, env_agents=env_agents, turn="ego")
    return gi
