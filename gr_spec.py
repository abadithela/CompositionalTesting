#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  8 12:35:06 2021

@author: apurvabadithela
"""
# Ego: system
# Env: tester
# This file is to generate the GR1 specifications associated with the merge example abstraction
from __future__ import print_function
import logging
import numpy as np
from tulip import spec, synth, hybrid, transys
from polytope import box2poly
from tulip.abstract import prop2part, discretize
from tulip.abstract.plot import plot_partition
from tulip.dumpsmach import write_python_case
from tulip.spec.gr1_fragment import response_to_gr1

def design_spec(env_vars, sys_vars, env_init, sys_init, env_safe, sys_safe, env_prog, sys_prog):
    logging.basicConfig(level=logging.WARNING)
    show = False

    # Constructing GR1spec from environment and systems specifications:
    specs = spec.GRSpec(env_vars, sys_vars, env_init, sys_init,
                        env_safe, sys_safe, env_prog, sys_prog)
    return spec

def add_property(prop_set, new_prop):
    prop_set |= new_prop
    return prop_set

def var_setup():
    sys_vars = {}
    tester_vars = {}
    sys_vars['x'] = (1, 4)
    tester_vars['y'] = ((1,2)
    return sys_vars, tester_vars
