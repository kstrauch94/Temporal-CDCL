from lib2to3.pgen2 import literals
import os
import subprocess
import re
import sys
import errno
import argparse
import operator
import logging
from collections import Counter

from util import util

from Nogood import Nogood
from Validator import Validator

import random

def check_subsumed(ng_list, new_ng):
    # ng_list is a list of nogoods of which none is a subset of any other
    # new_ng is a nogood object

    # returns: nogood_list, success, nogoods_deleted
    # success is True if new nogood is in the list or not
    if ng_list == []:
        return [new_ng], True, 0

    nogoods_deleted = 0

    new_list = []
    for ng in ng_list:
        # remember to check if the T>0 is there or not!!

        # if nogood is useless
        if ng.issubset(new_ng):
            # new nogood is now irrelevant
            # because if this nogood already in the list is a subset
            # we dont really need the new nogood anymore
            # and also, any nogood that would be made irrelevant
            # by the new one should not be in the list
            # since we have a subset of that nogood already in the list 
            # so we just return the old list
            return ng_list, False, 0

        # if new is not a subset of the nogood in the list()
        # then add the old nogood to the list
        if not new_ng.issubset(ng):
            new_list.append(ng)
        else:
            nogoods_deleted += 1

    # at this point we have deleted all supersets of the new nogood
    # so we add the new nogood to the list and return it
    new_list.append(new_ng)

    return new_list, True, nogoods_deleted

def get_sort_value(object, attributes):
    val = []

    for attr in attributes:
        val.append(getattr(object, attr))

    return val

def call_clingo_pipe(file_names, time_limit, options, gen_t="T", max_size=None, max_degree=None, max_lbd=None):

    CLINGO = ["./runsolver", "-W", "{}".format(time_limit), 
              "-w", "runsolver.watcher", "-d", "20", 
              "clingo"] + file_names

    call = CLINGO + options

    print("calling: " + " ".join(call))

    pipe = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    ng_list = []

    for order, line in enumerate(pipe.stdout):
        line = line.decode("utf-8")
        if line.startswith(":-") and "." in line:
            util.Count.add("Total nogoods")
            ng = Nogood(line, order=order)

            if max_size is not None and max_size < len(ng) or \
               max_degree is not None and max_degree < ng.degree or \
               max_lbd is not None and max_lbd < ng.lbd:
                continue

            ng.generalize(gen_t)
            ng_list, success, deleted = check_subsumed(ng_list, ng)
            util.Count.add("nogoods subsumed", deleted)


    for ng in ng_list:
        print(ng.to_general_constraint())

    util.Count.add("Nogoods after filter", len(ng_list))

    print("call has finished\n")

    return ng_list

def process_ng_list(ng_list, sort_by=None, sort_reversed=False, validator=None):

    ng_list = validator.validate_list(ng_list)

    if sort_by is not None:
        ng_list.sort(key=lambda nogood : get_sort_value(nogood, sortby), reverse=sort_reversed)
    
    return ng_list

def write_ng_list_to_file(ng_list, generalized=True, file_name="nogoods.lp"):

    with open(file_name, "w") as _f:
        for ng in ng_list:
            if generalized:
                _f.write(ng.to_general_constraint()+"\n")
            else:
                _f.write(ng.to_constraint()+"\n")


def print_stats():

    for name, count in util.Count.counts.items():
        print(f"{name:24}  :   {count}")

    for name, time_taken in sorted(util.Timer.timers.items()):
        print(f"{name:19}  :   {time_taken:.3f}")

NG_RECORDING_OPTIONS = ["--lemma-out-txt",
                    "--lemma-out=-",
                    "--lemma-out-dom=output", 
                    "--quiet=2",
                    "--stats"]

encoding = ["encodings/Hanoi.asp", "encodings/assumption-solver.py"]
instance = ["test-instances/hanoitest.asp"]          

validation_files = ["validation-encoding/hanoi-validation.lp", "encodings/assumption-solver.py"] + instance
ng_list = call_clingo_pipe(encoding+instance, 100, NG_RECORDING_OPTIONS, max_lbd=2)

validator = Validator(validation_files)

process_ng_list(ng_list, validator=validator)

write_ng_list_to_file(ng_list)

print_stats()
