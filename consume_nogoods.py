import os
import subprocess
import re
import sys
import errno
import argparse
import operator
import logging
import time



match_time = r"Time         : (\d+\.\d+)s"
match_time_solve = r"Solving: (\d+\.\d+)s"

FD_CALL = ["/home/klaus/bin/Fast-Downward/fast-downward.py", "--translate"]


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


def call_clingo(file_names, options):
    #  TODO: use runsolver here to manage the max time and such

    CLINGO = ["clingo"] + file_names

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

    res["time"] = eval_re(match_time, output, 1, res["time"])

    res["solving"] = eval_re(match_time_solve, output, 1, res["solving"])

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

def run_tests(files, nogood_file, scaling, max_scaling, time_limit=0):

    logging.info("Starting nogood consumption...")

    noogood_temp_name = "nogood.temp"
    options = ["--time-limit={}".format(time_limit)]

    scaling = scaling.split(",")
    scaling_start = int(scaling[0])
    scaling_factor = float(scaling[1])
    scaling_count = int(scaling[2])

    times = {}

    nogoods = read_nogoods(nogood_file)
    total_nogoods = len(nogoods)

    nogood_current = scaling_start

    # do a base run
    logging.info("base run")
    output = call_clingo(files, options)
    times[0] = parse_call_results(output)
    logging.info("Results: {}".format(str(times[0])))

    # runs with scaling
    for i in range(scaling_count):
        if nogood_current > total_nogoods:
            logging.info("Finishing early. Trying to use {} nogoods but only {} are available.".format(nogood_current, total_nogoods))
            break

        # if this run has a current scaling higher than the max, break
        if max_scaling <= 0 and nogood_current > max_scaling:
            break

        logging.info("Current scaling: {}".format(nogood_current))

        write_nogood_partial(nogoods[:nogood_current], noogood_temp_name)

        output = call_clingo(files + [noogood_temp_name], options)
        times[nogood_current] = parse_call_results(output, times[0]["time"])
        logging.info("Results: {}".format(str(times[nogood_current])))

        if nogood_current == total_nogoods:
            break

        nogood_current = int(nogood_current*(scaling_factor))

        # if we are using max scaling, the current amount of nogoods exceeds the scaling and its not the last iteration
        if max_scaling <= 0 and nogood_current >= max_scaling and i < scaling_count-1:
            logging.info("Doing a final run with {}(max scaling) nogoods as the current scaling ({}) is now higher.".format(max_scaling, nogood_current))
            nogood_current = max_scaling

        if nogood_current > total_nogoods and i < scaling_count-1:
            logging.info("Doing a final run with {}(max) nogoods as there are not enough for next the scaling: {}".format(total_nogoods, nogood_current))
            nogood_current = total_nogoods



    os.remove(noogood_temp_name)

    return times

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--files", metavar='f', nargs='+', help="Files to run clingo on")
    parser.add_argument("--nogoods", help="File holding the processed nogoods")
    parser.add_argument("--scaling", help="scaling of how many nogoods to use. format=start,factor,count. Default = 8,2,5", default="8,2,5")
    parser.add_argument("--max-scaling", help="maximum value of the scaling. If this value if lower than any step in the scaling, it will be used as the last nogood amount. A zero value means no max scaling.", default=2048)

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

    logging.info(run_tests(files, args.nogoods, args.scaling, args.max_scaling, args.time_limit))