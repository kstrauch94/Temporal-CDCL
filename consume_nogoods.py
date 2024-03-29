import os
import subprocess
import argparse
import logging

import config

from tools.tools import setup_logging, create_folder

DEBUG = False

def call_clingo(file_names, time_limit, memory_limit, options):

    CLINGO = [config.RUNSOLVER_PATH, "--real-time-limit={}".format(time_limit),
              "-o", "runsolver.consume.watcher"]

    if memory_limit is not None:
        CLINGO += ["--space-limit={}".format(memory_limit)]
    
    CLINGO += [config.CLINGO] + file_names
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

def run_tests(files, nogood_file, scaling, scaling_exact=False, scaling_block=False, time_limit=0, memory_limit=None, horizon=None, solver_args=None, no_base_run=False):

    logging.info("Starting nogood consumption...")

    noogood_temp_name = "nogood.temp"
    options = ["--stats", "--quiet=2"]

    if horizon is not None:
        options += ["-c", "horizon={}".format(horizon)]

    if solver_args is not None:
        options += solver_args.split()

    results = {}

    nogoods = read_nogoods(nogood_file)
    total_nogoods = len(nogoods)


    if not no_base_run:
        # do a base run
        logging.info("base run")
        output = call_clingo(files, time_limit, memory_limit, options)
        results["base"] = output
        logging.info(output)
    
    print("\n\n")

    # runs with scaling
    for idx, nogood_current in enumerate(scaling, start=0):
        if nogood_current > 0 and nogood_current > total_nogoods:
            #logging.info("Finishing early. Trying to use {} nogoods but only {} are available.".format(nogood_current, total_nogoods))
            logging.warning("Trying to use {} nogoods but only {} are available. Using all nogoods to run!".format(nogood_current, total_nogoods))
            
            nogood_current = -1

        logging.info("Current scaling: {}".format(nogood_current))

        if scaling_exact:

            if nogood_current == -1:
                write_nogood_partial(nogoods[-1], noogood_temp_name, debug=DEBUG, fileid=nogood_current)
            else:
                write_nogood_partial(nogoods[nogood_current], noogood_temp_name, debug=DEBUG, fileid=nogood_current)

        elif scaling_block and idx > 0:
            prev_scale = scaling[idx-1]
            if nogood_current == -1:
                write_nogood_partial(nogoods[prev_scale:-1], noogood_temp_name, debug=DEBUG, fileid=nogood_current)
            else:
                write_nogood_partial(nogoods[prev_scale:nogood_current], noogood_temp_name, debug=DEBUG, fileid=nogood_current)

        else:
            if nogood_current == -1:
                write_nogood_partial(nogoods[:], noogood_temp_name, debug=DEBUG, fileid=nogood_current)
            else:
                write_nogood_partial(nogoods[:nogood_current], noogood_temp_name, debug=DEBUG, fileid=nogood_current)

        output = call_clingo(files + [noogood_temp_name], time_limit, memory_limit, options)
        results[nogood_current] = output

        logging.info(output)

    try:
        os.remove(noogood_temp_name)
    except OSError:
        logging.info("Failed to delete the nogood temp file.(Might not exist)")

    return results

def consume(files, nogood_file, scaling_list=None, scaling_exact=False, scaling_block=False, time_limit=0, memory_limit=None, horizon=None, solver_args=None, no_base_run=False):

    if scaling_list is not None:
        if type(scaling_list) == str:
            # this comes from the command line
            scaling_split = scaling_list.split(",")
            scaling = [int(s) for s in scaling_split]


    return run_tests(files, nogood_file, scaling, scaling_exact, scaling_block, \
            time_limit=time_limit, memory_limit=memory_limit, horizon=horizon, solver_args=solver_args, \
            no_base_run=no_base_run)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--files", metavar='f', nargs='+', help="Files to run clingo on")
    parser.add_argument("--nogoods", help="File holding the processed nogoods")
    parser.add_argument("--scaling-list", help="Perform scaling by the values provided. A scaling of -1 signifies the use of ALL nogoods.", default=None)

    parser.add_argument("--scaling-exact", action="store_true", help="Run only the nogood given in the number of the scaling list")
    parser.add_argument("--scaling-block", action="store_true", help="Run the block of nogoods given by 2 numbers of the scaling list.")

    parser.add_argument("--time-limit", help="Time limit for each call. Default=300", default=300)
    parser.add_argument("--memory-limit", default=None, type=int, help="Memory limit for nogood extraction in MB. Default = None")

    parser.add_argument("--no-base-run", action="store_true", help="do not run clingo with 0 added nogoods")

    parser.add_argument("--horizon", help="horizon will be added to clingo -c hor is needed", default=None)
    parser.add_argument("--no-fd", action="store_true", help="When translating the pddl instance, do not use Fast Downward preprocessing.")

    parser.add_argument("--save-folder", help="name of the folder where results will be written to", default=None)
    parser.add_argument("--print-results", action="store_true", help="Print results to stdout")

    parser.add_argument("--no-stream-output", action="store_true", help="Supress output to the console")
    parser.add_argument("--logtofile", help="log to a file")

    parser.add_argument("--debug", action="store_true", help="For every scaling amount, write a file with the nogoods used for that particular scaling.")

    parser.add_argument("--solver-args", help="Add extra clingo arguments to the learning solve call as given here. give arguments inside quotation marks", default=None)

    other = parser.add_argument_group("Other options")

    other.add_argument("--runsolver", help="Path to the runsolver binary. Default is current directory.", default=None)

    args = parser.parse_args()

    setup_logging(args.no_stream_output, args.logtofile)

    if args.runsolver is not None:
        config.RUNSOLVER_PATH = args.runsolver

    if args.scaling_exact and args.scaling_block:
        raise argparse.ArgumentError("scaling-exact and scaling-block can not be used at the same time")

    DEBUG = args.debug

    if args.scaling_list is None:
        raise(argparse.ArgumentError("--scaling-list", "Scaling list can not be empty"))

    results = consume(args.files, args.nogoods, args.scaling_list, args.scaling_exact, args.scaling_block,
                        time_limit=args.time_limit, memory_limit=args.memory_limit, horizon=args.horizon, solver_args=args.solver_args, no_base_run=args.no_base_run)

    if args.save_folder is not None:
        create_folder(args.save_folder)

        for label, out in results.items():
            out_path = os.path.join(args.save_folder, "-{}".format(str(label)))
            with open(out_path, "w") as f:
                f.write(out)

if __name__ == "__main__":
    main()
