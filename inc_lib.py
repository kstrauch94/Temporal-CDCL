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
               collect_options=None,
               base_bechmark_mode = None,
               sort_by = ["size"],
               max_nogoods_to_keep = None,
               max_nogoods_to_add = None,
               nogoods_per_step = None,
               degreem1 = False):

        self.ng_name = ng_name
        self.converted_ng_name = converted_ng_name

        self.collect_options = collect_options
        self.base_benchmark_mode = base_bechmark_mode
        self.sort_by = sort_by
        # nogoods wanted per step!
        self.max_nogoods_to_keep = max_nogoods_to_keep
        self.max_nogoods_to_add = max_nogoods_to_add
        self.nogoods_per_step = nogoods_per_step

        self.degreem1 = degreem1

        self.supress_collection_output = True

        self.total_nogoods_added = 0

        self.logger = logging.getLogger(
            self.__module__ + '.' + self.__class__.__name__)

        self.ng_list = NogoodList()

        print(collect_options)

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
        """calls the generalizer"""

        if self.max_nogoods_to_keep is not None and len(self.ng_list) >= self.max_nogoods_to_keep:
            return
        
        if self.max_nogoods_to_add is not None and self.total_nogoods_added >= self.max_nogoods_to_add:
            return

        self.preprocess_ng_file()

        # collect nogoods
        with open(self.ng_name, "r") as _f:
            collect_nogoods(_f.readlines(), self.ng_list, process_limit=None, gen_t="t",
                            supress_output=self.supress_collection_output,
                            **self.collect_options)

        process_ng_list(ng_list=self.ng_list, nogoods_wanted=None, sort_by=self.sort_by, sort_reversed=False, validator=None)

        self.ng_list = self.ng_list[:self.max_nogoods_to_keep]

        self.logger.info("Length of current nogood list: %i", len(self.ng_list))
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


    def add_nogoods(self, prg, step, extra_name="N"):
        """
        this function returns the name of the parts that were added to the program that have to be grounded
        """
        # this is a safety net, if we are in step < 1 we have not solved yet
        # so there is no nogood file
        if step < 1:
            return []

        # if we have already added the maximum amount just return
        if self.max_nogoods_to_add is not None and self.total_nogoods_added >= self.max_nogoods_to_add:
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
            if self.nogoods_per_step is not None and added >= self.nogoods_per_step:
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
        if self.max_nogoods_to_add is not None and len(nogoods) + self.total_nogoods_added >= self.max_nogoods_to_add:
            add_amount = self.max_nogoods_to_add - self.total_nogoods_added
            nogoods = nogoods[:add_amount]

        parts = []

        # add new nogoods to a program to be grounded to all previous steps
        prog_name = f"step-{step}-{extra_name}"
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

    def add_learned_rules(self, prg, step, extra_name=""):
        if os.path.isfile(self.ng_name):
            self.logger.debug("adding nogoods")
            
            parts = self.add_nogoods(prg, step, extra_name)

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