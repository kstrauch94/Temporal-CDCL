import subprocess
import argparse
import sys
from util import util

from Nogood import Nogood, NogoodList
from Validator import Validator
#from Minimizer import minimize

import config


def check_subsumed(ng_list, new_ng):
    # ng_list is a list of nogoods of which none is a subset of any other
    # new_ng is a nogood object

    #ng_list.append(new_ng)
    #return ng_list.copy(), True, 0
    # returns: nogood_list, success, nogoods_deleted
    # success is True if new nogood is in the list or not
    if len(ng_list) == 0:
        return [new_ng], True, 0

    nogoods_deleted = 0

    new_list = []
    failed = False
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
            ng.subsumes += 1
            failed = True
            continue

        if failed:
            # only keep going to see if other nogoods subsume the new one also
			# and increment the subsumes value accordingly
            continue
        # if new is not a subset of the nogood in the list()
        # then add the old nogood to the list
        if not new_ng.issubset(ng):
            new_list.append(ng)
        else:
            new_ng.subsumes += ng.subsumes
            nogoods_deleted += 1

    if failed:
        return None, False, 0

    # at this point we have deleted all supersets of the new nogood
    # so we add the new nogood to the list and return it
    # also the amount of deleted nogoods is added to the subsumed amount of new nogood
    new_ng.subsumes += nogoods_deleted
    new_list.append(new_ng)

    return new_list, True, nogoods_deleted


def get_sort_value(object, attributes):
    val = []

    for attr in attributes:
        val.append(getattr(object, attr))

    return val


def call_clingo_pipe(file_names, time_limit, memory_limit, options):
    # TODO
    # rewrite so that it ONLY returns the pipe!
    # is it confusing to have the collect inside this aswell
    CLINGO = [config.RUNSOLVER_PATH, "--real-time-limit={}".format(time_limit),
              "-o", "runsolver.produce.watcher"]

    if memory_limit is not None:
        CLINGO += ["--space-limit={}".format(memory_limit)]

    CLINGO += [config.CLINGO] + file_names

    call = CLINGO + options

    print("calling: " + " ".join(call))

    pipe = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    return pipe

@util.Timer("collect")
def collect_nogoods(output, ng_list, process_limit=None, gen_t="T", max_size=None, max_degree=None, max_lbd=None, horn_filter=None, no_subsumption=False, degreem1=False, supress_output=False):
    import re
    split_atom_re = r",\s+(?=[^()]*(?:\(|$))"
    for order, line in enumerate(output):
        if type(line) != str:
            line = line.decode("utf-8")

        if process_limit is not None and process_limit < order:
            print(f"breaking {process_limit} {order}")
            return

        if line.startswith(":-") and "." in line and "__atom" not in line:
            ## __atom refers to auxiliary atoms, we can not parse those
            try:
                if max_size is not None:
                    pre_lits = Nogood.split_raw_constraint(line)
                    if len(pre_lits) > max_size:
                        continue

                ng = Nogood(line, order=order, degreem1=degreem1)
            except AttributeError:
                # in this case the line was not written properly in the output_file
                continue
            except RuntimeError:
                # in this case, somehow a bad line for into the nogood and the parse term gave an error, probably
                print("bad line: " + line, file=sys.stderr)
                continue

            util.Count.add("Total nogoods")

            if (max_degree is not None and max_degree < ng.degree) or \
               (max_lbd is not None and max_lbd < ng.lbd) or \
                (horn_filter is not None and ((horn_filter=="pos" and ng.horn_pos) or (horn_filter=="neg" and ng.horn_neg) or (horn_filter=="any" and ng.horn_any)) ):
                util.Count.add("skipped")
                continue

            ng.generalize(gen_t)
            if no_subsumption:
                ng_list.append(ng)
                continue
            with util.Timer("subsumption"):
                new_ng_list, success, deleted = check_subsumed(ng_list, ng)
                if success:
                    ng_list.replace(new_ng_list)
                    util.Count.add("nogoods subsumed", deleted)
                else:
                    util.Count.add("nogoods subsumed", 1)

        else:
            if supress_output:
                continue
            print(line, end="")
    #for ng in ng_list:
    #    print(ng.to_general_constraint())

    #print("call has finished\n")


def process_ng_list(ng_list, nogoods_wanted=None, sort_by=None, sort_reversed=False, validator=None):

    if sort_by is not None:
        ng_list.sort(key=lambda nogood : get_sort_value(nogood, sort_by), reverse=sort_reversed)

    #minimize(ng_list, 0)

    if validator is not None:
        validated = validator.validate_list(ng_list, nogoods_wanted=nogoods_wanted)
        ng_list.replace(validated)
    else:
        ng_list.replace(ng_list[:nogoods_wanted])

    return ng_list

def find_persistence(ng_list):
    print("Trying to find persistence...")
    for ng in ng_list:
        if ng.size == 2:
            util.Count.add("size 2", 1)
            if ng.is_horn_clause():
                util.Count.add("horn of size 2!", 1)
                if ng.gen_literals[0].same_without_time_and_sign(ng.gen_literals[1]):
                    util.Count.add("persistent?", 1)
                    print(f"persistent?:\n{ng.to_general_constraint()}")
    print("finished with persistence!")


def find_persistence_gen(ng_list):
    print("Trying to find persistence gen...")
    for ng in ng_list:
        if ng.size not in range(3, 4+1):
            continue
        util.Count.add("size 3 or 4", 1)
        if not ng.is_horn_clause():
            continue

        if ng.horn_pos:
            atoms = ng.pos_atoms
            rev_atom = ng.neg_atoms[0]
        else:
            atoms = ng.neg_atoms
            rev_atom = ng.pos_atoms[0]
        util.Count.add("tested", 1)
        for test in range(len(atoms)):
            if ng.gen_literals[test].same_without_time_and_sign(rev_atom):
                util.Count.add("persistent?", 1)
                print(f"persistent?:\n{ng.to_general_constraint()}")
                break

    print("finished with persistence!")

def write_ng_list_to_file(ng_list, generalized=True, file_name="nogoods.lp"):

    with open(file_name, "w") as _f:
        for ng in ng_list:
            if generalized:
                _f.write(ng.to_general_constraint()+"\n")
            else:
                _f.write(ng.to_constraint()+"\n")


def extract_stats(ng_list):

    lbd_sum = 0
    size_sum = 0

    max_size = 0
    max_lbd = 0
    max_degree = 0

    for ng in ng_list:
        lbd_sum += ng.lbd
        size_sum += ng.size

        max_size = max(max_size, ng.size)
        max_lbd = max(max_lbd, ng.lbd)
        max_degree = max(max_degree, ng.degree)

    print(f"avg lbd : {lbd_sum/len(ng_list)}")
    print(f"avg size: {size_sum/len(ng_list)}")

    print(f"max size : {max_size}")
    print(f"max lbd : {max_lbd}")
    print(f"max degree : {max_degree}")


def print_stats():

    for name, count in util.Count.counts.items():
        print(f"{name:24}  :   {count}")

    for name, time_taken in sorted(util.Timer.timers.items()):
        print(f"{name:19}  :   {time_taken:.3f}")

def main():

    parser = argparse.ArgumentParser()

    domain_args = parser.add_argument_group("Domain input")

    domain_args.add_argument('--files', metavar='f', nargs='+', help="Files to run clingo on not including instance")
    domain_args.add_argument('--instance', metavar='i', nargs='+', help="Instance file. If file has a .pddl extension it will be treated as a pddl instance.")
    domain_args.add_argument("--validate-files", nargs='+', help="file used to validate learned constraints. If no file is provided validation is not performed.", default=None)
    domain_args.add_argument("--val-walltime", help="Walltime for the validation of each nogood in seconds. Default is no walltime.", default=None)

    domain_args.add_argument("--horizon", help="horizon will be added to clingo -c horizon=<h>", type=int, default=None)

    processing = parser.add_argument_group("Processing options")

    processing.add_argument("--output-file", help="name of the file that the generalized nogoods will be saved to. Default=nogoods.lp", default="nogoods.lp")
    processing.add_argument("--use-existing-file", help="Process an existing nogood file.", metavar="file", default=None)

    processing.add_argument("--sort-by", help="Attributes(comma separated) that will sort the nogood list. The order of the attributes is the sorting order. Choose from [degree, literal_count, order, lbd, random_id, horn_pos, r_horn_pos, horn_neg, r_horn_neg]. default: None", default=None)
    processing.add_argument("--sort-reversed", action="store_true", help="Reverse the sort order.")
    processing.add_argument("--inc-t", action="store_true", help="use the incremental 't' instead of the normal 'T'")

    processing.add_argument("--max-degree", help="Processing will ignore nogoods with higher degree. Default = None", default=None, type=int)
    processing.add_argument("--max-size", help="Processing will ignore nogoods with higher literal count. Default = None.", default=None, type=int)
    processing.add_argument("--max-lbd", help="Processing will ignore nogoods with higher lbd. Default = None.", default=None, type=int)
    processing.add_argument("--horn-filter", help="Processing will ignore nogoods that are not horn clauses", choices=["pos","neg","any"], default=None)

    processing.add_argument("--nogoods-wanted", help="Nogoods processed will stop after this amount. Default = None", default=None, type=int)
    processing.add_argument("--degreem1", action="store_true", help="degree will be calculated using the max - min otime instead of max - min - 1")

    processing.add_argument("--no-subsumption", action="store_true", help="Skip subsumption of atom")

    processing.add_argument("--nogoods-limit", help="Solving will only find up to this amount of nogoods for processing. Default = None", default=None, type=int)
    processing.add_argument("--max-extraction-time", default=20, type=int, help="Time limit for nogood extraction in seconds. Default = 20")
    processing.add_argument("--memory-limit", default=None, type=int, help="Memory limit for nogood extraction in MB. Default = None")

    processing.add_argument("--solver-args", help="Add extra clingo arguments to the learning solve call as given here. give arguments inside quotation marks", default=None)
    processing.add_argument("--supress-output", help="supress the output of the clingo call", action="store_true")


    other = parser.add_argument_group("Other options")

    other.add_argument("--runsolver", help="Path to the runsolver binary. Default is current directory.", default=None)
    other.add_argument("--clingo", help="Clingo call to use. Default is \"clingo\".", default=None)

    args = parser.parse_args()

    if args.instance is None:
        raise argparse.ArgumentTypeError(args.instance, "Instance can not be empty")

    if args.files is None:
        raise argparse.ArgumentTypeError(args.files, "Files can not be empty")

    if args.runsolver is not None:
        config.RUNSOLVER_PATH = args.runsolver

    if args.clingo is not None:
        config.CLINGO = args.clingo

    NG_RECORDING_OPTIONS = ["--lemma-out-txt",
                    "--lemma-out=-",
                    "--lemma-out-dom=output",
                    "--quiet=2",
                    "--stats"]

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

    if args.max_lbd is not None:
        options += [f"--lemma-out-lbd={args.max_lbd}"]

    if args.solver_args is not None:
        options += args.solver_args.split()
    
    if args.sort_by is not None:
        args.sort_by = args.sort_by.split(",")

    # generalize using the normal variable or incremental variable
    gen_t = "T"
    if args.inc_t:
        gen_t = "t"

    collect_kwargs = {"gen_t": gen_t, 
                    "process_limit": args.nogoods_limit, 
                    "max_degree": args.max_degree, 
                    "max_size": args.max_size, 
                    "max_lbd": args.max_lbd,
                    "horn_filter": args.horn_filter,
                    "no_subsumption": args.no_subsumption, 
                    "degreem1": args.degreem1, 
                    "supress_output": args.supress_output}

    # grab the nogood list
    with util.Timer("Collect Nogoods"):
        ng_list = NogoodList()
        if args.use_existing_file:
            with open(args.use_existing_file, "r") as _f:
                collect_nogoods(_f.readlines(), ng_list, **collect_kwargs)
        else:
            cpipe = call_clingo_pipe(encoding+instance, args.max_extraction_time, args.memory_limit, options=options)

            collect_nogoods(cpipe.stdout, ng_list, **collect_kwargs)
            print("killing process...")
            #cpipe.kill()
            cpipe.terminate()
            print("killed")
            stdout, stderr = cpipe.communicate()
            print(stdout)

    util.Count.add("Nogoods after filter", len(ng_list))

    # find persistence
    #find_persistence(ng_list)
    #find_persistence_gen(ng_list)

    with util.Timer("Process Nogoods"):
        # Process nogoods
        process_ng_list(ng_list, nogoods_wanted=args.nogoods_wanted, sort_by=args.sort_by, sort_reversed=args.sort_reversed, validator=validator)

    util.Count.add("Nogoods after processing", len(ng_list))

    # output file
    write_ng_list_to_file(ng_list, file_name=args.output_file)

    extract_stats(ng_list)

    print_stats()


if __name__ == "__main__":
    main()
