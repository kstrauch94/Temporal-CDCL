import re
import clingo
from math import log

from collections.abc import MutableSequence

OPENTIME = "otime"

split_atom_re = r",\s+(?=[^()]*(?:\(|$))"

lbd_re = r"lbd = ([0-9]+)"

class Literal:

    def __init__(self, atom, sign):
        self.name = atom.name
        if atom.negative:
            self.name = f"-{self.name}"

        self.arguments = [str(arg) for arg in atom.arguments[:-1]]
        
        # -we add this variable to keep record of the unprocessed time
        # (the time changes when the literal is primed)
        # we may use this time in the calculation of the minimum time of the nogood
        self.non_processed_time = atom.arguments[-1].number
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
        
    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
        if self.name != other.name:
            return False

        for arg, oarg in zip(self.arguments, other.arguments):
            if arg != oarg:
                return False

        if self.time != other.time:
            return False

        if self.sign != other.sign:
            return False

        return True

    def __ne__(self, other: object) -> bool:
        return not self == other


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

    def str_no_sign(self):
        if self.sign == -1:
            return str(self)[3:]

        return str(self)

    def __repr__(self) -> str:
        return str(self)
        return f"GenLiteral({self.name},{self.arguments},{self.t},{self.sign})"

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
        if self.name != other.name:
            return False

        for arg, oarg in zip(self.arguments, other.arguments):
            if arg != oarg:
                return False

        if self.t != other.t:
            return False

        if self.sign != other.sign:
            return False

        return True

    def __ne__(self, other: object) -> bool:
        return not self == other


class Nogood:

    def __init__(self, ng_str, order=None, degreem1=False):
        
        self.original_str = ng_str
        self.order = order
        self.degreem1 = degreem1

        self.literals = []
        self.domain_literals = []

        self.gen_literals = []
        self.gen_domain_literals = []

        self.lbd = None

        self.degree = None
        self.max_time = None
        self.min_time = None

        self.min_step_time = None
        self.max_step_time = None

        self.horn_pos = 0
        self.horn_neg = 0

        self.subsumes = 0

        self.process_lbd(ng_str)

        self.process_literals(ng_str)

        self.process_time()

        self.is_horn_clause()

        self.generalized = None

        # this is exclusively for the incremental mode
        # set this to true if the nogood has been added to the program
        self.grounded = False



    @property
    def score(self):
        return self.lbd + log(self.size, 50) + log(self.degree+1, 5)

    @property
    def horn_any(self):
        return int(self.horn_pos or self.horn_neg)

    @property
    def r_horn_pos(self):
        return -self.horn_pos

    @property
    def r_horn_neg(self):
        return -self.horn_neg

    @property
    def r_horn_any(self):
        return -self.horn_any

    @property
    def size(self):
        return len(self.literals)

    @property
    def subsumes_r(self):
        #useful to not specify reverse sort
        return -self.subsumes

    def is_horn_clause(self):
        pos = 0
        neg = 0

        for val in self.literals:
            if val.sign == 1:
                pos += 1
            elif val.sign == -1:
                neg += 1
        
        self.horn_pos = int(pos == 1)
        self.horn_neg = int(neg == 1)

            


    def process_lbd(self, nogood_str):
        try:
            self.lbd = int(re.search(lbd_re, nogood_str).group(1))
        except AttributeError as _:
            print(f"ERROR IN LBD: {nogood_str}")
            raise AttributeError from _


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
        processed_times = []
        for lit in self.literals:
            regular_times.append(lit.non_processed_time)
            processed_times.append(lit.time)

        step_times = []
        for lit in self.domain_literals:
            step_times.append(lit.non_processed_time)

        self.max_time = max(regular_times + step_times)

        # minimum between the lowest point in the step atom -1 (since step atom only covers the higher timepoint of the transition)
        # and the lowest timepoint if the literals when no prime literals are present

        # full min is the actual minimum timepoint, not the minimum time of the rule(e.g min of on'(5), otime(6) = 5 but full min = 4 (due to on'(5) = on(4) ) )

        if len(step_times) == 0:
            self.min_time = min(regular_times)
            self.full_min = min(processed_times)
        else:
            # these 2 are just for information when printing the nogood
            self.min_step_time = min(step_times)
            self.max_step_time = max(step_times)


            self.min_time = min(min(regular_times), min(step_times)-1)
            self.full_min = min(min(processed_times), min(step_times)-1)

        self.degree = self.max_time - self.min_time


    def _generalize(self, literals, t):

        if len(literals) == 0:
            return []

        gen_literals = []

        for lit in literals:
            time = lit.time

            new_lit = GenLiteral(lit.name, lit.arguments, t=f"{t}-{self.max_time - time}", sign=lit.sign)

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

        if t == "t":
            for timepoint in range(0, self.degree+1):
                self.gen_domain_literals += [f"{OPENTIME}({t}-{timepoint})"]

        # make sure lowest timepoint possible is 0
        if self.degreem1:
            self.gen_domain_literals += [f"{t}-{self.degree} >= 0"]
        else:
            self.gen_domain_literals += [f"{t}-{self.degree} > 0"]

        self.gen_domain_literals += [f"{t}-{self.full_min} >= 0"]

        self.generalized = t

    def properties_str(self):
        return f"% lbd = {self.lbd} , order = {self.order} , max,min = {self.max_time},{self.min_time}  , score = {self.score}  , subsumes = {self.subsumes}, min,max steps = {self.min_step_time},{self.max_step_time}"

    def to_constraint(self):

        lits = [str(a) for a in self.literals]
        lits.extend([str(a) for a in self.domain_literals])

        return f":- {', '.join(lits)}. {self.properties_str()}"

    def to_general_constraint(self):
        if self.generalized is not None:
            lits = [str(a) for a in self.gen_literals]
            lits.extend([str(a) for a in self.gen_domain_literals])

            return f":- {', '.join(lits)}. {self.properties_str()}"


        return self.to_constraint()

    def issubset(self, other_ng):
        return set(self.all_literals).issubset(set(other_ng.all_literals))

    @property
    def all_literals(self):
        return self.gen_literals + self.gen_domain_literals

    def delete_gen_lit(self, lit):
        self.gen_literals.remove(lit)

    def __len__(self):
        return len(self.gen_literals)

    def __str__(self) -> str:
        if self.generalized is not None:
            return self.to_general_constraint()

        return self.to_constraint()

class NogoodList(MutableSequence):
    """A more or less complete user-defined wrapper around list objects."""

    # We need this ng_list so that we can replace the list while keeping the pointer
    # for the list in the arguments intact!

    def __init__(self, initlist=None):
        self.data = []
        if initlist is not None:
            # XXX should this accept an arbitrary sequence?
            if type(initlist) == type(self.data):
                self.data[:] = initlist
            elif isinstance(initlist, NogoodList):
                self.data[:] = initlist.data[:]
            else:
                self.data = list(initlist)

    def replace(self, data):
         self.data = data

    def __repr__(self):
        return repr(self.data)

    def __lt__(self, other):
        return self.data < self.__cast(other)

    def __le__(self, other):
        return self.data <= self.__cast(other)

    def __eq__(self, other):
        return self.data == self.__cast(other)

    def __gt__(self, other):
        return self.data > self.__cast(other)

    def __ge__(self, other):
        return self.data >= self.__cast(other)

    def __cast(self, other):
        return other.data if isinstance(other, NogoodList) else other

    def __contains__(self, item):
        return item in self.data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.__class__(self.data[i])
        else:
            return self.data[i]

    def __setitem__(self, i, item):
        self.data[i] = item

    def __delitem__(self, i):
        del self.data[i]

    def __add__(self, other):
        if isinstance(other, NogoodList):
            return self.__class__(self.data + other.data)
        elif isinstance(other, type(self.data)):
            return self.__class__(self.data + other)
        return self.__class__(self.data + list(other))

    def __radd__(self, other):
        if isinstance(other, NogoodList):
            return self.__class__(other.data + self.data)
        elif isinstance(other, type(self.data)):
            return self.__class__(other + self.data)
        return self.__class__(list(other) + self.data)

    def __iadd__(self, other):
        if isinstance(other, NogoodList):
            self.data += other.data
        elif isinstance(other, type(self.data)):
            self.data += other
        else:
            self.data += list(other)
        return self

    def __mul__(self, n):
        return self.__class__(self.data * n)

    __rmul__ = __mul__

    def __imul__(self, n):
        self.data *= n
        return self

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["data"] = self.__dict__["data"][:]
        return inst

    def append(self, item):
        self.data.append(item)

    def insert(self, i, item):
        self.data.insert(i, item)

    def pop(self, i=-1):
        return self.data.pop(i)

    def remove(self, item):
        self.data.remove(item)

    def clear(self):
        self.data.clear()

    def copy(self):
        return self.__class__(self)

    def count(self, item):
        return self.data.count(item)

    def index(self, item, *args):
        return self.data.index(item, *args)

    def reverse(self):
        self.data.reverse()

    def sort(self, /, *args, **kwds):
        self.data.sort(*args, **kwds)

    def extend(self, other):
        if isinstance(other, NogoodList):
            self.data.extend(other.data)
        else:
            self.data.extend(other)
