import os
import subprocess
import argparse
import logging

import config_file

from tools.tools import setup_logging, plasp_translate, plasp2_translate, get_parent_dir, create_folder

DEBUG = False

global RUNSOLVER_PATH

def call_clingo(file_names, time_limit, options):

    CLINGO = [RUNSOLVER_PATH, "-W", "{}".format(time_limit), \
              "-w", "runsolver.consumer.watcher", "clingo"] + file_names + ["--stats", "--quiet=2"]

    call = CLINGO + options

    logging.info("calling: " + " ".join(call))

    try:
        output = subprocess.check_output(call).decode("utf-8")
    except subprocess.CalledProcessError as e:
        output = e.output.decode("utf-8")

    logging.debug("call has finished\n")

    return output

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

def run_tests(files, nogood_file, scaling, time_limit=0, horizon=None, no_base_run=False):

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
    for nogood_current in scaling:
        if nogood_current > 0 and nogood_current > total_nogoods:
            logging.info("Finishing early. Trying to use {} nogoods but only {} are available.".format(nogood_current, total_nogoods))
            break

        logging.info("Current scaling: {}".format(nogood_current))

        if nogood_current == -1:
            write_nogood_partial(nogoods[:], noogood_temp_name, debug=DEBUG, fileid=nogood_current)
        else:
            write_nogood_partial(nogoods[:nogood_current], noogood_temp_name, debug=DEBUG, fileid=nogood_current)

        output = call_clingo(files + [noogood_temp_name], time_limit, options)
        results[nogood_current] = output

        logging.info(output)

    try:
        os.remove(noogood_temp_name)
    except OSError:
        logging.info("Failed to delete the nogood temp file.(Might not exist)")

    return results

def consume(files, nogood_file, scaling_list=None, time_limit=0, horizon=None, no_base_run=False):

    if scaling_list is not None:
        if type(scaling_list) == str:
            # this comes from the command line
            scaling_split = scaling_list.split(",")
            scaling = [int(s) for s in scaling_split]


    return run_tests(files, nogood_file, scaling, \
            time_limit=time_limit, horizon=horizon, \
            no_base_run=no_base_run)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--files", metavar='f', nargs='+', help="Files to run clingo on")
    parser.add_argument("--nogoods", help="File holding the processed nogoods")
    parser.add_argument("--scaling-list", help="Perform scaling by the values provided. A scaling of -1 signifies the use of ALL nogoods.", default=None)

    parser.add_argument("--time-limit", help="Time limit for each call. Default=300", default=300)

    parser.add_argument("--no-base-run", help="do not run clingo with 0 added nogoods")

    parser.add_argument("--horizon", help="horizon will be added to clingo -c hor is needed", default=None)
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

    RUNSOLVER_PATH = args.runsolver

    DEBUG = args.debug

    if args.scaling_list is None:
        raise(argparse.ArgumentError("--scaling-list", "Scaling list can not be empty"))

    results = consume(args.files, args.nogoods, args.scaling_list,
                        time_limit=args.time_limit, horizon=args.horizon, no_base_run=args.no_base_run)
    
    if args.save_folder is not None:
        create_folder(args.save_folder)

        for label, out in results.items():
            out_path = os.path.join(args.save_folder, "-{}".format(str(label)))
            with open(out_path, "w") as f:
                f.write(out)


