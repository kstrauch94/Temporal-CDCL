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

END_STR = "asdasdasd"
time_no_s_re = r"([0-9]+)\)*{end_str}".format(end_str=END_STR)

answer_re = r"Answer: [0-9]+\n(.*)\n"

models_re = r"Models       : ([0-9]+)"

lbd_re = r"lbd = ([0-9]+)"

error_re = r"error\(([0-9]+)\)"

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
        #self.process_prev()
        self.process_domain_literals()

        self.raw_literal_count = len(self.literals)

        logging.debug("literal count: {}".format(self.raw_literal_count))

        self.process_time()

        self.generalized = None
        self.minimized = None

        self.validated = None
        self.instance_validated = None
        self.instance_val_error_time = "-1"

    def process_literals(self):
        # this takes the raw nogood string and splits the atoms
        # into singular ones

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


    def process_prev(self):
        # since we are not using this function it wasnt updated to the new time format
        # Ill leave the function here in case we need it in the future

        for idx, atom in enumerate(self.literals, start=0):
            if "prev_" in atom:
                new_atom = atom.replace("prev_", "")

                time_match = int(re.search(time_re, new_atom).group(1))

                new_atom = new_atom.replace("s({})".format(time_match), "s({})".format(time_match-1))

                self.literals[idx] = new_atom

                new_dom_lit = "not external(next(s({}),s({})))".format(time_match-1, time_match)
                if new_dom_lit not in self.domain_literals:
                    self.domain_literals.append(new_dom_lit)

    def process_domain_literals(self):
        # here we create "next" literals out of the not external literals
        # as a form of handling the domain of the time 

        for idx, dl in enumerate(self.domain_literals, start=0):
            if "not external(" in dl:
                # delete the not external and the last parenthesis )
                new_dl = dl.replace("not external(", "")[:-1]

                self.domain_literals.append(new_dl)


    def process_time(self):
        # finding the max doesnt take into account the first value of the external(next(T1,T2))
        # because that value will never be the max anyway

        matches = re.findall(time_no_s_re, END_STR.join(self.literals)+END_STR)
        matches += re.findall(time_no_s_re, END_STR.join(self.domain_literals)+END_STR)
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

        gen_literals = []

        for lit in literals:
            time = int(re.search(r"([0-9]+)\)*{end}".format(end=END_STR), lit + END_STR).group(1))

            new_lit = re.sub(r"{t}(\)*){end}".format(t=time, end=END_STR), r"T-{dif}\1{end}".format(dif=self.max_time - time, end=END_STR), lit + END_STR)

            if "external(next(" in lit or "next(" in lit:
                new_lit = re.sub(r"next\({t},".format(t=time-1), r"next(T-{dif},".format(dif=self.max_time - time + 1), new_lit)


            gen_literals.append(new_lit.replace(END_STR, ""))

        # there is an extra empty item at the end, so we delete it
        return gen_literals

    def generalize(self):

        self.generalized = self._generalize(self.literals)

        self.domain_literals = self._generalize(self.domain_literals)

        if self.dif_to_min == 0:
            self.domain_literals += ["time(T)"]

        # minimum timepoint in the rule is 1
        self.domain_literals += ["T-{} > 0".format(self.dif_to_min)]

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
hypothesisConstraint(T-degree) {}
:- not hypothesisConstraint(1).
""".format(self.degree, self.to_constraint_any(literals))

        with open(temp_validate, "w") as f:
            f.write(program)

        try:
            output = subprocess.check_output(call).decode("utf-8")
        except subprocess.CalledProcessError as e:
            output = e.output.decode("utf-8")

        logging.debug(output)

        os.remove(temp_validate)

        if UNSAT in output:
            return True

        else:
            return False

    def validate_instance(self, files):

        temp_validate = "temp_validate_inst.lp"

        call = ["clingo", "--quiet=1", temp_validate] + files

        logging.debug("calling : {}".format(call))

        program = """error(T) {}
error :- error(_).
:- not error.
#project error/0.
#show error/1.""".format(self.to_constraint())

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
        output = subprocess.check_output(call).decode("utf-8")
    except subprocess.CalledProcessError as e:
        output = e.output.decode("utf-8")

    logging.info("call has finished\n")

    logging.info(output)

    #logging.info("Models: {}".format(re.findall(models_re, output)))

def validate_instance_all(files):
    # files argument contains the encoding, instance and the file containing all nogoods to be proven
    # + the program that searches for counterexamples

    call = ["clingo", "--quiet=1"] + files

    logging.debug("calling : {}".format(call))

    try:
        output = subprocess.check_output(call).decode("utf-8")
    except subprocess.CalledProcessError as e:
        output = e.output.decode("utf-8")

    logging.debug(output)

    if UNSAT in output:
        return True

    else:
        return False

def convert_ng_file(ng_name, converted_ng_name,
                    max_deg=10,
                    max_lit_count=50,
                    nogoods_wanted=100,
                    minimal=False, 
                    sortby=["degree", "literal_count"], 
                    validate_files=None, 
                    reverse_sort=False,
                    validate_instance="none",
                    validate_instance_files=None):

    # sortby should be a list of the int attributes in the nogood:
    # lbd, ordering, degree, literal_count

    converted_lines = []
    amount_validated = 0
    amount_instance_validated = 0

    failed_to_validate = []
    prev_check = 0

    # just so that we dont check multiple times
    validate = validate_files is not None

    # read nogoods
    with open(ng_name, "r") as f:
        lines = f.readlines()


    total_nogoods = len(lines)
    logging.info("\ntotal lines in the no good file: {}\n".format(total_nogoods))
    if total_nogoods == 0:
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
    # this set will contain the string of nogoods. 
    #We will test if a nogood is unique with this
    nogood_strings = set()
    for line_num, line in enumerate(lines):
        # line is the raw text of the nogood, line num is the order it appears in the file
        ng = Nogood(line, line_num)

        # ignore nogoods of higher degree or literal count
        if max_deg >= 0 and ng.degree > max_deg:
            continue
        if max_lit_count > 0 and ng.literal_count > max_lit_count:
            continue

        t = time.time()
        ng.generalize()
        time_generalize += time.time() - t

        # if nogood has not been seen before, add it to list
        if ng.to_constraint() not in nogood_strings:
            nogoods.append(ng)
            nogood_strings.add(ng.to_constraint())

        if len(nogoods) >= nogoods_wanted:
            break

    if sortby is not None:
        nogoods.sort(key=lambda nogood : get_sort_value(nogood, sortby), reverse=reverse_sort)


    total_nogoods = len(nogoods)

    logging.info("Total nogoods after processing: {}".format(total_nogoods))

    if validate:
        logging.info("Starting validation...")
        percent_validated = 0.1

        for i, ng in enumerate(nogoods):

            # this part is the normal validation as patrick does it
            t = time.time()
            ng.validate_self(validate_files)
            time_validate += time.time() - t

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
                failed_to_validate.append(ng.to_rule())
                if "\'" in ng.to_rule():
                    prev_check += 1

            if float(i) / float(total_nogoods) >= percent_validated:
                logging.info("Validated {}% of total nogoods".format(percent_validated*100))
                percent_validated += 0.1


        print("failed vals {}, prev(\') in fails {}".format(len(failed_to_validate), prev_check))

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

            val_file_all = "validate_instance_all.lp"

            with open(val_file_all, "w") as f:
                for ng in nogoods:
                    f.write(str(ng.to_rule()))
                f.write("\nerror :- error(_).\n")
                f.write(":- not error.\n")
                f.write("#project error/0.\n")
                f.write("#show error/1.\n")

            t = time.time()
            validate_instance_all(validate_instance_files + [val_file_all])
            time_validate_instance += time.time() - t

        logging.info("Finishing instance validation")

    # if not validating(instance validating does not populate converted lines)
    # use all of them
    if converted_lines == []:
        converted_lines = nogoods

    # write generelized nogoods into a file
    lines_set = set()
    with open(converted_ng_name, "w") as f:
        for conv_line in converted_lines:
            line = conv_line.to_constraint()
            if line not in lines_set:
                f.write(str(line))
                lines_set.add(line)

    # write failed validations to a file
    with open("failed_to_validate.log", "w") as f:
        for l in failed_to_validate:
            f.write(str(l))

    logging.info("Finished converting!\n")

    if validate:
        logging.info("Validated {} of {} nogoods".format(amount_validated, total_nogoods))
    if validate_instance == "single":
        logging.info("Validated {} of {} nogoods within the instance".format(amount_instance_validated, total_nogoods))
    if validate_instance == "all":
        logging.info("Validation of all nogoods returned {}".format(all_val_result))

    logging.info("time to generelize: {}".format(time_generalize))
    if validate:
        logging.info("time to validate: {}".format(time_validate))
    if validate_instance == "single" or validate_instance == "all":
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

    output = subprocess.check_output(fd_call).decode("utf-8")
    #print(output)

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
                        "--lemma-out={}".format(ng_name),
                        "--lemma-out-dom=output", 
                        "--heuristic=domain", 
                        "--dom-mod=1,16",
                        "--lemma-out-max={}".format(args.nogoods_limit),
                        "--solve-limit={}".format(3*int(args.nogoods_limit)),
                        "--time-limit={}".format(args.max_extraction_time),
                        "--quiet=2",
                        "--stats",
                        "0"]

    # call clingo to extract nogoods
    t = time.time()
    call_clingo(file_names, NG_RECORDING_OPTIONS)
    time_extract = time.time() - t

    # convert the nogoods
    convert_ng_file(ng_name, converted_ng_name,
                    **config)

    logging.info("time to extract: {}".format(time_extract))

    #os.remove(ng_name)

    return converted_ng_name

def setup_logging(no_stream_output=False, logtofile=None):

    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(levelname)s: %(message)s")

    if logtofile is not None:
        fileHandler = logging.FileHandler(logtofile, mode="w")
        fileHandler.setFormatter(formatter)
        rootLogger.addHandler(fileHandler)

    if not no_stream_output:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(formatter)
        rootLogger.addHandler(consoleHandler)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('--files', metavar='f', nargs='+', help="Files to run clingo on not including instance")
    parser.add_argument('--instance', metavar='i', help="Instance file. If file has a .pddl extension it will be treated as a pddl instance.")

    parser.add_argument("--pddl-instance", help="pddl instance")
    parser.add_argument("--pddl-domain", help="pddl domain", default=None)
    parser.add_argument("--trans-name", help="name of the translated file")

    parser.add_argument("--sortby", nargs='+', help="attributes that will sort the nogood list. The order of the attributes is the sorting order. Choose from [degree, literal_count, ordering, lbd]. default: [degree, literal_count]", default=["degree", "literal_count"])
    parser.add_argument("--reverse-sort", action="store_true", help="Reverse the sort order.")
    parser.add_argument("--minimize", action="store_true", help="Minimize nogoods. Requires validation encoding.")

    parser.add_argument("--validate-files", nargs='+', help="file used to validate learned constraints. If no file is provided validation is not performed.", default=None)
    parser.add_argument("--validate-instance", default="none", choices=["none", "single", "all"], help="With this option the constraints will be validated with a search by counterexamples using the files and instances provided. Single validates every constraint by itself. all validates all constraints together")

    parser.add_argument("--nogoods-limit", help="Solving will only find up to this amount of nogoods for processing. Default = 100", default=100, type=int)

    parser.add_argument("--nogoods-wanted", help="Nogoods will be processed will stop after this amount. Default = 100", default=100, type=int)

    parser.add_argument("--max-deg", help="Processing will ignore nogoods with higher degree. Default = 10. A negative number means no limit.", default=10, type=int)
    parser.add_argument("--max-lit-count", help="Processing will ignore nogoods with higher literal count. Default = 50. 0 or a negative number means no limit.", default=50, type=int)

    parser.add_argument("--max-extraction-time", default=20, type=int, help="Time limit for nogood extraction in seconds. Default = 20")

    parser.add_argument("--logtofile", help="log to a file")

    parser.add_argument("--consume", action="store_true", help="consume the generated nogoods based on the given scaling.")
    parser.add_argument("--scaling", help="scaling of how many nogoods to use. format=start,factor,count. Default = 8,2,5", default="8,2,5")
    parser.add_argument("--consume-time-limit", type=int, help="time limit per call in seconds. Default=300", default=300)

    parser.add_argument("--no-stream-output", action="store_true", help="Supress output to the console")


    args = parser.parse_args()

    setup_logging(args.no_stream_output, args.logtofile)

    files = args.files

    config = {}

    config["validate_files"] = args.validate_files
    config["validate_instance"] = args.validate_instance
    config["sortby"] = args.sortby
    config["reverse_sort"] = args.reverse_sort
    config["minimal"] = args.minimize

    config["max_deg"] = args.max_deg
    config["max_lit_count"] = args.max_lit_count
    config["nogoods_wanted"] = args.nogoods_wanted

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


    # maybe pass the nogoods directly instead of file?
    converted_nogoods = produce_nogoods(files, args, config)

    if args.consume:
        times = consume_nogoods.run_tests(files, converted_nogoods, args.scaling, args.consume_time_limit)
        logging.info(times)

    if args.pddl_instance is not None:
        os.remove(trans_name)