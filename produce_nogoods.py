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

time_re = r"s\(([0-9]+)\)"

answer_re = r"Answer: [0-9]+\n(.*)\n"

models_re = r"Models       : ([0-9]+)"

lbd_re = r"lbd = ([0-9]+)"

UNSAT = "UNSATISFIABLE"

FD_CALL = ["/home/klaus/bin/Fast-Downward/fast-downward.py", "--translate"]


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

    def __init__(self, nogood_str, ordering):

        #nogood_str: raw string printed out by the clingo call
        #ordering: line number of the nogood (the order in which the noogood was created)

        self.raw_str = nogood_str

        # split by a . and then get the first element and add the . 
        # do this to delete the lbd part at the end
        self.raw = nogood_str.split(".")[0] + "."
        
        self.ordering = ordering

        self.lbd = int(re.search(lbd_re, nogood_str).group(1))

        self.process_literals()

        self.raw_literal_count = len(self.literals)

        logging.debug("literal count: {}".format(self.raw_literal_count))

        self.process_time()

        self.generalized = None
        self.minimized = None

        self.validated = None

    def process_literals(self):

        pre_literals = self.raw.replace(":-", "").replace(".","").strip()
        # regex from 
        # https://stackoverflow.com/questions/9644784/python-splitting-on-spaces-except-between-certain-characters
        # split on commas followed by whitespace except when between ""
        # the comma at the beggining was added by me
        pre_literals = re.split(r",\s+(?=[^()]*(?:\(|$))", pre_literals)

        self.literals = []
        self.domain_literals = []

        for lit in pre_literals:
            if "external(next" in lit or "next(" in lit:
                self.domain_literals.append(lit)

            else:
                self.literals.append(lit)

    def sanitize_literals(self):
        old_lit = self.literals[:]
        new_lit = []

        candidate = ""
        while old_lit != []:
            if candidate != "":
                candidate += ", " + old_lit[0]
            else:
                candidate += old_lit[0]

            old_lit.remove(old_lit[0])

            if candidate.count("(") != candidate.count(")"):
                continue
            else:
                new_lit.append(candidate)
                candidate = ""

        self.literals = new_lit

    def process_time(self):

        matches = re.findall(time_re, self.raw)
        matches = [int(m) for m in matches]

        self.max_time = max(matches)
        # dif_to_min would be the degree
        self.dif_to_min = self.max_time - min(matches)

    @property
    def degree(self):
        return self.dif_to_min

    @property
    def literal_count(self):
        return len(self.get_nogood())

    def _generalize(self, literals):

        if len(literals) == 0:
            return []

        split_str = "-.-.-"

        generalized = split_str.join(literals)
        generalized = generalized.replace("s({})".format(self.max_time), "s(T)")        
        # +1 to include the number
        # since the i will be the number to subtract to the time
        for i in range(1, self.dif_to_min+1):
            generalized = generalized.replace("s({})".format(self.max_time-i), "s(T-{})".format(i))
        
        # careful here, maybe there is an extra empty item at the end
        return generalized.split(split_str)

    def generalize(self):

        self.generalized = self._generalize(self.literals)

        self.domain_literals = self._generalize(self.domain_literals)

        # add time atoms
        self.domain_literals += ["time(s(T))", "time(s(T-{}))".format(self.dif_to_min)]

    def minimize(self, files):
        t = time.time()
        # files is a list of the needed files to run the validation

        logging.debug("minimizing")

        lit_len = len(self.generalized)
        if lit_len == 1: # already minimal 
            self.minimized = self.generalized

            return 1

        unknown = self.generalized[:]
        needed = []

        # this should go through every literal and see if its needed to keep the contraint working
        # if it isnt it just gets deleted
        # else if will be flagged as needed
        # in the end the literals in needed are the ones that keep the constraint working
        for i in range(lit_len):
            delete_candidate = self.generalized[i]

            unknown.remove(delete_candidate)

            lits_to_validate = needed + unknown + self.domain_literals

            validated = self._validate(files, lits_to_validate)

            # there was a counterexample
            if not validated:
                needed.append(delete_candidate)

        self.minimized = needed
        logging.debug("initial literals: {}\nFinal literals: {}\n".format(self.raw_literal_count, len(self.minimized)))
        logging.debug("minimized: {}".format(self.minimized))

        logging.info("time minimize: {}".format(time.time() - t))

        return 1

    def minimize_optimized(self, files):
        t = time.time()
        # files is a list of the needed files to run(e.g. encoding + instance)
        logging.debug("minimizing")

        lit_len = len(self.generalized)
        if lit_len == 1: # already minimal 
            self.minimized = self.generalized

            return self.minimized

        unknown = self.generalized[:]
        needed = []

        # this should go through every literal and see if its needed to keep the contraint working
        # if it isnt it just gets deleted
        # else if will be flagged as needed
        # in the end the literals in needed are the ones that we keep
        i = 0
        elim_window_inc = 0
        while i <= lit_len - 1:
            if elim_window_inc == 0:
                delete_candidate = self.generalized[i]

                unknown.remove(delete_candidate)

                lits_to_validate = needed + unknown + self.domain_literals

                validated = self._validate(files, lits_to_validate)

                # there was a counterexample
                if not validated:
                    needed.append(delete_candidate)

                else: # on succesful eliminations increase window
                    elim_window_inc += 1

                i += 1

            else:
                delete_candidates = self.generalized[i:i+elim_window_inc]

                test_unknown = [e for e in unknown if e not in delete_candidates]

                lits_to_validate = needed + test_unknown + self.domain_literals

                validated = self._validate(files, lits_to_validate)

                if not validated:
                    # reset elim window to 0
                    # don't change the i so that in the next run it looks at the first
                    # item alone
                    elim_window_inc = 0
                else:
                    # if it worked increase i by the window
                    i += elim_window_inc
                    # and icnrease the window
                    elim_window_inc += 1
                    # use the unknown with the useless literals
                    unknown = test_unknown

        self.minimized = needed
        logging.debug("minimized from {} to {}\n".format(self.raw_literal_count, len(self.minimized)))
        logging.debug("minimized: {}".format(self.minimized))

        logging.debug("time minimize opt: {}".format(time.time() - t))


        return self.minimized

    def _validate(self, files, literals):
        temp_validate = "temp_validate.lp"

        call = ["clingo", "--quiet=2", temp_validate] + files

        logging.debug("calling : {}".format(call))


        program = """#const degree={}.
hypothesisConstraint(s(T-degree)) {}
""".format(self.degree, self.to_constraint_any(literals))

        with open(temp_validate, "w") as f:
            f.write(program)

        try:
            output = subprocess.check_output(call)
        except subprocess.CalledProcessError as e:
            output = e.output

        logging.debug(output)

        os.remove(temp_validate)

        if UNSAT in output:
            return True

        else:
            return False

    def validate_instance(self, files):

        temp_validate = "temp_validate_inst.lp"

        call = ["clingo", "--quiet=2", temp_validate] + files

        logging.debug("calling : {}".format(call))

        program = """error {}
:- not error.
#project error/0.
#show error/0.""".format(self.to_constraint())

        with open(temp_validate, "w") as f:
            f.write(program)

        try:
            output = subprocess.check_output(call)
        except subprocess.CalledProcessError as e:
            output = e.output

        logging.debug(output)

        os.remove(temp_validate)

        if UNSAT in output:
            return True

        else:
            return False

    def validate_self(self, files):

        self.validated = self._validate(files, self.get_nogood())

    def to_constraint(self):
        return ":- " +  ", ".join(self.get_nogood()) + ".\n"

    def to_rule(self):
        return "error({}) ".format(self.ordering) + self.to_constraint()

    def to_rule_any(self, literals):
       return "error({}) ".format(self.ordering) + ":- " +  ", ".join(literals) + ".\n"

    def to_constraint_any(self, literals):
        return ":- " +  ", ".join(literals) + ".\n"

    def get_nogood(self):
        if self.minimized is not None:
            return self.minimized + self.domain_literals

        elif self.generalized is not None:
            return self.generalized + self.domain_literals

        else:
            return self.literals + self.domain_literals

    def __str__(self):
        # returns a string version of the nogood
        return self.to_constraint()

def get_sort_value(object, attributes):
    val = []

    for attr in attributes:
        val.append(getattr(object, attr))

    return val

def call_clingo(file_names, options):

    CLINGO = ["clingo"] + file_names

    call = CLINGO + options

    logging.info("calling: " + " ".join(call))

    try:
        output = subprocess.check_output(call)
    except subprocess.CalledProcessError as e:
        output = e.output

    logging.info("call has finished\n")

    logging.info(output)

    #logging.info("Models: {}".format(re.findall(models_re, output)))

def convert_ng_file(ng_name, converted_ng_name, 
                    minimal=False, 
                    sortby=["degree", "literal_count"], 
                    validate_files=None, 
                    reverse_sort=False,
                    validate_instance_files=None):

    # sortby should be a list of the int attributes in the nogood:
    # lbd, ordering, degree, literal_count

    converted_lines = []
    amount_validated = 0
    amount_instance_validated = 0

    # just so that we dont check multiple times
    validate = validate_files is not None

    # read nogoods
    with open(ng_name, "r") as f:
        lines = f.readlines()


    total_nogoogds = len(lines)
    logging.info("\ntotal lines in the no good file: {}\n".format(total_nogoogds))
    if total_nogoogds == 0:
        logging.info("no nogoods learned...")
        return 0


    time_generalize = 0
    time_validate = 0
    time_validate_instance = 0


    logging.info("converting...")


    # use patricks flowchart
    # first read nogoods and generalize them
    # then sort them
    # later, validate
    # finally minimize if wanted

    nogoods = []
    for line_num, line in enumerate(lines):
        # line is the raw text of the nogood, line num is the order it appears in the file
        ng = Nogood(line, line_num)

        t = time.time()
        ng.generalize()
        time_generalize += time.time() - t

        nogoods.append(ng)

    if sortby is not None:
        nogoods.sort(key=lambda nogood : get_sort_value(nogood, sortby), reverse=reverse_sort)


    if validate:
        for ng in nogoods:

            # this part is the normal validation as patrick does it
            t = time.time()
            ng.validate_self(validate_files)
            time_validate = time.time() - t

            logging.debug("validated: {}".format(ng.validated))

            if ng.validated:
                if minimal:
                    #ng.minimize(validate_files)
                    ng.minimize_optimized(validate_files)

                converted_lines.append(ng)
                amount_validated += 1

            else:
                logging.info("not validated: {}".format(ng.to_constraint()))
                logging.info("number: {}".format(ng.ordering))

            
            # this part is validating within the instance
            t = time.time()
            instance_val = ng.validate_instance(validate_instance_files)
            time_validate_instance = time.time() - t
            
            if not instance_val:
                logging.info("Result of instance val: {}".format(instance_val))
                logging.info("number: {}".format(ng.ordering))
            else:
                amount_instance_validated += 1

            if instance_val != ng.validated:
                logging.info("validations do not match")
                logging.info("Normal validation: {}".format(ng.validated))
                logging.info("Instance validation: {}".format(instance_val))
                logging.info("constraint: {}".format(str(ng)))

    # if not validating use all of them
    else:
        converted_lines = nogoods

    # write generelized nogoods into a file
    with open(converted_ng_name, "w") as f:
        for conv_line in converted_lines:
            line = conv_line.to_constraint()

            f.write(str(line))

    logging.info("Finished converting!\n")

    if validate:
        logging.info("Validated {} of {} nogoods".format(amount_validated, total_nogoogds))
        logging.info("Validated {} of {} nogoods withing the instance".format(amount_instance_validated, total_nogoogds))

    logging.info("time to generelize: {}".format(time_generalize))
    if validate:
        logging.info("time to validate: {}".format(time_validate))
        logging.info("time to validate within instance: {}".format(time_validate_instance))
        
    return 1


def get_parent_dir(path):
    # this gets the name of the parent folder

    # if there is a trailing backslash then delete it
    if path.endswith("/"):
        path = path[:-1]

    return os.path.dirname(path)

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

    output = subprocess.check_output(fd_call)
    #print(output)

    plasp_call = ["plasp", "translate", "output.sas"]

    output = subprocess.check_output(plasp_call)
    with open(filename, "w") as f:
        f.write(output)

    logging.info("saved translation into {}".format(filename))

    os.remove("output.sas")


def produce_nogoods(file_names, nogoods_limit, extraction_time, config):

    logging.info("Starting nogood production...")

    ng_name = "ng_temp.lp"
    converted_ng_name =  "conv_ng.lp"

    NG_RECORDING_OPTIONS = ["--lemma-out-txt",
                        "--lemma-out={}".format(ng_name),
                        "--lemma-out-dom=output", 
                        "--heuristic=domain", 
                        "--dom-mod=1,16",
                        "--lemma-out-max={}".format(nogoods_limit),
                        "--time-limit={}".format(extraction_time),
                        "--quiet=2",
                        "1"]

    # call clingo to extract nogoods
    t = time.time()
    call_clingo(file_names, NG_RECORDING_OPTIONS)
    time_extract = time.time() - t

    # convert the nogoods
    convert_ng_file(ng_name, converted_ng_name, **config)

    logging.info("time to extract: {}".format(time_extract))

    #os.remove(ng_name)

    return converted_ng_name

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


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('--files', metavar='f', nargs='+', help="Files to run clingo on not including instance")
    parser.add_argument('--instance', metavar='i', help="Instance file")

    parser.add_argument("--pddl-instance", help="pddl instance")
    parser.add_argument("--pddl-domain", help="pddl domain", default=None)
    parser.add_argument("--trans-name", help="name of the translated file")

    parser.add_argument("--config", help="File with a CONFIG dictionary where the configuration of the nogood is stored.")

    parser.add_argument("--nogoods-limit", help="Solving will only find up to this amount of nogoods for processing")

    parser.add_argument("--max-extraction-time", default=20, type=int, help="Time limit for nogood extraction in seconds.")

    parser.add_argument("--logtofile", help="log to a file")

    parser.add_argument("--consume", action="store_true", help="consume the generated nogoods based on the given scaling")

    parser.add_argument("--scaling", help="scaling of how many nogoods to use. format=start,factor,count. Default = 8,2,5", default="8,2,5")


    args = parser.parse_args()

    setup_logging(args.logtofile)

    files = args.files
    instance = args.instance

    config = {}
    if args.config is not None:
        config_file = __import__(args.config)
        config = config_file.CONFIG

    if args.pddl_instance is not None:
        if args.trans_name is not None:
            trans_name = args.trans_name
        else:
            trans_name = "instance-temp.lp"

        plasp_translate(args.pddl_instance, args.pddl_domain, trans_name)

        instance = trans_name

    if args.instance is not None:
        instance = args.instance

    files.append(instance)

    if config["validate_files"] is not None:
        # last value in files should be instance
        config["validate_files"] += [instance]

        config["validate_instance_files"] = files


    # maybe pass the nogoods directly instead of file?
    converted_nogoods = produce_nogoods(files, args.nogoods_limit,
                                        args.max_extraction_time, config)

    if args.consume:
        times = consume_nogoods.run_tests(files, converted_nogoods, args.scaling)
        logging.info(times)