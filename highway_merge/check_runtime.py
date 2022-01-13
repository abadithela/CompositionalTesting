import numpy as np
import matplotlib.pyplot as plt
import time
import os
import pickle
from ipdb import set_trace as st
from merge_receding_horizon_winsets import get_tester_states_in_winsets, specs_car_rh, get_winset_rh
from winning_set.correct_win_set import specs_for_entire_track, make_grspec, Spec, WinningSet, check_all_states_in_winset


def compute_winning_set_and_save_time(tracklength):
    merge_setting = "between"
    print('Synthesizing for {}'.format(tracklength))
    # compute here:
    ego_spec, test_spec, Vij_dict, state_tracker, ver2st_dict, G, state_dict_test, state_dict_system = specs_car_rh(tracklength, merge_setting)
    Wij = dict()
    # Go through all the goal states
    # st()
    t_winset_all_goals = 0
    tic = time.time()
    for i, key in enumerate(Vij_dict.keys()):
        tic2 = time.time()
        Wj, t_goal = get_winset_rh(tracklength, merge_setting, Vij_dict[key], state_tracker, ver2st_dict,ego_spec, test_spec, state_dict_test, state_dict_system, G)
        toc2 = time.time()
        delta_t2 = toc2 - tic2
        print('Goal {0} takes {1} s'.format(i,delta_t2))
        Wij.update({key: Wj})
        t_winset_all_goals += t_goal

    # Wij, Vij_dict, state_tracker, ver2st_dict = get_tester_states_in_winsets(tracklength, merge_setting)
    toc = time.time()
    delta_t = toc - tic
    save_winning_set(tracklength, Wij, Vij_dict, state_tracker, ver2st_dict)
    return delta_t, delta_t2, t_winset_all_goals

def save_winning_set(tracklength, Wij, Vij_dict, state_tracker, ver2st_dict):
    # save objects in dictionary
    ws = dict()
    ws.update({'Wij': Wij})
    ws.update({'Vij_dict': Vij_dict})
    ws.update({'state_tracker': state_tracker})
    ws.update({'ver2st_dict': ver2st_dict})
    # save dict in pkl file
    output_dir = os.getcwd()+'/saved_wsets/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filename = 'ws_out_file_'+str(tracklength)+'.p'
    filepath = output_dir + filename
    print('Saving winning set in pkl file')
    with open(filepath, 'wb') as pckl_file:
        pickle.dump(ws, pckl_file)

def plot_the_times(tracklength, times):
    # plt.style.use('_mpl-gallery')
    # st()
    # make data
    x = tracklength
    y = []
    for l in tracklength:
        y.append(times[l])

    # plot
    fig, ax = plt.subplots()

    plt.plot(x, y, linewidth=2.0)

    # ax.set(xlim=(0, 8), xticks=np.arange(1, 8),
    #        ylim=(0, 8), yticks=np.arange(1, 8))

    plt.xlabel('track length')
    plt.ylabel('time [s]')
    plt.title('Highway Merge: Runtime vs. Tracklength', fontsize = 15)

    plt.savefig('ws_runtime.png', dpi = 200, bbox_inches='tight')
    plt.savefig('ws_runtime.pdf', bbox_inches='tight')
    plt.show()

def original_specs():
    Lmax = 10 # Maximum tracklength
    tracklength = np.linspace(5, Lmax, Lmax-5+1)
    tracklength = [int(tli) for tli in tracklength]
    times = []
    for l in tracklength:

        ego_spec, test_spec = specs_for_entire_track(l)
        gr_spec = make_grspec(test_spec, ego_spec) # Placing test_spec as sys_spec and sys_spec as env_spec to
        print(gr_spec.pretty())

        w_set = WinningSet()
        tic = time.time()
        w_set.set_spec(gr_spec)
        aut = w_set.make_compatible_automaton(gr_spec)
        # g = synthesize_some_controller(aut)
        agentlist = ['x1', 'x2']
        fp = w_set.find_winning_set(aut)
        print("Printing states in fixpoint: ")
        # states_in_fp, states_out_fp = check_all_states_in_fp(tracklength, agentlist, w_set, fp, aut)
        print(" ")
        print("Printing states in winning set: ")
        mode="between"
        states_in_winset = check_all_states_in_winset(l, agentlist, w_set, fp, aut, mode)
        toc = time.time()
        times.append(toc-tic)
    return tracklength, times

def save_times(tracklength,times,filename='times_file.p'):
    save_dict = dict()
    save_dict.update({'tracklength': tracklength})
    save_dict.update({'times': times})
    # save dict in pkl file
    output_dir = os.getcwd()+'/saved_data/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filepath = output_dir + filename
    print('Saving data in pkl file')
    with open(filepath, 'wb') as pckl_file:
        pickle.dump(save_dict, pckl_file)


if __name__=='__main__':
    print('Checking runtime for winning set synthesis')
    Lmax = 10 # Maximum tracklength
    tracklength = np.linspace(5, Lmax, Lmax-5+1)
    # tracklength = [5, 20]
    tracklength = [int(tli) for tli in tracklength]
    tracklength=[3]
    times = dict()

    for l in tracklength:
        t, t2, t_all_goals = compute_winning_set_and_save_time(l)
        print("Synthesizing winning set for all goals takes {0}".format(t_all_goals))
        print('Tracklength: {0} took {1} s total and {2} for one single goal'.format(l,t,t2))
        times.update({l:t})
        # st()
    print(times)
    save_times(tracklength,times)

    tracklength, times = original_specs()
    print(times)
    save_times(tracklength,times,filename='orig_times_file.p')
    
    # plot_the_times(tracklength, times)
