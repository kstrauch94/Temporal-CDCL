import os
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

import random

import config_file
from tools.tools import setup_logging, plasp_translate, plasp2_translate, get_parent_dir, create_folder

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
UNK = "UNKNOWN"
TIMEOUT = "TIMEOUT"
INTERRUPTED = "INTERRUPTED"
SAT = "SATISFIABLE"

class Nogood:

    def __init__(self, nogood_str, ordering, lbd=None, inc_t=False, transform_prime=False):

        #nogood_str: raw string printed out by the clingo call
        #ordering: line number of the nogood (the order in which the noogood was created)

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

        self.process_prime_literals()

        # here we choose which type of literal to use,
        # normal or without primes
        if transform_prime:
            self.literals = self.literals_without_primes
        else:
            self.literals = self.literals_normal

        self.process_time()

        self.validated = None
        self.instance_validated = None

        # time in the name refers to timepoint in the program
        self.instance_val_error_time = "-1" 

        self.random_id = random.randint(1, 999999999) # 999 999 999

    def process_literals(self, nogood_str):
        # this takes the raw nogood string and splits the atoms
        # into singular ones

        pre_literals = nogood_str.split(".")[0].replace(":-", "").strip()

        pre_literals = re.split(split_atom_re, pre_literals)

        self.literals_normal = []
        self.domain_literals = []

        for lit in pre_literals:
            if "{}(".format(OPENTIME) in lit:
                self.domain_literals.append(lit)

            else:
                self.literals_normal.append(lit)

    def process_prime_literals(self):

        self.literals_without_primes = self.literals_normal[:]

        for i, lit in enumerate(self.literals_normal):
            if "'" in lit:
                time = self._time_in_lit(lit)
                new_lit = re.sub(r"{t}(\)*){end}".format(t=time, end=END_STR), r"{t}\1{end}".format(t=time-1, end=END_STR), lit + END_STR)

                self.literals_without_primes[i] = new_lit.replace("'", "")

    def process_time(self):

        # matches with regular literals(prime literals still present)
        matches_regular = re.findall(time_no_s_re, END_STR.join(self.literals_normal)+END_STR)
        
        # get time matches only for step externals
        matches_step = re.findall(time_step_re, " ".join(self.domain_literals))

        matches_regular = [int(m) for m in matches_regular]
        matches_step = [int(m) for m in matches_step]

        self.max_time = max(matches_regular + matches_step)

        # minimum between the lowest point in the step atom -1 (since step atom only covers the higher timepoint of the transition)
        # and the lowest timepoint if the literals when no prime literals are present
        
        if len(matches_step) == 0:
            self.min_time = min(matches_regular)
        else: 
            # here, it is important to note that the lowest timepoint MAY contain prime literals. This is why we add the minimum T > 0
            # to the domain literals later on. We could also, just take the minimum point as the minimum of the transformed literals
            # but then, the degree and dif_to_min would be different
            self.min_time = min(min(matches_step)-1, min(matches_regular))
        
        self.dif_to_min = self.max_time - self.min_time

    @property
    def degree(self):
        return self.dif_to_min

    @property
    def literal_count(self):
        return len(self.literals)

    def _time_in_lit(self, lit):
        time = int(re.search(r"([0-9]+)\)*{end}".format(end=END_STR), lit + END_STR).group(1))

        return time

    def _generalize(self, literals):

        if len(literals) == 0:
            return []

        gen_literals = []

        for lit in literals:
            time = self._time_in_lit(lit)

            new_lit = re.sub(r"{t}(\)*){end}".format(t=time, end=END_STR), r"{t}-{dif}\1{end}".format(t=self.t, dif=self.max_time - time, end=END_STR), lit + END_STR)

            gen_literals.append(new_lit.replace(END_STR, ""))

        return gen_literals

    def generalize(self):
        t = time.time()
        self.literals = self._generalize(self.literals)

        self.domain_literals = self._generalize(self.domain_literals)

        if len(self.domain_literals) == 0:
            if self.t == "T":
                self.domain_literals += ["time(T)"]

        if self.min_time > 0:
            # minimum timepoint in the rule is 1 but only if
            # in the original rule the minimum was NOT 0
            self.domain_literals += ["{}-{} > 0".format(self.t, self.dif_to_min)]

        return time.time() - t
        
    def validate(self, files, walltime=0):
        #walltime in seconds
        t = time.time()

        literals = self.get_nogood()
        temp_validate = "temp_validate.lp"

        program = """#const degree={deg}.
hypothesisConstraint({t}-degree) {constraint}
:- not hypothesisConstraint(1).
""".format(deg=self.degree, t=self.t, constraint=self.to_constraint_any(literals))

        with open(temp_validate, "w") as f:
            f.write(program)

        # build call
        call = [config_file.RUNSOLVER_PATH, "-w", "runsolver.watcher"]
        if walltime is not None:
            call += ["-W", "{}".format(walltime)]

        call += ["clingo", "--quiet=2", "--stats", "--warn=none", temp_validate] + files

        logging.debug("calling : {}".format(" ".join(call)))

        try:
            output = subprocess.check_output(call).decode("utf-8")
        except subprocess.CalledProcessError as e:
            output = e.output.decode("utf-8")

        logging.debug(output)

        os.remove(temp_validate)
        os.remove("runsolver.watcher")

        if UNSAT in output:
            self.validated = True
            fail_reason = "none"

        else:
            self.validated = False

            logging.info("not validated: {}".format(self.to_constraint()))
            logging.info("number: {}".format(self.ordering))
            if TIMEOUT in output:
                logging.info("validation timed out!")

            fail_reason = "unknown"
            if SAT in output:
                fail_reason = "sat"
            if TIMEOUT in output or INTERRUPTED in output:
                fail_reason = "timeout"

            logging.info("fail reason: {}".format(fail_reason))

        time_taken = time.time() - t

        return time_taken, fail_reason

    def validate_instance(self, files, horizon=None, walltime=None):
        # walltime in seconds
        t = time.time()

        temp_validate = "temp_validate_inst.lp"

        program = """error({t}) {constraint}
error :- error(_).
:- not error.
#project error/0.
#show error/1.""".format(t=self.t, constraint=self.to_constraint())

        with open(temp_validate, "w") as f:
            f.write(program)

        # build call
        call = [config_file.RUNSOLVER_PATH, "-w", "runsolver.watcher"]
        if walltime is not None:
            call += ["-W", "{}".format(walltime)]

        call += ["clingo", "--quiet=1" ,"--warn=none", temp_validate] + files

        if horizon is not None:
            call += ["-c", "horizon={}".format(horizon)]

        logging.debug("calling : {}".format(call))

        try:
            output = subprocess.check_output(call).decode("utf-8")
        except subprocess.CalledProcessError as e:
            output = e.output.decode("utf-8")

        logging.debug(output)

        os.remove(temp_validate)
        os.remove("runsolver.watcher")

        if UNSAT in output:
            self.instance_validated = True
            fail_reason = "none"

        else:
            self.instance_validated = False
            self.instance_val_error_time = str(re.findall(error_re, output))

            logging.info("not validated: {}".format(self.to_constraint()))
            logging.info("number: {}".format(self.ordering))
            logging.info("error times: {}".format(self.instance_val_error_time))

            fail_reason = "unknown"
            if SAT in output:
                fail_reason = "sat"
            if TIMEOUT in output or INTERRUPTED in output:
                fail_reason = "timeout"

            logging.info("fail reason: {}".format(fail_reason))

        time_taken = time.time() - t

        return time_taken, fail_reason

    def issubset(self, other_ng):
        return set(self.all_literals).issubset(set(other_ng.all_literals))

    @property
    def all_literals(self):
        return self.literals + self.domain_literals

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

    CLINGO = [config_file.RUNSOLVER_PATH, "-W", "{}".format(time_limit), \
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

    CLINGO = [config_file.RUNSOLVER_PATH, "-W", "{}".format(time_limit), 
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

def extract_stats(nogoods):

    total_nogoods = len(nogoods)

    if total_nogoods == 0:
        return {"degree": {}, "lbd": {}, "size": {},
            "degree mean": None,
            "lbd mean": None,
            "size mean": None}

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

def scaling_by_value_total_count(stats, nogoods_wanted_by_count, sortby):

    if sortby[0] != "ordering" :
        if args.sortby[0] == "literal_count":
            stat_name = "size"
        elif args.sortby[0] == "degree":
            stat_name = "degree"
        elif args.sortby[0] == "lbd":
            stat_name = "lbd"

        # keep track of cumulative count of prev values
        total_count = 0 
        for i in range(nogoods_wanted_by_count + 1):
            if i in stats[stat_name]:
                count = int(stats[stat_name][i])
                total_count += count

    return total_count

def get_scaling_count_and_labels(new_nogoods, nogoods_wanted_by_count, sortby):

    stats = extract_stats(new_nogoods)

    if sortby[0] != "ordering" :
        if args.sortby[0] == "literal_count":
            stat_name = "size"
        elif args.sortby[0] == "degree":
            stat_name = "degree"
        elif args.sortby[0] == "lbd":
            stat_name = "lbd"

        print(stats[stat_name])

        scaling_by_val = []
        total_count = 0 # keep track of cumulative count of prev values
        scaling_labels = []
        for i in range(nogoods_wanted_by_count + 1):
            if i in stats[stat_name]:
                count = int(stats[stat_name][i])
                scaling_by_val.append(count + total_count)
                total_count += count
                scaling_labels.append(i)

    else:
        scaling_by_val = None
        scaling_labels = None

    return scaling_by_val, scaling_labels

def read_nogood_file(ng_file, max_deg, max_lit_count, inc_t, transform_prime):
    unprocessed_ng = []

    total_nogoods = 0

    with open(ng_file, "r") as f:
        for line in f:

            # if no lbd is found then the file was not written fully
            # if it is found then pass it as argument to not do this twice
            try:
                lbd = int(re.search(lbd_re, line).group(1))
            except AttributeError as e:
                continue

            total_nogoods += 1

            # line is the raw text of the nogood, line num is the order it appears in the file
            nogood = Nogood(line, total_nogoods, lbd, inc_t, transform_prime)
            # ignore nogoods of higher degree or literal count
            if max_deg >= 0 and nogood.degree > max_deg:
                continue
            if max_lit_count > 0 and nogood.literal_count > max_lit_count:
                continue

            unprocessed_ng.append(nogood)

    # line-num should be the amount of nogoods in the raw file
    return unprocessed_ng, total_nogoods

def check_nogood_str(ng_str, max_deg, max_lit_count):
    # if no lbd is found then the file was not written fully
    # if it is found then pass it as argument to not do this twice
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


def generalize_nogoods(ng_list, nogoods_wanted, grab_last, 
                       validate_files, validate_instance, validate_instance_files,
                       horizon, val_walltime):

    validate = validate_files is not None

    lines_set = set()
    repeats = 0
    nogoods_generalized = 0
    nogoods = []
    ng_count = len(ng_list)

    time_generalize = 0

    not_validated = 0
    not_instance_validated = 0

    validation_time = 0
    instance_validation_time = 0

    fail_reason_counter = Counter()
    fail_reason_instance_counter = Counter()

    subsumed_fail_count = 0

    if grab_last:
        ng_list = reversed(ng_list)

    for num, ng in enumerate(ng_list):
        time = ng.generalize()
        time_generalize += time
        # if nogood is not a repeat we add it to the list
        line = ng.to_constraint()
        if line not in lines_set:
            # check if we want to validate or not
            if validate:
                time, fail_reason = ng.validate(validate_files, walltime=val_walltime)
                validation_time += time
                if not ng.validated:
                    not_validated += 1
                    fail_reason_counter[fail_reason] += 1

            if validate_instance:
                time, fail_reason = ng.validate_instance(validate_instance_files, horizon=horizon, walltime=val_walltime)
                instance_validation_time += time
                if not ng.instance_validated:
                    not_instance_validated += 1
                    fail_reason_instance_counter[fail_reason] += 1

            if (validate and not ng.validated) or (validate_instance and not ng.instance_validated):
                continue

            nogoods, success, deleted = check_subsumed(nogoods, ng)

            # if its not a repeat and not subsumed then add it to the lines to check for repeats
            # even if eliminated are in the repeat line, if its a repeat anyway it would be eliminated
            # by one of the nogoods added previously
            # also, only update amount generalized if its a success
            # since for no success we get the same list
            if success:
                lines_set.add(line)
                nogoods_generalized = len(nogoods)
                subsumed_fail_count += deleted
            else:
                subsumed_fail_count += 1                
        else:
            repeats += 1

        # if nogoods_wanted is a valid value
        # and the amount of nogoods we have is higher or equal
        # than the amount we want
        if nogoods_wanted > 0 and nogoods_generalized >= nogoods_wanted:
            break

        if num % 100 == 0:
            logging.info("Checked {} of {} nogoods for generalization.".format(num, ng_count))
            logging.info("Generalized {} of {} checked nogoods.".format(nogoods_generalized, num))

    if grab_last:
        nogoods = list(reversed(nogoods))


    if validate_files is not None:
        logging.info("Failed {} validations".format(not_validated))
        if not_validated > 0:
            line = " - ".join(["{} : {}".format(reason, amount) for reason, amount in fail_reason_counter.items()])
            logging.info("Reasons for validation failure: {}".format(line))

    if validate_instance:
        logging.info("Failed {} validations within the instance".format(not_instance_validated))
        if not_instance_validated > 0:
            line = " - ".join(["{} : {}".format(reason, amount) for reason, amount in fail_reason_instance_counter.items()])
            logging.info("Reasons for instance validation failure: {}".format(line))

    logging.info("subsumed failures: {}".format(subsumed_fail_count))

    return nogoods, repeats, time_generalize, validation_time, instance_validation_time

class Stat:

    def __init__(self, name, value, message):
        self.name = name
        self.value = value
        self._message = message


    @property
    def message(self):
        return self._message.format(self.value)
    
def convert_ng_file(ng_name, converted_ng_name,
                    no_generalization=False,
                    max_deg=10,
                    max_lit_count=50,
                    nogoods_wanted=100,
                    nogoods_wanted_by_count=-1,
                    sortby=["ordering"], 
                    validate_files=None, 
                    reverse_sort=False,
                    validate_instance=False,
                    validate_instance_files=None,
                    inc_t=False,
                    transform_prime=False,
                    grab_last=False,
                    horizon=None,
                    no_nogood_stats=False,
                    val_walltime=None):

    # sortby should be a list of the int attributes in the nogood:
    # lbd, ordering, degree, literal_count
    conversion_time = time.time()

    conversion_stats = {}

    converted_lines = []
    amount_validated = 0
    amount_instance_validated = 0

    failed_to_validate = []

    # read nogoods
    
    total_nogoods = 0

    time_generalize = 0

    logging.info("converting...")
    
    t = time.time()

    if not os.path.isfile(ng_name):
        logging.info("nogood file does not exist!")
        return None, None, None

    unprocessed_ng, total_nogoods = read_nogood_file(ng_name, max_deg, max_lit_count, inc_t, transform_prime)
    total_nogoods_after_processing = len(unprocessed_ng)

    time_init_nogood = time.time() - t
    conversion_stats["time_init_nogood"] = Stat("time_init_nogood", time_init_nogood, "time initializing nogoods: {}")

    conversion_stats["total_raw_nogoods"] = Stat("total_raw_nogoods", total_nogoods, "total lines in the raw nogood file: {}\n")
    conversion_stats["total_raw_nogoods_after_filters"] = Stat("total_raw_nogoods_after_filters", total_nogoods_after_processing, "total nogoods after filtering by degree and size: {}\n")

    logging.info(conversion_stats["total_raw_nogoods"].message)
    logging.info(conversion_stats["total_raw_nogoods_after_filters"].message)
    if total_nogoods == 0:
        logging.info("no nogoods learned...")
        return None, None, None

    t = time.time()
    if sortby is not None:
        unprocessed_ng.sort(key=lambda nogood : get_sort_value(nogood, sortby), reverse=reverse_sort)

    time_sorting_nogoods = time.time() - t    

    conversion_stats["time_sorting_nogoods"] = Stat("time_sorting_nogoods", time_sorting_nogoods, "time sorting nogoods: {}")

    # extract some stats about some nogood properties
    t = time.time()
    stats = extract_stats(unprocessed_ng)
    time_extract_stats = time.time() - t
    conversion_stats["time_extract_stats"] = Stat("time_extract_stats", time_extract_stats, "time to extract stats: {}")

    if not no_nogood_stats:

        t = time.time()
        for key, val in stats.items():
            if "mean" not in key:
                logging.info("{} {}".format(key, sorted(val.items())))
            else:
                logging.info("{} {}".format(key, val))

        time_logging_stats = time.time() - t

        conversion_stats["time_logging_stats"] = Stat("time_logging_stats", time_logging_stats, "time to log stats: {}")

    else:
        conversion_stats["time_logging_stats"] = Stat("time_logging_stats", 0, "time to log stats: {}")


    # get the scaling amounts and the nogoods count we want
    if nogoods_wanted_by_count >= 0:
        nogoods_wanted = scaling_by_value_total_count(stats, nogoods_wanted_by_count, sortby)
    else:
        scaling_by_val = None
        scaling_labels = None

    if no_generalization == False:    

        nogoods, repeats, time_generalize, validation_time, instance_validation_time = generalize_nogoods(unprocessed_ng, 
                                                                                        nogoods_wanted, 
                                                                                        grab_last, 
                                                                                        validate_files, 
                                                                                        validate_instance, 
                                                                                        validate_instance_files, 
                                                                                        horizon,
                                                                                        val_walltime)
        conversion_stats["time_generalize"] = Stat("time_generalize", time_generalize, "time to generalize: {}")

        conversion_stats["repeats"] = Stat("repeats", repeats, "{} nogoods were identical")

        if nogoods_wanted_by_count >= 0:
            scaling_by_val, scaling_labels = get_scaling_count_and_labels(nogoods, nogoods_wanted_by_count, sortby)


        total_nogoods = len(nogoods)
        conversion_stats["total_nogoods_generalized"] = Stat("total_nogoods_generalized", total_nogoods, "Total nogoods after generalizing: {}")

        logging.info(conversion_stats["total_nogoods_generalized"].message)

        conversion_stats["time_validate"] = Stat("time_validate", validation_time, "time to validate: {}")
        conversion_stats["time_validate_instance"] = Stat("time_validate_instance", instance_validation_time, "time to validate within instance: {}")

        # log some info after finishing
        logging.info("Finished converting!\n")

        logging.info(conversion_stats["time_generalize"].message)
        if validate_files is not None:
            logging.info(conversion_stats["time_validate"].message)
        if validate_instance:
            logging.info(conversion_stats["time_validate_instance"].message)


    else:
        # if we don't generalize then nogoods is just the n first
        # from the list (since it should be sorted in the correct order anyway)
        # if nogoods wanted is 0 or less then we take all nogoods
        if nogoods_wanted > 0:
            nogoods = unprocessed_ng[:nogoods_wanted]
        else:
            nogoods = unprocessed_ng

    t = time.time()

    with open(converted_ng_name, "w") as f:
        for conv_line in nogoods:
            line = conv_line.to_constraint()
            f.write(str(line))
    
    time_writing_file = time.time() - t
    conversion_stats["time_writing_file"] = Stat("time_writing_file", time_writing_file, "time writing file: {}")


    logging.info(conversion_stats["repeats"].message)
    logging.info(conversion_stats["time_extract_stats"].message)
    logging.info(conversion_stats["time_logging_stats"].message)

    logging.info(conversion_stats["time_init_nogood"].message)
    logging.info(conversion_stats["time_sorting_nogoods"].message)
    logging.info(conversion_stats["time_writing_file"].message)

    conversion_time = time.time() - conversion_time

    conversion_stats["time_conversion_jobs"] = Stat("time_conversion_jobs", conversion_time, "time to do conversion jobs: {}")    

    return conversion_stats, scaling_by_val, scaling_labels

def produce_nogoods(file_names, args, config):

    if args.use_existing_ng_file is None:

        logging.info("Starting nogood production...")

        ng_name = args.ng_file_name

        NG_RECORDING_OPTIONS = ["--lemma-out-txt",
                            "--lemma-out=-",
                            "--lemma-out-dom=output", 
                            "--heuristic=Domain", 
                            "--dom-mod=level,show",
                            "--quiet=2",
                            "--stats",
                            "--loops=no", "--reverse-arcs=0", "--otfs=0"]

        if int(args.nogoods_limit) > 0:
            lemma_out_max = ["--lemma-out-max={}".format(args.nogoods_limit)]
        else:
            lemma_out_max = []


        if args.horizon is not None:
            horizon = ["-c", "horizon={}".format(args.horizon)]
        else:
            horizon = []

        NG_RECORDING_OPTIONS += lemma_out_max + horizon + ["0"]

        # call clingo to extract nogoods
        t = time.time()
        if args.no_nogood_logging_filter:
            # if no filter: add the correct values to max def and max lit so that there is no limit
            call_clingo_pipe(file_names, args.max_extraction_time, NG_RECORDING_OPTIONS,
                             ng_name, -1, 0)
        else:
            call_clingo_pipe(file_names, args.max_extraction_time, NG_RECORDING_OPTIONS,
                             ng_name, args.max_deg, args.max_lit_count)
        time_extract = time.time() - t

    else:
        if not os.path.isfile(args.use_existing_ng_file):
            logging.error("The nogood file provided does not exist. Exiting...")
            sys.exit(-1)

        ng_name = args.use_existing_ng_file
        time_extract = 0


    converted_ng_name = args.generalized_ng_file_name

    # convert the nogoods
    stats, scaling_by_val, scaling_labels = convert_ng_file(ng_name, converted_ng_name,
                    **config)

    logging.info("time to extract: {}".format(time_extract))
    if stats is not None:
        logging.info(stats["time_conversion_jobs"].message)
    
    try:
        #os.remove(ng_name)
        pass
    except OSError:
        logging.warning("Tried to remove {} but it was already deleted!".format(ng_name))

    return converted_ng_name, scaling_by_val, scaling_labels

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('--files', metavar='f', nargs='+', help="Files to run clingo on not including instance")
    parser.add_argument('--instance', metavar='i', help="Instance file. If file has a .pddl extension it will be treated as a pddl instance.")

    parser.add_argument("--pddl-instance", help="pddl instance")
    parser.add_argument("--pddl-domain", help="pddl domain", default=None)
    parser.add_argument("--trans-name", help="name of the translated file")
    parser.add_argument("--no-fd", action="store_true", help="When translating the pddl instance, do not use Fast Downward preprocessing.")
    parser.add_argument("--horizon", help="horizon will be added to clingo -c horizon=<h>", type=int, default=None)

    parser.add_argument("--ng-file-name", help="name of the file that the nogoods will be saved to. Default=ng_temp.lp", default="ng_temp.lp")
    parser.add_argument("--generalized-ng-file-name", help="name of the file that the nogoods will be saved to. Default=conv_ng.lp", default="conv_ng.lp")

    parser.add_argument("--use-existing-ng-file", help="Process and existing nogood file.", metavar="file", default=None)

    parser.add_argument("--grab-last", action="store_true", help="Grab the last N nogoods. E.G. list=[1,2,3,4,5,6] and we want 2 nogoods: no --grab-last result is [1,2]. with --grab-last result is [5,6] ")
    parser.add_argument("--no-generalization", action="store_true", help="Don't generalize the learned nogoods")
    parser.add_argument("--sortby", nargs='+', help="attributes that will sort the nogood list. The order of the attributes is the sorting order. Choose from [degree, literal_count, ordering, lbd, random_id]. default: ordering", default=["ordering"])
    parser.add_argument("--reverse-sort", action="store_true", help="Reverse the sort order.")
    parser.add_argument("--inc_t", action="store_true", help="use the incremental 't' instead of the normal 'T'")
    parser.add_argument("--transform-prime", action="store_true", help="Transform prime atoms to their non prime variant. E.G. holds'(T) --> holds(T-1)")

    parser.add_argument("--validate-files", nargs='+', help="file used to validate learned constraints. If no file is provided validation is not performed.", default=None)
    parser.add_argument("--validate-instance", action="store_true", help="With this option the constraints will be validated with a search by counterexamples using the files and instances provided.")
    parser.add_argument("--val-walltime", help="Walltime for the validation of each nogood in seconds. Default is no walltime.", default=None)

    parser.add_argument("--nogoods-limit", help="Solving will only find up to this amount of nogoods for processing. Default = 0, 0 = no limit", default=0, type=int)

    parser.add_argument("--nogoods-wanted", help="Nogoods processed will stop after this amount. Default = 0, 0 = no limit", default=0, type=int)
    parser.add_argument("--nogoods-wanted-by-count", help="Nogoods that have a value equal or less than the one given here in the variable given in the first position of the sortby option(does not work for ordering).", default=-1, type=int)

    parser.add_argument("--max-deg", help="Processing will ignore nogoods with higher degree. Default = -1. A negative number means no limit.", default=-1, type=int)
    parser.add_argument("--max-lit-count", help="Processing will ignore nogoods with higher literal count. Default = 0. 0 or a negative number means no limit.", default=0, type=int)

    parser.add_argument("--max-extraction-time", default=20, type=int, help="Time limit for nogood extraction in seconds. Default = 20")

    parser.add_argument("--no-nogood-stats", action="store_true", help="Do not show the stats on nogoods(degree, size and lbd count)")
    parser.add_argument("--no-nogood-logging-filter", action="store_true", help="Do not filter the nogoods by literal count or degree on the nogoods logging stage(on the first clingo call)")

    parser.add_argument("--logtofile", help="log to a file")

    parser.add_argument("--no-stream-output", action="store_true", help="Supress output to the console")

    parser.add_argument("--version", action="store_true", help="Print version information and exit.")

    args = parser.parse_args()

    setup_logging(args.no_stream_output, args.logtofile)

    if args.version:
        logging.info(subprocess.check_output([config_file.PLASP, "--version"]).decode("utf-8"))
        logging.info(subprocess.check_output([config_file.RUNSOLVER_PATH, "--version"]).decode("utf-8"))
        logging.info("last git commit: " + subprocess.check_output(["git", "show", "--name-status"]).decode("utf-8"))

        sys.exit(0)

    files = args.files

    config = {}

    config["no_generalization"] = args.no_generalization
    config["validate_files"] = args.validate_files
    config["validate_instance"] = args.validate_instance
    config["val_walltime"] = args.val_walltime
    config["sortby"] = args.sortby
    config["reverse_sort"] = args.reverse_sort

    config["max_deg"] = args.max_deg
    config["max_lit_count"] = args.max_lit_count
    config["nogoods_wanted"] = args.nogoods_wanted
    config["nogoods_wanted_by_count"] = args.nogoods_wanted_by_count
    config["inc_t"] = args.inc_t
    config["transform_prime"] = args.transform_prime
    config["grab_last"] = args.grab_last
    config["horizon"] = args.horizon
    config["no_nogood_stats"] = args.no_nogood_stats

    if args.instance is not None and args.instance.endswith(".pddl"):
        args.pddl_instance = args.instance

        args.instance = None

    if args.pddl_instance is not None:
        if args.trans_name is not None:
            trans_name = args.trans_name
        else:
            trans_name = "instance-temp.lp"

        # check plasp version
        output = subprocess.check_output([config_file.PLASP, "--version"]).decode("utf-8")
        logging.info(output)
        if "plasp 2." in output:
            plasp2_translate(args.pddl_instance, args.pddl_domain, trans_name)
        elif "plasp version 3." in output:
            plasp_translate(args.pddl_instance, args.pddl_domain, trans_name, args.no_fd)

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
    
    if scaling_by_val is not None:
        scaling_by_val = ",".join([str(v) for v in scaling_by_val])
        scaling_labels = ",".join([str(v) for v in scaling_labels])

        logging.info("Scaling by value amounts: {}".format(scaling_by_val))
        logging.info("Scaling by value labels : {}".format(scaling_labels))


    #if args.pddl_instance is not None:
    #    os.remove(trans_name)
