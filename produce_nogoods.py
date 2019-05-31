import os
import clingo
import subprocess
import re
import sys
import errno
import argparse
import operator
import logging
import time
import consume_nogoods
from collections import Counter

def get_parent_dir(path):
    # this gets the name of the parent folder

    # if there is a trailing backslash then delete it
    if path.endswith("/"):
        path = path[:-1]

    return os.path.dirname(path)

OPENTIME = "otime"

time_re = r"s\(([0-9]+)\)"

END_STR = "asdasdasd"
time_no_s_re = r"([0-9]+)\)*{end_str}".format(end_str=END_STR)

time_step_re = r"{}\(([0-9]+)\)".format(OPENTIME)

answer_re = r"Answer: [0-9]+\n(.*)\n"

models_re = r"Models       : ([0-9]+)"

lbd_re = r"lbd = ([0-9]+)"

error_re = r"error\(([0-9]+)\)"

# regex from 
# https://stackoverflow.com/questions/9644784/python-splitting-on-spaces-except-between-certain-characters
# split on commas followed by whitespace except when between ""
# the comma at the beggining was added by me
split_atom_re = r",\s+(?=[^()]*(?:\(|$))"

UNSAT = "UNSATISFIABLE"

FD_CALL = ["/home/klaus/bin/Fast-Downward/fast-downward.py", "--translate"]

FILE_PATH = os.path.abspath(__file__)

RUNSOLVER_PATH = os.path.join(get_parent_dir(FILE_PATH), "runsolver") 


def create_folder(path):
    """
    from http://stackoverflow.com/posts/5032238/revisions

    :param path: folder to be created
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

class Nogood:

    def __init__(self, nogood_str, ordering, lbd=None, inc_t=False):

        #nogood_str: raw string printed out by the clingo call
        #ordering: line number of the nogood (the order in which the noogood was created)

        # split by a . and then get the first element and add the . 
        # do this to delete the lbd part at the end
        #self.raw = nogood_str.split(".")[0] + "."
        if inc_t:
            self.t = "t"
        else:
            self.t = "T"

        self.ordering = ordering

        if lbd is None:
            try:
                self.lbd = int(re.search(lbd_re, nogood_str).group(1))
            except AttributeError as e:
                logging.info("ERROR IN LBD: {}".format(nogood_str))
                raise AttributeError            
        else:
            self.lbd = lbd

        self.process_literals(nogood_str)
        self.process_domain_literals()

        self.process_time()

        self.validated = None
        self.instance_validated = None

        # time in the name refers to timepoint in the program
        self.instance_val_error_time = "-1" 


    def process_literals(self, nogood_str):
        # this takes the raw nogood string and splits the atoms
        # into singular ones

        pre_literals = nogood_str.split(".")[0].replace(":-", "").strip()

        pre_literals = re.split(split_atom_re, pre_literals)

        self.literals = []
        self.domain_literals = []

        for lit in pre_literals:
            if "{}(".format(OPENTIME) in lit:
                self.domain_literals.append(lit)

            else:
                self.literals.append(lit)

    def process_domain_literals(self):
        # here we create "next" literals out of the not external literals
        # as a form of handling the domain of the time 

        for dl in self.domain_literals:
            if "not external(" in dl:
                # delete the not external and the last parenthesis )
                new_dl = dl.replace("not external(", "")[:-1]

                self.domain_literals.append(new_dl)

    def process_time(self):
        # finding the max doesnt take into account the first value of the external(next(T1,T2))
        # because that value will never be the max anyway

        matches = re.findall(time_no_s_re, END_STR.join(self.literals)+END_STR)
        matches += re.findall(time_no_s_re, END_STR.join(self.domain_literals)+END_STR)
        # get time matches only for step externals
        matches_step = re.findall(time_step_re, " ".join(self.domain_literals))

        matches = [int(m) for m in matches]

        self.max_time = max(matches)

        # dif_to_min would be the degree
        if len(matches_step) == 0:
            # if there are no step externals then dif is 0
            self.dif_to_min = 0
        else:
            # if there are step atoms then dif +1 is the degree
            # since step externals only cover the higher time step of
            # the rule
            matches_step = [int(m) for m in matches_step]
            self.dif_to_min = self.max_time - min(matches_step) + 1

    @property
    def degree(self):
        return self.dif_to_min

    @property
    def literal_count(self):
        return len(self.literals)

    def _generalize(self, literals):

        if len(literals) == 0:
            return []

        gen_literals = []

        for lit in literals:
            time = int(re.search(r"([0-9]+)\)*{end}".format(end=END_STR), lit + END_STR).group(1))

            new_lit = re.sub(r"{t}(\)*){end}".format(t=time, end=END_STR), r"{t}-{dif}\1{end}".format(t=self.t, dif=self.max_time - time, end=END_STR), lit + END_STR)

            if "external(next(" in lit or "next(" in lit:
                new_lit = re.sub(r"next\({t},".format(t=time-1), r"next({t}-{dif},".format(t=self.t, dif=self.max_time - time + 1), new_lit)


            gen_literals.append(new_lit.replace(END_STR, ""))

        # there is an extra empty item at the end, so we delete it
        return gen_literals

    def generalize(self):

        self.literals = self._generalize(self.literals)

        self.domain_literals = self._generalize(self.domain_literals)

        if self.dif_to_min == 0:
            if self.t == "T":
                self.domain_literals += ["time(T)"]

        # minimum timepoint in the rule is 1
        self.domain_literals += ["{}-{} > 0".format(self.t, self.dif_to_min)]

    def validate(self, files):

        literals = self.get_nogood()
        temp_validate = "temp_validate.lp"

        call = ["clingo", "--quiet=2", temp_validate] + files

        logging.debug("calling : {}".format(call))


        program = """#const degree={deg}.
hypothesisConstraint({t}-degree) {constraint}
:- not hypothesisConstraint(1).
""".format(deg=self.degree, t=self.t, constraint=self.to_constraint_any(literals))

        with open(temp_validate, "w") as f:
            f.write(program)

        try:
            output = subprocess.check_output(call).decode("utf-8")
        except subprocess.CalledProcessError as e:
            output = e.output.decode("utf-8")

        logging.debug(output)

        os.remove(temp_validate)

        if UNSAT in output:
            self.validated = True

        else:
            self.validated = False

    def validate_instance(self, files):

        temp_validate = "temp_validate_inst.lp"

        call = ["clingo", "--quiet=1", temp_validate] + files

        logging.debug("calling : {}".format(call))

        program = """error({t}) {constraint}
error :- error(_).
:- not error.
#project error/0.
#show error/1.""".format(t=self.t, constraint=self.to_constraint())

        with open(temp_validate, "w") as f:
            f.write(program)

        try:
            output = subprocess.check_output(call).decode("utf-8")
        except subprocess.CalledProcessError as e:
            output = e.output.decode("utf-8")

        logging.debug(output)

        os.remove(temp_validate)

        if UNSAT in output:
            self.instance_validated = True

        else:
            self.instance_validated = False
            self.instance_val_error_time = str(re.findall(error_re, output))

    def to_constraint(self):
        return ":- " +  ", ".join(self.get_nogood()) + ".\n"

    def to_rule(self):
        return "error({}) ".format(self.ordering) + self.to_constraint()

    def to_rule_any(self, literals):
       return "error({}) ".format(self.ordering) + ":- " +  ", ".join(literals) + ".\n"

    def to_constraint_any(self, literals):
        return ":- " +  ", ".join(literals) + ".\n"

    def get_nogood(self):
        return self.literals + self.domain_literals

    def __str__(self):
        # returns a string version of the nogood
        return self.to_constraint()

def get_sort_value(object, attributes):
    val = []

    for attr in attributes:
        val.append(getattr(object, attr))

    return val

def call_clingo(file_names, time_limit, options):

    CLINGO = [RUNSOLVER_PATH, "-W", "{}".format(time_limit), \
              "-w", "runsolver.watcher", "-d", "20", 
              "clingo"] + file_names

    call = CLINGO + options

    logging.info("calling: " + " ".join(call))

    try:
        output = subprocess.check_output(call).decode("utf-8")
    except subprocess.CalledProcessError as e:
        output = e.output.decode("utf-8")

    logging.info("call has finished\n")

    logging.info(output)

def call_clingo_pipe(file_names, time_limit, options, out_file, max_deg=10, max_lit_count=50):

    CLINGO = [RUNSOLVER_PATH, "-W", "{}".format(time_limit), 
              "-w", "runsolver.watcher", "-d", "20", 
              "clingo"] + file_names

    call = CLINGO + options

    if os.path.isfile(out_file):
        os.remove(out_file)

    logging.info("calling: " + " ".join(call))

    output = ""
    pipe = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    with open(out_file, "a") as out:
        for line in pipe.stdout:
            line = line.decode("utf-8")
            if line.startswith(":-"):
                if check_nogood_str(line, max_deg, max_lit_count):
                    out.write(line)
            else:
                output += line

    logging.info("call has finished\n")

    logging.info(output)

def validate_instance_all(files):
    # files argument is a list containing the encoding, instance and the file containing all nogoods to be proven

    val_file_all = "validate_instance_all.lp"

    with open(val_file_all, "w") as f:
        for ng in nogoods:
            f.write(str(ng.to_rule()))
        f.write("\nerror :- error(_).\n")
        f.write(":- not error.\n")
        f.write("#project error/0.\n")
        f.write("#show error/1.\n")

    call = ["clingo", "--quiet=1", val_file_all] + files

    logging.debug("calling : {}".format(call))

    try:
        output = subprocess.check_output(call).decode("utf-8")
    except subprocess.CalledProcessError as e:
        output = e.output.decode("utf-8")

    logging.debug(output)

    os.remove(val_file_all)

    if UNSAT in output:
        return True

    else:
        return False

def extract_stats(nogoods):

    total_nogoods = len(nogoods)

    degree = Counter()
    lbd = Counter()
    size = Counter()

    degree_total = 0
    lbd_total = 0
    size_total = 0

    for ng in nogoods:
        degree[ng.degree] += 1
        lbd[ng.lbd] += 1
        size[ng.literal_count] += 1

        degree_total += ng.degree
        lbd_total += ng.lbd
        size_total += ng.literal_count




    return {"degree": degree, "lbd": lbd, "size": size,
            "degree mean": float(degree_total)/total_nogoods,
            "lbd mean": float(lbd_total)/total_nogoods,
            "size mean": float(size_total)/total_nogoods}

def scaling_by_value(stats, count, sortby):

    if sortby[0] != "ordering" :
        if args.sortby[0] == "literal_count":
            stat_name = "size"
        elif args.sortby[0] == "degree":
            stat_name = "degree"
        elif args.sortby[0] == "lbd":
            stat_name = "lbd"

        scaling_by_val = []
        total_count = 0 # keep track of cumulative count of prev values
        scaling_labels = []
        for i in range(args.nogoods_wanted_by_count + 1):
            if i in stats[stat_name]:
                count = int(stats[stat_name][i])
                scaling_by_val.append(count + total_count)
                total_count += count
                scaling_labels.append(i)

    else:
        scaling_by_val = None

    return scaling_by_val, total_count, scaling_labels

def read_nogood_file(ng_file, max_deg, max_lit_count, inc_t):
    unprocessed_ng = []

    with open(ng_file, "r") as f:
        for line_num, line in enumerate(f):

            # if no lbd is found then the file was not written fully
            # if it it found then pass it as argument to not do this twice
            try:
                lbd = int(re.search(lbd_re, line).group(1))
            except AttributeError as e:
                continue

            # line is the raw text of the nogood, line num is the order it appears in the file
            nogood = Nogood(line, line_num, lbd, inc_t)
            # ignore nogoods of higher degree or literal count
            if max_deg >= 0 and nogood.degree > max_deg:
                continue
            if max_lit_count > 0 and nogood.literal_count > max_lit_count:
                continue

            unprocessed_ng.append(nogood)

    return unprocessed_ng

def check_nogood_str(ng_str, max_deg, max_lit_count):
    # if no lbd is found then the file was not written fully
    # if it it found then pass it as argument to not do this twice
    try:
        lbd = int(re.search(lbd_re, ng_str).group(1))
    except AttributeError as e:
        return False

    # ng_str is the raw text of the nogood, ng_str num is the order it appears in the file
    nogood = Nogood(ng_str, 1, lbd)
    # ignore nogoods of higher degree or literal count
    if max_deg >= 0 and nogood.degree > max_deg:
        return False
    if max_lit_count > 0 and nogood.literal_count > max_lit_count:
        return False

    return True

def generalize_nogoods(ng_list, nogoods_wanted):

        nogoods = []
        for ng in ng_list:

            ng.generalize()
            nogoods.append(ng)

            if len(nogoods) >= nogoods_wanted:
                break

        return nogoods

def convert_ng_file(ng_name, converted_ng_name,
                    no_generalization=False,
                    max_deg=10,
                    max_lit_count=50,
                    nogoods_wanted=100,
                    nogoods_wanted_by_count=-1,
                    sortby=["literal_count"], 
                    validate_files=None, 
                    reverse_sort=False,
                    validate_instance="none",
                    validate_instance_files=None,
                    inc_t=False):

    # sortby should be a list of the int attributes in the nogood:
    # lbd, ordering, degree, literal_count

    converted_lines = []
    amount_validated = 0
    amount_instance_validated = 0

    failed_to_validate = []
    # just so that we dont check multiple times
    validate = validate_files is not None

    # read nogoods
    
    total_nogoods = 0

    time_generalize = 0
    time_validate = 0
    time_validate_instance = 0

    logging.info("converting...")
    
    t = time.time()

    unprocessed_ng = read_nogood_file(ng_name, max_deg, max_lit_count, inc_t)
    total_nogoods = len(unprocessed_ng)

    time_init_nogood = time.time() - t

    logging.info("total lines in the no good file: {}\n".format(total_nogoods))
    if total_nogoods == 0:
        logging.info("no nogoods learned...")
        return 0, None, None

    t = time.time()
    if sortby is not None:
        unprocessed_ng.sort(key=lambda nogood : get_sort_value(nogood, sortby), reverse=reverse_sort)

    time_sorting_nogoods = time.time() - t    

#    # write sorted unprocessed nogoods
#    with open("sorted_ng.txt", "w") as f:
#        for conv_line in unprocessed_ng:
#            line = conv_line.to_constraint()
#            f.write(str(line))

    # extract some stats about some nogood properties
    t = time.time()
    stats = extract_stats(unprocessed_ng)
    time_extract_stats = time.time() - t

    t = time.time()
    for key, val in stats.items():
        #if "mean" in key:
        logging.info("{} {}".format(key, val))
    time_logging_stats = time.time() - t

    # get the scaling amounts and the nogoods count we want
    if nogoods_wanted_by_count >= 0:
        scaling_by_val, nogoods_wanted, scaling_labels = scaling_by_value(stats, nogoods_wanted_by_count, sortby)
    else:
        scaling_by_val = None
        scaling_labels = None

    if no_generalization == False:    

        t = time.time()

        nogoods = generalize_nogoods(unprocessed_ng, nogoods_wanted)

        time_generalize = time.time() - t

        total_nogoods = len(nogoods)

        logging.info("Total nogoods after processing: {}".format(total_nogoods))

        if validate:
            logging.info("Starting validation...")
            percent_validated = 0.1

            for i, ng in enumerate(nogoods):

                # this part is the normal validation as patrick does it
                t = time.time()
                ng.validate(validate_files)
                time_validate += time.time() - t

                logging.debug("validated: {}".format(ng.validated))

                if ng.validated:
                    amount_validated += 1

                else:
                    logging.info("not validated: {}".format(ng.to_constraint()))
                    logging.info("number: {}".format(ng.ordering))
                    failed_to_validate.append(ng.to_rule())

                if float(i) / float(total_nogoods) >= percent_validated:
                    logging.info("Validated {}% of total nogoods".format(percent_validated*100))
                    percent_validated += 0.1


            print("failed vals {}".format(len(failed_to_validate)))

            logging.info("Finishing validation")

        if validate_instance != "none":

            logging.info("Starting instance validation...")

            # validate nogoods one at a time
            if validate_instance == "single":
                percent_validated = 0.1

                for i, ng in enumerate(nogoods):

                    # this part is validating within the instance
                    t = time.time()
                    ng.validate_instance(validate_instance_files)
                    time_validate_instance += time.time() - t
                    
                    if not ng.instance_validated:
                        logging.info("Result of instance val: {}".format(ng.instance_validated))
                        logging.info("constraint: {}".format(ng.to_constraint()))
                        logging.info("number: {}".format(ng.ordering))
                        logging.info("error times: {}".format(ng.instance_val_error_time))
                    else:
                        amount_instance_validated += 1

                    # if we validate with both methods check if they have the same result
                    if (validate_instance and validate):
                        if ng.instance_validated != ng.validated:
                            logging.info("validations do not match")
                            logging.info("Normal validation: {}".format(ng.validated))
                            logging.info("Instance validation: {}".format(ng.instance_validated))
                            logging.info("constraint: {}".format(str(ng)))

                    if float(i) / float(total_nogoods) >= percent_validated:
                        logging.info("Validated {}% of total nogoods".format(percent_validated*100))
                        percent_validated += 0.1
                        
            # validate nogoods all at the same time
            elif validate_instance == "all":
                #write all nogoods in a file as a rule:
                # add the rule as in the nogoods class instance val
                t = time.time()
                validate_instance_all(validate_instance_files)
                time_validate_instance += time.time() - t

            logging.info("Finishing instance validation")

        # log some info after finishing
        logging.info("Finished converting!\n")

        if validate:
            logging.info("Validated {} of {} nogoods".format(amount_validated, total_nogoods))
        if validate_instance == "single":
            logging.info("Validated {} of {} nogoods within the instance".format(amount_instance_validated, total_nogoods))
        if validate_instance == "all":
            logging.info("Validation of all nogoods returned {}".format(all_val_result))

        logging.info("time to generalize: {}".format(time_generalize))
        if validate:
            logging.info("time to validate: {}".format(time_validate))
        if validate_instance == "single" or validate_instance == "all":
            logging.info("time to validate within instance: {}".format(time_validate_instance))
 

    else:
        # if we don't generalize then nogoods is just the n first
        # from the list (since it should be sorted in the correct order anyway)
        nogoods = unprocessed_ng[:nogoods_wanted]

    t = time.time()
    # write generalized nogoods into a file
    lines_set = set()
    with open(converted_ng_name, "w") as f:
        for conv_line in nogoods:
            line = conv_line.to_constraint()
            if line not in lines_set:
                f.write(str(line))
                lines_set.add(line)
    
    time_writing_file = time.time() - t

    logging.info("time to extract stats: {}".format(time_extract_stats))
    logging.info("time to log stats: {}".format(time_logging_stats))

    logging.info("time initializing nogoods: {}".format(time_init_nogood))
    logging.info("time sorting nogoods: {}".format(time_sorting_nogoods))
    logging.info("time writing file: {}".format(time_writing_file))

    return total_nogoods, scaling_by_val, scaling_labels

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

    fd_call = FD_CALL + [domain, instance]

    output = subprocess.check_output(fd_call).decode("utf-8")

    plasp_call = ["plasp", "translate", "output.sas"]

    output = subprocess.check_output(plasp_call).decode("utf-8")
    with open(filename, "w") as f:
        f.write(output)

    logging.info("saved translation into {}".format(filename))

    os.remove("output.sas")


def produce_nogoods(file_names, args, config):

    logging.info("Starting nogood production...")

    ng_name = "ng_temp.lp"
    converted_ng_name =  "conv_ng.lp"

    NG_RECORDING_OPTIONS = ["--lemma-out-txt",
                        "--lemma-out=-",
                        "--lemma-out-dom=output", 
                        "--heuristic=Domain", 
                        "--dom-mod=level,show",
                        "--lemma-out-max={}".format(args.nogoods_limit),
                        "--solve-limit={}".format(3*int(args.nogoods_limit)),
                        "--quiet=2",
                        "--stats",
                        "--loops=no", "--reverse-arcs=0", "--otfs=0",
                        "1"]

    if args.horizon is not None:
        horizon = ["-c", "horizon={}".format(args.horizon)]
    else:
        horizon = []

    NG_RECORDING_OPTIONS += horizon

    # call clingo to extract nogoods
    t = time.time()
    call_clingo_pipe(file_names, args.max_extraction_time, NG_RECORDING_OPTIONS,
                     ng_name, args.max_deg, args.max_lit_count)
    time_extract = time.time() - t

    t = time.time()
    # convert the nogoods
    total_nogoods, scaling_by_val, scaling_labels = convert_ng_file(ng_name, converted_ng_name,
                    **config)
    time_conversion = time.time() - t

    logging.info("time to extract: {}".format(time_extract))
    logging.info("time to do conversion jobs: {}".format(time_conversion))
    
    try:
        os.remove(ng_name)
    except OSError:
        logging.warning("Tried to remove {} but it was already deleted!".format(ng_name))

    return converted_ng_name, scaling_by_val, scaling_labels

def setup_logging(no_stream_output=False, logtofile=None):

    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(levelname)s: %(message)s")

    if logtofile is not None:
        fileHandler = logging.FileHandler(logtofile, mode="w")
        fileHandler.setFormatter(formatter)
        rootLogger.addHandler(fileHandler)

    if not no_stream_output:
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setFormatter(formatter)
        rootLogger.addHandler(consoleHandler)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('--files', metavar='f', nargs='+', help="Files to run clingo on not including instance")
    parser.add_argument('--instance', metavar='i', help="Instance file. If file has a .pddl extension it will be treated as a pddl instance.")

    parser.add_argument("--pddl-instance", help="pddl instance")
    parser.add_argument("--pddl-domain", help="pddl domain", default=None)
    parser.add_argument("--trans-name", help="name of the translated file")
    parser.add_argument("--horizon", help="horizon will be added to clingo -c horizon=<h>", type=int, default=None)

    parser.add_argument("--no-generalization", action="store_true", help="Don't generalize the learned nogoods")
    parser.add_argument("--sortby", nargs='+', help="attributes that will sort the nogood list. The order of the attributes is the sorting order. Choose from [degree, literal_count, ordering, lbd]. default: [degree, literal_count]", default=["degree", "literal_count"])
    parser.add_argument("--reverse-sort", action="store_true", help="Reverse the sort order.")
    parser.add_argument("--inc_t", action="store_true", help="use the incremental 't' instead of the normal 'T'")

    parser.add_argument("--validate-files", nargs='+', help="file used to validate learned constraints. If no file is provided validation is not performed.", default=None)
    parser.add_argument("--validate-instance", default="none", choices=["none", "single", "all"], help="With this option the constraints will be validated with a search by counterexamples using the files and instances provided. Single validates every constraint by itself. all validates all constraints together")

    parser.add_argument("--nogoods-limit", help="Solving will only find up to this amount of nogoods for processing. Default = 100", default=100, type=int)

    parser.add_argument("--nogoods-wanted", help="Nogoods will be processed will stop after this amount. Default = 100", default=100, type=int)
    parser.add_argument("--nogoods-wanted-by-count", help="Nogoods that have a value equal or less than the one given here in the variable given in the first position of the sortby option(does not work for ordering). This option overwrites nogoods-wanted option. If this option is used along with --consume it will use this values as the argument for --scaling-list unless those values are provided.", default=-1, type=int)

    parser.add_argument("--max-deg", help="Processing will ignore nogoods with higher degree. Default = 10. A negative number means no limit.", default=10, type=int)
    parser.add_argument("--max-lit-count", help="Processing will ignore nogoods with higher literal count. Default = 50. 0 or a negative number means no limit.", default=50, type=int)

    parser.add_argument("--max-extraction-time", default=20, type=int, help="Time limit for nogood extraction in seconds. Default = 20")

    parser.add_argument("--logtofile", help="log to a file")

    parser.add_argument("--consume", action="store_true", help="consume the generated nogoods based on the given scaling.")
    parser.add_argument("--scaling-exp", help="scaling of how many nogoods to use. format=start,factor,count", default=None)
    parser.add_argument("--scaling-list", help="Perform scaling by the values provided", default=None)
    parser.add_argument("--consume-time-limit", type=int, help="time limit per call in seconds. Default=300", default=300)

    parser.add_argument("--no-stream-output", action="store_true", help="Supress output to the console")


    args = parser.parse_args()

    setup_logging(args.no_stream_output, args.logtofile)

    if args.scaling_list is not None and args.scaling_exp is not None:
        logging.error("only one scaling can be provided at a time. Use either --scaling-list or --scaling-exp")
        sys.exit(1)

    files = args.files

    config = {}

    config["no_generalization"] = args.no_generalization
    config["validate_files"] = args.validate_files
    config["validate_instance"] = args.validate_instance
    config["sortby"] = args.sortby
    config["reverse_sort"] = args.reverse_sort

    config["max_deg"] = args.max_deg
    config["max_lit_count"] = args.max_lit_count
    config["nogoods_wanted"] = args.nogoods_wanted
    config["nogoods_wanted_by_count"] = args.nogoods_wanted_by_count
    config["inc_t"] = args.inc_t

    if args.instance.endswith(".pddl"):
        args.pddl_instance = args.instance

        args.instance = None

    if args.pddl_instance is not None:
        if args.trans_name is not None:
            trans_name = args.trans_name
        else:
            trans_name = "instance-temp.lp"

        plasp_translate(args.pddl_instance, args.pddl_domain, trans_name)

        instance = trans_name
        files.append(instance)

    elif args.instance is not None:
        instance = args.instance
        files.append(instance)

    if config["validate_files"] is not None:
        # last value in files should be instance
        config["validate_files"] += [instance]

    config["validate_instance_files"] = files

    converted_nogoods, scaling_by_val, scaling_labels = produce_nogoods(files, args, config)
    
    if args.scaling_list is not None:
        scaling_list = args.scaling_list
        scaling_exp = None
    elif scaling_by_val is not None:
        scaling_list = scaling_by_val
        scaling_exp = None
    elif args.scaling_exp is not None:
        scaling_exp = args.scaling_exp
        scaling_list = None

    if args.consume:
        results = consume_nogoods.consume(files, converted_nogoods, 
                                          scaling_list, scaling_exp, 
                                          time_limit=args.consume_time_limit, 
                                          labels=scaling_labels, 
                                          horizon=args.horizon)
        for label, out in results.items():
            logging.debug(out)

    if args.pddl_instance is not None:
        os.remove(trans_name)
