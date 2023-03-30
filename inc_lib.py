import imp
from produce import collect_nogoods, process_ng_list
from Nogood import NogoodList
import clingo
import os
import sys
from util import util

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
               converted_ng_name="nogoods.lp",
               options=None):

        self.ng_name = ng_name
        self.converted_ng_name = converted_ng_name

        
        self.max_nogoods = None
        self.max_size = None
        self.max_degree = None
        self.max_lbd = None

        self.base_benchmark_mode = None
        self.no_subsumption = None
        self.sort_by = None
        # nogoods wanted per step!
        self.nogoods_wanted = None

        self.set_option("max_nogoods", options, "max_nogoods", 1000)
        self.set_option("max_size", options, "max_size", 50)
        self.set_option("max_degree", options, "max_degree", 8)
        self.set_option("max_lbd", options, "max_lbd", None)
        self.set_option("base_benchmark_mode", options, "base_benchmark_mode", False)
        self.set_option("no_subsumption", options, "no_subsumption", True)
        self.set_option("sort_by", options, "sort_by", ["size"])
        self.set_option("nogoods_wanted", options, "nogoods_wanted", None)

        self.degreem1 = False

        self.supress_collection_output = True

        print(self.max_degree, self.max_lbd, self.max_nogoods, self.max_size, self.sort_by)

        self.total_nogoods_added = 0

        self.logger = logging.getLogger(
            self.__module__ + '.' + self.__class__.__name__)

        self.ng_list = NogoodList()

    def set_option(self, var, options, name, default):
        if options is None or name not in options:
            setattr(self, var, default)
        else:
            setattr(self, var, options[name])

    def prepare(self, prg):
        self.get_assumptions_and_domains(prg)
        self.add_domains(prg)

    def get_assumptions_and_domains(self, prg):
        #prg has to ground base before calling this function

        truth_dict = {"true": True,
                      "false": False}


        self.init_assumptions = []
        self.goal_assumptions = []

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

                if atom.name.startswith(DOMAIN_PREFIX):
                    self.parse_domain(atom)
                        

    def add_domains(self, prg):

        for domain in self.domains:
            prev_atom_rules = PREV_RULES.format(domain=domain["domain"],
                                                prev_atom=domain["prev"],
                                                atom=domain["atom"],
                                                opentime=OPENTIME)

            self.logger.debug(prev_atom_rules)
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

        self.logger.debug(atom_prev)
        self.logger.debug(atom)

        self.domains.append({"domain": domain_atom, 
                "prev": atom_prev,
                "atom": atom})

        return 1

    def assumptions_for_step(self, step):

        goal = []

        for name, args, truth_val in self.goal_assumptions:
            atom_func = clingo.Function(name, args+[clingo.Number(step)])
            goal.append([atom_func, truth_val])

        other_assumptions = []
        if step > 0:
            for i in range(1, step+1):
                otime_func = clingo.Function(OPENTIME, [clingo.Number(i)])
                other_assumptions.append([otime_func, True])

        return other_assumptions + self.init_assumptions + goal  

    def convert_nogoods(self):
        # this function sanitizes the raw nogood file by deleting the last nogood logged if its unfinished
        # it also does the actual call to the generalizer and writes the new converted nogoods file


        if len(self.ng_list) >= self.max_nogoods:
            return

        self.preprocess_ng_file()

        # collect nogoods
        with open(self.ng_name, "r") as _f:
            collect_nogoods(_f.readlines(), self.ng_list, process_limit=None, gen_t="t", 
                            max_degree=self.max_degree, max_size=self.max_size, max_lbd=self.max_lbd, 
                            no_subsumption=self.no_subsumption, degreem1=self.degreem1, 
                            supress_output=self.supress_collection_output)

        process_ng_list(ng_list=self.ng_list, nogoods_wanted=None, sort_by=self.sort_by, sort_reversed=False, validator=None)

        self.logger.debug("Length of current nogood list: %i", len(self.ng_list))
        # process nogoods
        
        self.postprocess_ng_file()


    def preprocess_ng_file(self):
        """
        # if there are any weird null characters
        # in the middle as a result of not properly finishing the last
        # writing action in the previous solve call then delete the null characters
        # ----
        # handling the unfisnihed nogood is done in the actual generalizer
        """
        with open(self.ng_name, "r") as f:
            no_null_chars = f.read().replace("\0", "")

        with open(self.ng_name, "w") as f:
            f.write(no_null_chars)


    def postprocess_ng_file(self):
        with open(self.ng_name, "r") as f:
            lines = f.readlines()

        if len(lines) == 0:
            return
        # check if the last line was unfinished. If so, 
        # add it to the ng file
        if "lbd = " not in lines[-1]:
            # if the last line doesnt have the lbd then it is unfinished and  we have
            # to continue it for later
            lastline = lines[-1]

            with open(self.ng_name, "w") as f:
                f.write(lastline)

        # else we just delete the contents
        # we do this so that previous nogoods are not used anymore
        else:
            open(self.ng_name, "w").close()


    def add_nogoods(self, prg, step):
        """
        this function returns the name of the parts that were added to the program that have to be grounded
        """
        # this is a safety net, if we are in step < 1 we have not solved yet
        # so there is no nogood file
        if step < 1:
            return []

        self.convert_nogoods()

        if self.base_benchmark_mode:
            # return here after having converted the nogods
            # so that it doesnt add any new programs or extends the step program
            self.logger.info("noogods to add: 0")
            self.logger.info("total nogoods added: {}".format(self.total_nogoods_added))
            return []
        #print(self.ng_list)
        nogoods = []
        added = 0
        for ng in self.ng_list:
            if self.nogoods_wanted is not None and added >= self.nogoods_wanted:
                break

            if not ng.grounded:
                ng.grounded = True
                added += 1
                nogoods.append(ng.to_general_constraint())

        # if there are no nogoods to ground, then just return
        if len(nogoods) == 0:
            self.logger.info("noogods to add: 0")
            self.logger.info("total nogoods added: {}".format(self.total_nogoods_added))
            return []

        # add nogoods to the exact max amount
        if len(nogoods) + self.total_nogoods_added >= self.max_nogoods:
            add_amount = self.max_nogoods - self.total_nogoods_added
            nogoods = nogoods[:add_amount]

        parts = []

        # add new nogoods to a program to be grounded to all previous steps
        prog_name = "step-{}".format(step)
        prg.add(prog_name, ["t"], "\n".join(nogoods))
        for s in range(1, step):
            parts.append((prog_name, [clingo.Number(s)]))

        # new and old nogoods are added to a program to be grounded 
        # to the current step
        prg.add("step", ["t"], " ".join(nogoods))


        self.total_nogoods_added += len(nogoods)
        util.Count.add("Nogoods added", len(nogoods))

        self.logger.info("noogods to add: {}".format(len(nogoods)))
        self.logger.info("total nogoods added: {}".format(self.total_nogoods_added))

        return parts

    def add_learned_rules(self, prg, step):
        if os.path.isfile(self.ng_name):
            self.logger.debug("adding nogoods")
            
            parts = self.add_nogoods(prg, step)

            self.logger.debug(f"Time used for collection {util.Timer.timers['collect']}")
            self.logger.debug(f"Time used for subsumption {util.Timer.timers['subsumption']}")


            return parts


        # if no nogoods were found
        return []

    def print_stats(self):

        for name, count in util.Count.counts.items():
            print(f"{name:24}  :   {count}")

        for name, time_taken in sorted(util.Timer.timers.items()):
            print(f"{name:19}  :   {time_taken:.3f}")