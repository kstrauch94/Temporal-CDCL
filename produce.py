import subprocess
import re
import errno
import argparse

from util import util

from Nogood import Nogood
from Validator import Validator
import config

from collections.abc import MutableSequence


class Nogood_List(MutableSequence):
    """A container for manipulating lists of hosts"""
    def __init__(self, data=None):
        """Initialize the class"""
        super(Nogood_List, self).__init__()
        if (data is not None):
            self._list = list(data)
        else:
            self._list = list()

    def replace(self, list):
        self._list = list

    def sort(self, *args, **kwargs):
        return self._list.sort(*args, **kwargs)

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self._list)

    def __len__(self):
        """List length"""
        return len(self._list)

    def __getitem__(self, ii):
        """Get a list item"""
        return self._list[ii]

    def __delitem__(self, ii):
        """Delete an item"""
        del self._list[ii]

    def __setitem__(self, ii, val):
        # optional: self._acl_check(val)
        self._list[ii] = val

    def __str__(self):
        return str(self._list)

    def insert(self, ii, val):
        # optional: self._acl_check(val)
        self._list.insert(ii, val)

    def append(self, val):
        self.insert(len(self._list), val)

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

def minimize(nogood):
    pass #TODO

def get_sort_value(object, attributes):
    val = []

    for attr in attributes:
        val.append(getattr(object, attr))

    return val

def call_clingo_pipe(file_names, ng_list, time_limit, process_limit, options, raw_file=None, gen_t="T", max_size=None, max_degree=None, max_lbd=None):

    CLINGO = [config.RUNSOLVER_PATH, "-W", "{}".format(time_limit),
              "-w", "runsolver.cdcl.watcher", "-d", "20",
              "clingo"] + file_names

    call = CLINGO + options

    #print("calling: " + " ".join(call))

    pipe = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    if raw_file is not None:
        with open(raw_file, "w") as _f:
            collect_nogoods(pipe.stdout, ng_list, process_limit, raw_file=_f, gen_t=gen_t, max_size=max_size, max_degree=max_degree, max_lbd=max_lbd)
    else:
        collect_nogoods(pipe.stdout, ng_list, process_limit, gen_t=gen_t, max_size=max_size, max_degree=max_degree, max_lbd=max_lbd)

    pipe.kill()

def collect_nogoods(output, ng_list, process_limit=None, raw_file=None, gen_t="T", max_size=None, max_degree=None, max_lbd=None):

    for order, line in enumerate(output):
        line = line.decode("utf-8")

        if process_limit is not None and process_limit < order:
            #print(f"breaking {process_limit} {order}")
            break

        if line.startswith(":-") and "." in line:

            try:
                ng = Nogood(line, order=order)
            except AttributeError:
                # in this case the line was not written properly in the output_file
                break
            util.Count.add("Total nogoods")
            if raw_file is not None:
                raw_file.write(line)

            if max_size is not None and max_size < len(ng) or \
               max_degree is not None and max_degree < ng.degree or \
               max_lbd is not None and max_lbd < ng.lbd:
                util.Count.add("skipped")
                continue
            

            ng.generalize(gen_t)
            with util.Timer("subsumption"):
                new_ng_list, success, deleted = check_subsumed(ng_list, ng)
                ng_list.replace(new_ng_list)

            util.Count.add("nogoods subsumed", deleted)
            

        #else:
        #    print(line, end="")


    #for ng in ng_list:
    #    print(ng.to_general_constraint())

    #print("call has finished\n")


def clingo_pipe_multiple_calls(file_names, ng_list, time_limit, nogoods_per_step, nogoods_wanted, options, raw_file=None, gen_t="T", max_size=None, max_degree=None, max_lbd=None):

    ng_file_name = "ng_file.tmp"
    with open(ng_file_name, "w") as _f:
        # only here to create the file
        pass

    while 1:
        with util.Timer("pipe calls"):
            # after getting all the nogoods, write them into a file and call the solver again with the nogoods
            call_clingo_pipe(file_names + [ng_file_name], ng_list, time_limit, nogoods_per_step, options=options, 
                            raw_file=raw_file, gen_t=gen_t, max_size=max_size, max_degree=max_degree, max_lbd=max_lbd)

            with open(ng_file_name, "w") as _f:
                # write nogoods to file
                for ng in ng_list:
                    _f.write(ng.to_general_constraint()+"\n")

        print(f"Collected nogoods: {len(ng_list)}  ,total {util.Count.counts['Total nogoods']}  ,sub {util.Count.counts['nogoods subsumed']} , skip {util.Count.counts['skipped']} \r", end="")
        
        if util.Timer.timers["pipe calls"] > time_limit:
            break

        elif nogoods_wanted is not None and len(ng_list) >= nogoods_wanted:
            break

def process_ng_list(ng_list, nogoods_wanted=None, sort_by=None, sort_reversed=False, validator=None):

    if sort_by is not None:
        ng_list.sort(key=lambda nogood : get_sort_value(nogood, sort_by), reverse=sort_reversed)

    if validator is not None:
        ng_list = validator.validate_list(ng_list, nogoods_wanted=nogoods_wanted)
    else:
        ng_list = ng_list[:nogoods_wanted]

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

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    domain_args = parser.add_argument_group("Domain input")

    domain_args.add_argument('--files', metavar='f', nargs='+', help="Files to run clingo on not including instance")
    domain_args.add_argument('--instance', metavar='i', nargs='+', help="Instance file. If file has a .pddl extension it will be treated as a pddl instance.")
    domain_args.add_argument("--validate-files", nargs='+', help="file used to validate learned constraints. If no file is provided validation is not performed.", default=None)
    domain_args.add_argument("--val-walltime", help="Walltime for the validation of each nogood in seconds. Default is no walltime.", default=None)

    domain_args.add_argument("--horizon", help="horizon will be added to clingo -c horizon=<h>", type=int, default=None)

    processing = parser.add_argument_group("Processing options")

    processing.add_argument("--output-file", help="name of the file that the generalized nogoods will be saved to. Default=nogoods.lp", default="nogoods.lp")
    processing.add_argument("--regular-ng-file", help="Name of the file containing the raw nogoods from clingo. Default=None", default=None)
    processing.add_argument("--use-existing-file", help="Process an existing nogood file.", metavar="file", default=None)

    #processing.add_argument("--grab-last", action="store_true", help="Grab the last N nogoods.")
    processing.add_argument("--sort-by", nargs='+', help="attributes that will sort the nogood list. The order of the attributes is the sorting order. Choose from [degree, literal_count, order, lbd, random_id]. default: None", default=None)
    processing.add_argument("--sort-reversed", action="store_true", help="Reverse the sort order.")
    processing.add_argument("--inc-t", action="store_true", help="use the incremental 't' instead of the normal 'T'")

    processing.add_argument("--max-degree", help="Processing will ignore nogoods with higher degree. Default = None", default=None, type=int)
    processing.add_argument("--max-size", help="Processing will ignore nogoods with higher literal count. Default = None.", default=None, type=int)
    processing.add_argument("--max-lbd", help="Processing will ignore nogoods with higher lbd. Default = None.", default=None, type=int)
    processing.add_argument("--nogoods-wanted", help="Nogoods processed will stop after this amount. Default = None", default=None, type=int)

    processing.add_argument("--multi-calls-step", help="Run clingo multiple times using the cummulated nogoods found in each subsequent call", default=None, type=int)

    processing.add_argument("--nogoods-limit", help="Solving will only find up to this amount of nogoods for processing. Default = None", default=None, type=int)
    processing.add_argument("--max-extraction-time", default=20, type=int, help="Time limit for nogood extraction in seconds. Default = 20")

    other = parser.add_argument_group("Other options")

    other.add_argument("--runsolver", help="Path to the runsolver binary. Default is current directory.", default=None)

    args = parser.parse_args()

    if args.instance is None:
        raise argparse.ArgumentTypeError(args.instance, "Instance can not be empty")

    if args.files is None:
        raise argparse.ArgumentTypeError(args.files, "Files can not be empty")

    if args.runsolver is not None:
        config.RUNSOLVER_PATH = args.runsolver

    NG_RECORDING_OPTIONS = ["--lemma-out-txt",
                    "--lemma-out=-",
                    "--lemma-out-dom=output",
                    "--quiet=2",
                    "--stats"]

    encoding = ["encodings/Hanoi.asp", "encodings/assumption-solver.py"]
    instance = ["test-instances/hanoitest.asp"]

    validation_files = ["validation-encoding/hanoi-validation.lp", "encodings/assumption-solver.py"] + instance

    # deal with encoding and validation files
    encoding = args.files
    instance = args.instance

    if args.validate_files is not None:
        validator = Validator(args.validate_files + args.instance, args.val_walltime)
    else:
        validator = None

    # deal with extra arguments given to clingo
    options = NG_RECORDING_OPTIONS.copy()

    if args.nogoods_limit is not None:
        options += [f"--lemma-out-max={args.nogoods_limit}"]

    if args.horizon is not None:
        options += [f"-c horizon={args.horizon}"]

    # generalize using the normal variable or incremental variable
    gen_t = "T"
    if args.inc_t:
        gen_t = "t"

    # grab the nogood list
    with util.Timer("Collect Nogoods"):
        ng_list = Nogood_List()
        if args.use_existing_file:
            collect_nogoods(args.use_existing_file, ng_list, gen_t=gen_t, max_degree=args.max_degree, max_size=args.max_size, max_lbd=args.max_lbd)
        elif args.multi_calls_step is None:
            call_clingo_pipe(encoding+instance, ng_list, args.max_extraction_time, options, raw_file=args.regular_ng_file, gen_t=gen_t, max_degree=args.max_degree, max_size=args.max_size, max_lbd=args.max_lbd)
        else:
            clingo_pipe_multiple_calls(encoding+instance, ng_list, args.max_extraction_time, args.multi_calls_step, args.nogoods_wanted, options, raw_file=args.regular_ng_file, gen_t=gen_t, max_degree=args.max_degree, max_size=args.max_size, max_lbd=args.max_lbd)

    util.Count.add("Nogoods after filter", len(ng_list))

    with util.Timer("Process Nogoods"):
        # Process nogoods
        process_ng_list(ng_list, sort_by=args.sort_by, sort_reversed=args.sort_reversed, validator=validator)

    # output file
    write_ng_list_to_file(ng_list, file_name=args.output_file)

    print_stats()
