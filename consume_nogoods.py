import os
import subprocess
import re
import sys
import errno
import argparse
import operator
import logging
import time


def get_parent_dir(path):
    # this gets the name of the parent folder

    # if there is a trailing backslash then delete it
    if path.endswith("/"):
        path = path[:-1]

    return os.path.dirname(path)
    

match_time = r"Time         : (\d+\.\d+)s"
match_time_solve = r"Solving: (\d+\.\d+)s"

FD_CALL = ["/home/klaus/bin/Fast-Downward/fast-downward.py", "--translate"]

FILE_PATH = os.path.abspath(__file__)

RUNSOLVER_PATH = os.path.join(get_parent_dir(FILE_PATH), "runsolver")

def setup_logging(logtofile):

    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(levelname)s: %(message)s")

    if logtofile is not None:
        fileHandler = logging.FileHandler(logtofile, mode="w")
        fileHandler.setFormatter(formatter)
        rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)
    rootLogger.addHandler(consoleHandler)


def plasp_translate(instance, domain, filename):

    if domain is None:
        # look for domain in the same folder
        logging.info(os.path.join(get_parent_dir(instance), "domain.pddl"))
        if  os.path.isfile(os.path.join(get_parent_dir(instance), "domain.pddl")):
            domain = os.path.join(get_parent_dir(instance), "domain.pddl")

        # look for domain in parent folder
        elif os.path.isfile(os.path.join(get_parent_dir(instance), "../domain.pddl")):
            domain = os.path.join(get_parent_dir(instance), "../domain.pddl")

        else:
            logging.error("no domain could be found. Exiting...")
            sys.exit(-1)


    logging.info("translating instance {}\nwith domain {}".format(instance, domain))

    FD_CALL = FD_CALL + [domain, instance]

    output = subprocess.check_output(FD_CALL).decode("utf-8")
    #print(output)

    plasp_call = ["plasp", "translate", "output.sas"]

    output = subprocess.check_output(plasp_call).decode("utf-8")
    with open(filename, "w") as f:
        f.write(output)

    logging.info("saved translation into {}".format(filename))

    os.remove("output.sas")


def call_clingo(file_names, time_limit, options):
    #  TODO: use runsolver here to manage the max time and such

    CLINGO = [RUNSOLVER_PATH, "-W", "{}".format(time_limit), \
              "-w", "runsolver.watcher", "clingo"] + file_names

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

def parse_call_results(output, base_time=None):
    # here i will parse the results of ONE call
    # return a dict with the results

    res = {"time" : 0,
           "solving" : 0,
           "success": None,
           "percent": None
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

    if base_time is not None:
        res["percent"] = res["time"] / float(base_time)

    return res

def read_nogoods(nogood_file):

    with open(nogood_file, "r") as f:
        nogoods = f.readlines()

    return nogoods

def write_nogood_partial(nogoods, filename="nogood.temp"):

    with open(filename, "w") as f:
        f.writelines(nogoods)

def run_tests(files, nogood_file, scaling, labels, max_scaling=0, time_limit=0,):

    logging.info("Starting nogood consumption...")

    noogood_temp_name = "nogood.temp"
    options = []

    times = {}

    nogoods = read_nogoods(nogood_file)
    total_nogoods = len(nogoods)

    # do a base run
    logging.info("base run")
    output = call_clingo(files, time_limit, options)
    times["base"] = parse_call_results(output)
    logging.info("Results: {}".format(str(times["base"])))

    # runs with scaling
    for nogood_current, label in zip(scaling, labels):
        if nogood_current > total_nogoods:
            logging.info("Finishing early. Trying to use {} nogoods but only {} are available.".format(nogood_current, total_nogoods))
            break

        # if this run has a current scaling higher than the max, break
        if max_scaling > 0 and nogood_current > max_scaling:
            logging.info("Finishing early. Current scaling of {} is higher than max scaling: {}".format(nogood_current, max_scaling))
            break

        logging.info("Current scaling: {}".format(nogood_current))

        write_nogood_partial(nogoods[:nogood_current], noogood_temp_name)

        output = call_clingo(files + [noogood_temp_name], time_limit, options)
        times[label] = parse_call_results(output, base_time=times["base"]["time"])
        logging.info("Results: {}".format(str(times[label])))

    os.remove(noogood_temp_name)

    return times

def consume(files, nogood_file, scaling, max_scaling=0, time_limit=0, scaling_type="by_factor", labels=None):
    # scaling type can be "by_value" or "by_factor"
    # by_value means just passing a list with amount of nogoods, those amounts will be used in the runs
    # by factor means passing 3 argument, start amount, scaling factor and total runs
    # a scaling by factor of 8,2,5 means doing 5 runs starting at 8 increasing by a factor of 2
    # so: 8,16,32,64,128
    # a base run is always done

    if scaling_type == "by_factor":
        scaling_split = scaling.split(",")

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

    if scaling_type == "by_value":
        if type(scaling) == str:
            # this comes from the command line
            scaling_split = scaling.split(",")
            scaling = [int(s) for s in scaling_split]
        
        scaling_labels = labels

    return run_tests(files, nogood_file, scaling, scaling_labels, \
            max_scaling=max_scaling, time_limit=time_limit)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--files", metavar='f', nargs='+', help="Files to run clingo on")
    parser.add_argument("--nogoods", help="File holding the processed nogoods")
    parser.add_argument("--scaling", help="scaling of how many nogoods to use. format=start,factor,count. Default = 8,2,5", default="8,2,5")
    parser.add_argument("--max-scaling", help="maximum value of the scaling. If this value if lower than any step in the scaling, it will be used as the last nogood amount. A zero value means no max scaling. Default = 2048", default=2048)

    parser.add_argument("--scaling-type", choices=["by_factor", "by_value"], help="Perform scaling by factor or by value")

    parser.add_argument("--time-limit", type=int, help="time limit per call in seconds. Default=300", default=300)

    parser.add_argument("--pddl-instance", help="pddl instance")
    parser.add_argument("--pddl-domain", help="pddl domain")
    parser.add_argument("--trans-name", help="name of the translated file")


    args = parser.parse_args()

    setup_logging(None)

    files = args.files

    if args.pddl_instance is not None:
        if args.trans_name is not None:
            trans_name = args.trans_name
        else:
            trans_name = "instance-temp.lp"

        plasp_translate(args.pddl_instance, args.pddl_domain, trans_name)

        files.append(trans_name)

    logging.info(run_tests(files, args.nogoods, args.scaling, max_scaling=args.max_scaling, time_limit=args.time_limit, scaling_type=args.scaling_type))
