import os
import subprocess
import re
import sys
import errno
import argparse
import operator
import logging
import time
import config_file
from tools.tools import setup_logging, plasp_translate, plasp2_translate, get_parent_dir, create_folder

DEBUG = False

match_time = r"Time         : (\d+\.\d+)s"
match_time_solve = r"Solving: (\d+\.\d+)s"

global RUNSOLVER_PATH

def call_clingo(file_names, time_limit, options):
    #  TODO: use runsolver here to manage the max time and such

    CLINGO = [RUNSOLVER_PATH, "-W", "{}".format(time_limit), \
              "-w", "runsolver.watcher", "clingo"] + file_names + ["--stats", "--quiet=2"]

    call = CLINGO + options

    logging.info("calling: " + " ".join(call))

    try:
        output = subprocess.check_output(call).decode("utf-8")
    except subprocess.CalledProcessError as e:
        output = e.output.decode("utf-8")

    logging.debug("call has finished\n")

    return output

def eval_re(regex, text, group, default):

    try:
        return re.search(regex, text).group(group)
    except AttributeError:
        return default

def parse_call_results(output):
    # here i will parse the results of ONE call
    # return a dict with the results

    res = {"time" : 0,
           "solving" : 0,
           "success": None,
           "raw": output
          }

    res["time"] = float(eval_re(match_time, output, 1, res["time"]))

    res["solving"] = float(eval_re(match_time_solve, output, 1, res["solving"]))

    try:
        if re.search(r"UNSATISFIABLE", output) is not None:
            res["success"] = "UNSAT"
            logging.info(output)
        elif re.search(r"SATISFIABLE", output) is not None:
            res["success"] = "SAT"
        elif re.search(r"UNKNOWN", output) is not None:
            res["success"] = "UNKNOWN"
    except AttributeError:
        pass    

    return res

def read_nogoods(nogood_file):

    with open(nogood_file, "r") as f:
        nogoods = f.readlines()

    return nogoods

def write_nogood_partial(nogoods, filename="nogood.temp", debug=False, fileid=0):

    with open(filename, "w") as f:
        f.writelines(nogoods)

    if debug:
        # if debug is on, write a file with the nogoods that won't get deleted
        # fileid should be the scaling so that you can see for which run this file was used

        with open(filename+"debug.{}".format(fileid), "w") as f:
            f.writelines(nogoods)

def run_tests(files, nogood_file, scaling, labels, max_scaling=0, time_limit=0, horizon=None, no_base_run=False):

    logging.info("Starting nogood consumption...")

    noogood_temp_name = "nogood.temp"
    options = []

    if horizon is not None:
        options += ["-c", "horizon={}".format(horizon)]

    results = {}

    nogoods = read_nogoods(nogood_file)
    total_nogoods = len(nogoods)


    if not no_base_run:
        # do a base run
        logging.info("base run")
        output = call_clingo(files, time_limit, options)
        results["base"] = output
        logging.info(output)

    # runs with scaling
    for nogood_current, label in zip(scaling, labels):
        if nogood_current > 0 and nogood_current > total_nogoods:
            logging.info("Finishing early. Trying to use {} nogoods but only {} are available.".format(nogood_current, total_nogoods))
            break

        # if this run has a current scaling higher than the max, break
        if nogood_current > 0 and max_scaling > 0 and nogood_current > max_scaling:
            logging.info("Finishing early. Current scaling of {} is higher than max scaling: {}".format(nogood_current, max_scaling))
            break

        logging.info("Current scaling: {}".format(nogood_current))

        if nogood_current == -1:
            write_nogood_partial(nogoods[:], noogood_temp_name, debug=DEBUG, fileid=nogood_current)
        else:
            write_nogood_partial(nogoods[:nogood_current], noogood_temp_name, debug=DEBUG, fileid=nogood_current)

        output = call_clingo(files + [noogood_temp_name], time_limit, options)
        results[label] = output

        logging.info(output)

    try:
        os.remove(noogood_temp_name)
    except OSError:
        logging.info("Failed to delete the nogood temp file.(Might not exist)")

    return results

def consume(files, nogood_file, scaling_list=None, scaling_exp=None, max_scaling=0, time_limit=0, labels=None, horizon=None, no_base_run=False):
    # scaling type can be "by_value" or "by_factor"
    # by_value means just passing a list with amount of nogoods, those amounts will be used in the runs
    # by factor means passing 3 argument, start amount, scaling factor and total runs
    # a scaling by factor of 8,2,5 means doing 5 runs starting at 8 increasing by a factor of 2
    # so: 8,16,32,64,128
    # a base run is always done

    if scaling_list is not None and scaling_exp is not None:
        logging.error("only one scaling can be provided at a time. Use either --scaling-list or --scaling-exp")
        sys.exit(1)

    if scaling_exp is not None:
        scaling_split = scaling_exp.split(",")

        if len(scaling_split) != 3:
            logging.error("scaling has to contain exactly 3 values!")
            raise ValueError

        scaling_start = int(scaling_split[0])
        scaling_factor = float(scaling_split[1])
        scaling_count = int(scaling_split[2])

        scaling = []
        for i in range(scaling_count):
            scaling.append(int(scaling_start * scaling_factor**i))
        
        scaling_labels=scaling

    if scaling_list is not None:
        if type(scaling_list) == str:
            # this comes from the command line
            scaling_split = scaling_list.split(",")
            scaling = [int(s) for s in scaling_split]
        elif type(scaling) == list:
            scaling = [int(s) for s in scaling_split]
        
        if labels is not None:
            scaling_labels = labels
        else:
            scaling_labels = scaling

    return run_tests(files, nogood_file, scaling, scaling_labels, \
            max_scaling=max_scaling, time_limit=time_limit, horizon=horizon, \
            no_base_run=no_base_run)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--files", metavar='f', nargs='+', help="Files to run clingo on")
    parser.add_argument("--nogoods", help="File holding the processed nogoods")
    parser.add_argument("--scaling-list", help="Perform scaling by the values provided. A scaling of -1 signifies the use of ALL nogoods.", default=None)

    parser.add_argument("--horizon", help="horizon will be added to clingo -c horizon=<h>", type=int, default=None)
    parser.add_argument("--time-limit", type=int, help="time limit per call in seconds. Default=300", default=300)
    parser.add_argument("--no-base-run", action="store_true", help="Do not do the base run", default=False)

    parser.add_argument("--pddl-instance", help="pddl instance")
    parser.add_argument("--pddl-domain", help="pddl domain")
    parser.add_argument("--trans-name", help="name of the translated file")
    parser.add_argument("--no-fd", action="store_true", help="When translating the pddl instance, do not use Fast Downward preprocessing.")

    parser.add_argument("--save-folder", help="name of the folder where results will be written to", default=None)
    parser.add_argument("--print-results", action="store_true", help="Print results to stdout")

    parser.add_argument("--no-stream-output", action="store_true", help="Supress output to the console")
    parser.add_argument("--logtofile", help="log to a file")

    parser.add_argument("--debug", action="store_true", help="For every scaling amount, write a file with the nogoods used for that particular scaling.")

    other = parser.add_argument_group("Other options")

    other.add_argument("--runsolver", help="Path to the runsolver binary. Default is current directory.", default="./runsolver")

    args = parser.parse_args()

    setup_logging(args.no_stream_output, args.logtofile)

    files = args.files

    RUNSOLVER_PATH = args.runsolver


    DEBUG = args.debug

    if args.pddl_instance is not None:
        if args.trans_name is not None:
            trans_name = args.trans_name
        else:
            trans_name = "instance-temp.lp"

        plasp_translate(args.pddl_instance, args.pddl_domain, trans_name, args.no_fd)

        files.append(trans_name)

    results = consume(files, args.nogoods, args.scaling_list, args.scaling_exp, 
                      max_scaling=args.max_scaling, time_limit=args.time_limit, horizon=args.horizon, no_base_run=args.no_base_run)
    
    if args.save_folder is not None:
        create_folder(args.save_folder)

        for label, out in results.items():
            out_path = os.path.join(args.save_folder, "-{}".format(str(label)))
            with open(out_path, "w") as f:
                f.write(out)


