from produce_nogoods import convert_ng_file
import clingo
import os
import sys
import inc_config_file

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(levelname)s:%(name)s: %(message)s")
consoleHandler.setFormatter(formatter)

logger.addHandler(consoleHandler)
logger.propagate = False

OPENTIME="otime"

DOMAIN_PREFIX = "domain_"

PREV_RULES = """
{{ {prev_atom} }} :- {domain}.
:- {prev_atom}, not {atom}, {opentime}(t).
:- not {prev_atom}, {atom}, {opentime}(t).
"""

class Handler:

    def __init__(self, ng_name="ng_temp.lp",
               converted_ng_name="conv_ng.lp", 
               options=inc_config_file.OPTIONS,
               max_nogoods_to_add=inc_config_file.MAX_NOGOODS_TO_ADD):


        self.ng_name = ng_name
        self.converted_ng_name = converted_ng_name
        self.config = options

        self._last_nogood_amount = 0

        # this flag says if we should keep generalizing nogoods
        # basically, if we have reached the max then do nothing
        self._no_conversion = max_nogoods_to_add <= 0

        self.total_nogoods_added = 0
        self.max_nogoods_to_add = max_nogoods_to_add

        self.total_conversion_time = 0

        self.logger = logging.getLogger(
            self.__module__ + '.' + self.__class__.__name__)

    def prepare(self, prg):
        self.get_assumptions_and_domains(prg)
        self.add_domains(prg)

    def get_assumptions_and_domains(self, prg):
        #prg has to ground base before calling this function

        truth_dict = {"true": True,
                      "false": False}


        self.init_assumptions = []
        self.goal_assumptions = []
        self.other_assumptions = []

        self.domains = []
        self.domain_names = set()

        for x in prg.symbolic_atoms:
                if x.is_fact:
                    atom = x.symbol
                    if "assumption" in atom.name:
                        truth_val = truth_dict[atom.arguments[1].name]
                    
                        if atom.name == "assumption_init":
                            self.init_assumptions.append([atom.arguments[0], truth_val])
            
                        elif atom.name == "assumption_goal":
                            inner_atom = atom.arguments[0]
                            name = inner_atom.name
                            args = inner_atom.arguments[:]
                            self.goal_assumptions.append([name, args, truth_val])
                        else:
                            self.other_assumptions.append([atom.arguments[0], truth_val])

                    if atom.name.startswith(DOMAIN_PREFIX):
                        self.parse_domain(atom)
                        

    def add_domains(self, prg):

        for domain in self.domains:
            prev_atom_rules = PREV_RULES.format(domain=domain["domain"],
                                                prev_atom=domain["prev"],
                                                atom=domain["atom"],
                                                opentime=OPENTIME)

            self.logger.info(prev_atom_rules)
            prg.add("step", ["t"], prev_atom_rules)

        prg.add("step", ["t"], "{ otime(t) }.")

    def parse_domain(self, domain):

        if domain.name in self.domain_names:
            return None

        self.domain_names.add(domain.name)

        arg_len = len(domain.arguments)
        if arg_len > 0:
            domain_atom = domain.name+"("+",".join(["X"+str(i) for i in range(arg_len)]) + ")"
        else:
            domain_atom = domain.name+"()"

        atom_no_time = domain_atom[len(DOMAIN_PREFIX):]

        if arg_len > 0:
            atom_prev = atom_no_time.replace("(", "'(").replace(")",",t)") 
            atom = atom_no_time.replace(")",",t-1)")
        else:
            atom_prev = atom_no_time.replace("(", "'(").replace(")","t)") 
            atom = atom_no_time.replace(")","t-1)")

            # we take out the () because its not important for processing anymore
            domain_atom = domain.name

        self.logger.info(atom_prev)
        self.logger.info(atom)

        self.domains.append({"domain": domain_atom, 
                "prev": atom_prev,
                "atom": atom})

        return 1

    def assumptions_for_step(self, step):

        goal = []

        for name, args, truth_val in self.goal_assumptions:
            atom_func = clingo.Function(name, args+[clingo.Number(step)])
            goal.append([atom_func, truth_val])

        if step > 0:
            otime_func = clingo.Function(OPENTIME, [clingo.Number(step)])
            self.other_assumptions.append([otime_func, True])

        return self.other_assumptions + self.init_assumptions + goal  

    def convert_nogoods(self):
        # this function sanitizes the raw nogood file by deleting the last nogood logged if its unfinished
        # it also does the actual call to the generalizer and writes the new converted nogoods file

        self.preprocess_ng_file()

        stats, _, __ = convert_ng_file(self.ng_name, self.converted_ng_name,
                        **self.config)

        # stats is only none when no nogoods were logged
        # or when the nogood file doesn't exist
        if stats is None:
            return 0

        # this is the amount of VALID raw nogoods
        total_raw_nogoods = stats["total_raw_nogoods"].value

        if "repeats" in stats:
            total_converted_nogoods = stats["total_nogoods_generalized"].value
            repeats = stats["repeats"].value

            self.logger.info("raw_nogoods in file: {}".format(total_raw_nogoods))
            self.logger.info("total converted nogoods: {}".format(total_converted_nogoods))
            self.logger.info("total repeats: {}".format(repeats))
            self.logger.info("repeats + converted nogoods: {}".format(repeats + total_converted_nogoods))
            self.logger.info(stats["time_conversion_jobs"].message)
            self.total_conversion_time += stats["time_conversion_jobs"].value
        else:
            total_converted_nogoods = 0
            repeats = 0

        self.logger.info("total time spent on conversion: {}".format(self.total_conversion_time))
        self.postprocess_ng_file(total_raw_nogoods)

        return total_converted_nogoods

    def preprocess_ng_file(self):
        """
        # if there are any weird null characters
        # in the middle as a result of not properly finishing the last
        # writing action in the previous solve call then delete the null characters
        # ----
        # handling the unfisnihed nogood is done in the actual generalizer
        """
        self.logger.info("POST")

        with open(self.ng_name, "r") as f:
            no_null_chars = f.read().replace("\0", "")

        with open(self.ng_name, "w") as f:
            f.write(no_null_chars)


    def postprocess_ng_file(self, total_raw_nogoods):
        self.logger.info("POST")

        with open(self.ng_name, "r") as f:
            lines = f.readlines()

        # check if the last line was unfinished. If so, 
        # add it to the ng file
        if len(lines) == total_raw_nogoods + 1:
            # if the total lines is 1 less than the amount of "nogoods"
            # in the file
            lastline = lines[-1]

            with open(self.ng_name, "w") as f:
                f.write(lastline)

        # else we just delete the contents
        # we do this so that previous nogoods are not used anymore
        else:
            open(self.ng_name, "w").close()


    def add_nogoods(self, prg, step):
        # this is a safety net, if we are in step 1 we have not solved yet
        # so there is no nogood file
        # we return the name of the parts that were added to the program that have to be grounded
        if step == 1:
            return []

        parts = []

        # here, we read the new converted nogood file
        with open(self.converted_ng_name, "r") as f:
            total_nogoods = f.readlines()

            if self.total_nogoods_added + len(total_nogoods) >= self.max_nogoods_to_add:
                dif = self.max_nogoods_to_add - self.total_nogoods_added
                nogoods = total_nogoods[:dif]

                self._no_conversion = True
            else:
                nogoods = total_nogoods
                
        #for n in nogoods:
        #    print(n)

        self.logger.info("noogods to add: {}".format(len(nogoods)))

        # add new nogoods to a program to be grounded to all previous steps
        prog_name = "step-{}".format(step)
        prg.add(prog_name, ["t"], "\n".join(nogoods))
        for s in range(1, step):
            parts.append((prog_name, [s]))

        # new and old nogoods are added to a program to be grounded 
        # to the current step
        prg.add("step", ["t"], " ".join(nogoods))


        self.total_nogoods_added += len(nogoods)

        self.logger.info("total nogoods added: {}".format(self.total_nogoods_added))

        return parts

    def add_learned_rules(self, prg, step):
        # if we reached the max amount of nogoods we want
        if self._no_conversion:
            return []
        if os.path.isfile(self.ng_name) and self.convert_nogoods() > 0:
            self.logger.info("adding nogoods")
            return self.add_nogoods(prg, step)

        # if no nogoods were found
        return []