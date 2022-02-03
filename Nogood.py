import re
import clingo

OPENTIME = "otime"

split_atom_re = r",\s+(?=[^()]*(?:\(|$))"

lbd_re = r"lbd = ([0-9]+)"

class Literal:

    def __init__(self, atom, sign):
        self.name = atom.name

        self.arguments = [str(arg) for arg in atom.arguments[:-1]]

        self.time = atom.arguments[-1].number

        if sign not in [1,-1]:
            raise ValueError(f"Invalid sign given {sign}")

        self.sign = sign

        self.process_prime()

    def process_prime(self):

        if self.name.endswith("'"):
            self.name = self.name[:-1]

            self.time -= 1

    def __str__(self):

        if len(self.arguments) > 0:
            s = f"{self.name}({','.join(self.arguments)},{self.time})"
        else:
            s = f"{self.name}({self.time})"

        if self.sign == 1:
            return s
        elif self.sign == -1:
            return f"not {s}"

class GenLiteral:

    def __init__(self, name, arguments, t, sign):

        self.name = name

        self.arguments = arguments

        self.t = t

        self.sign = sign

    def __str__(self):

        if len(self.arguments) > 0:
            s = f"{self.name}({','.join(self.arguments)},{self.t})"
        else:
            s = f"{self.name}({self.t})"

        if self.sign == 1:
            return s
        elif self.sign == -1:
            return f"not {s}"

class Nogood:

    def __init__(self, ng_str, order=None):

        self.order = order

        self.literals = []
        self.domain_literals = []

        self.gen_literals = []
        self.gen_domain_literals = []

        self.lbd = None

        self.degree = None
        self.max_time = None
        self.min_time = None

        self.process_lbd(ng_str)

        self.process_literals(ng_str)

        self.process_time()

        self.generalized = None

    def process_lbd(self, nogood_str):
        try:
            self.lbd = int(re.search(lbd_re, nogood_str).group(1))
        except AttributeError as e:
            print("ERROR IN LBD: {}".format(nogood_str))
            raise AttributeError


    def process_literals(self, nogood_str):
        # this takes the raw nogood string and splits the atoms
        # into singular ones
        pre_literals = nogood_str.split(".")[0].replace(":-", "").strip()

        pre_literals = re.split(split_atom_re, pre_literals)

        for lit in pre_literals:
            if "not " in lit:
                self.literals.append(Literal(clingo.parse_term(lit.replace("not ", "")), sign=-1))

            elif "{}(".format(OPENTIME) in lit:
                self.domain_literals.append(Literal(clingo.parse_term(lit), sign=1))

            else:
                self.literals.append(Literal(clingo.parse_term(lit), sign=1))

        #print(", ".join([str(a) for a in self.pos_literals + self.neg_literals + self.domain_literals]))


    def process_time(self):

        # matches with regular literals(prime literals still present)
        regular_times = []
        for lit in self.literals:
            regular_times.append(lit.time)

        step_times = []
        for lit in self.domain_literals:
            step_times.append(lit.time)

        self.max_time = max(regular_times + step_times)

        # minimum between the lowest point in the step atom -1 (since step atom only covers the higher timepoint of the transition)
        # and the lowest timepoint if the literals when no prime literals are present

        if len(step_times) == 0:
            self.min_time = min(regular_times)
        else:
            # here, it is important to note that the lowest timepoint MAY contain prime literals. This is why we add the minimum T > 0
            # to the domain literals later on. We could also, just take the minimum point as the minimum of the transformed literals
            # but then, the degree and dif_to_min would be different
            self.min_time = min(min(step_times)-1, min(regular_times))

        self.degree = self.max_time - self.min_time


    def _generalize(self, literals, t):

        if len(literals) == 0:
            return []

        gen_literals = []

        for lit in literals:
            time = lit.time

            new_lit = GenLiteral(lit.name, lit.arguments, t=f"{t}-{self.max_time - time}", sign=lit.sign)
            #re.sub(r"{t}(\)*){end}".format(t=time, end=END_STR), r"{t}-{dif}\1{end}".format(t=self.t, dif=self.max_time - time, end=END_STR), lit + END_STR)

            gen_literals.append(new_lit)

        return gen_literals

    def generalize(self, t="T"):

        self.gen_literals = self._generalize(self.literals, t)

        #self.gen_domain_literals = self._generalize(self.domain_literals, t)

        # otime is really only needed to keep track of the timepoints of the rules
        # at conflict resolution time. So, no need to write them again.
        # instead, if we use one-shot solving we add time(T) and time(T-degre)
        # so that the maximum and minimum times actually exist.

        #self.gen_domain_literals = self._generalize(self.domain_literals, t)

        if t == "T":
            self.gen_domain_literals += ["time(T)", f"time(T-{self.degree})"]

        if self.min_time > 0:
            # minimum timepoint in the rule is 1 but only if
            # in the original rule the minimum was NOT 0
            self.gen_domain_literals += ["{}-{} > 0".format(t, self.degree)]
        else:
            # we have to make sure that the minimum value is still 0
            self.gen_domain_literals += ["{}-{} >= 0".format(t, self.degree)]

        self.generalized = t

    def to_constraint(self):

        lits = [str(a) for a in self.literals]
        lits.extend([str(a) for a in self.domain_literals])

        return f":- {', '.join(lits)}. % lbd = {self.lbd} , order = {self.order} , max,min = {self.max_time},{self.min_time}"

    def to_general_constraint(self):
        if self.generalized is not None:
            lits = [str(a) for a in self.gen_literals]
            lits.extend([str(a) for a in self.gen_domain_literals])

            return f":- {', '.join(lits)}. % lbd = {self.lbd} , order = {self.order} , max,min = {self.max_time},{self.min_time}"


        return self.to_constraint()

    def issubset(self, other_ng):
        return set(self.all_literals).issubset(set(other_ng.all_literals))

    @property
    def all_literals(self):
        return self.gen_literals + self.gen_domain_literals

    def __len__(self):
        return len(self.gen_literals)
