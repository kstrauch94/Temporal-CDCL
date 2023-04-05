import sys

import clingo
import inc_lib

def get(val, default):
    return val if val != None else default

class Application:

    def __init__(self):
        self.version = "1.0"

        self.options = {"max_size": 50,
                        "max_degree": 10,
                        "max_lbd": None,
                        "horn_filter": None,
                        "no_subsumption": False}
        
        self.__base_benchmark_mode = clingo.Flag(False)
        self.__no_subsumption = clingo.Flag(False)
        self.__sort_by = None
        self.__max_nogoods = None
        self.__degreem1 = clingo.Flag(False)
        self.__nogoods_per_step = None

    def register_options(self, options):
        """
        See clingo.clingo_main().
        """

        group = "Generalization Options"

        options.add(group, "max-size", """Max nogood size""", lambda val: self.__parse_int_option("max_size", val))
        options.add(group, "max-degree", """Max degree """, lambda val: self.__parse_int_option("max_degree", val))
        options.add(group, "max-lbd", """Max lbd""", lambda val: self.__parse_int_option("max_lbd", val))
        options.add(group, "max-nogoods", """Max nogoods to use""", self.__parse_max_nogoods)
        options.add(group, "nogoods-per-step", """Max Noogods per step""", self.__parse_nogoods_per_step)

        options.add(group, "horn-filter", """Filter nogoods by horn clause type""", self.__parse_horn_filter)

        options.add_flag(group, "base-benchmark-mode", """Learn and generalize but add no nogoods to the solver""", self.__base_benchmark_mode)

        options.add_flag(group, "no-subsumption", """Do not subsume nogoods""", self.__no_subsumption)

        options.add(group, "sort-by", """Sort nogoods by a given criterion""", self.__parse_sort_by)

        options.add_flag(group, "degreem1", """Use nogoods on step 1 if possible""", self.__degreem1)
        
        # add options to parse max size, max lbd, max degree, horn filter and nogoods wanted

    def __parse_int_option(self, name, value):
        self.options[name] = int(value)

        return True

    def __parse_max_nogoods(self, value):
        self.__max_nogoods = int(value)

        return True
    
    def __parse_nogoods_per_step(self, value):
        self.__nogoods_per_step = int(value)

        return True
    
    def __parse_horn_filter(self, value):

        if value not in ["pos", "neg", "any"]:
            print(f"error: invalid value for horn-filter: {value}. Expected 'pos', 'neg', or 'any'.")
            return False
        
        self.options["horn_filter"] = value

        return True

    def __parse_sort_by(self, value):
        self.__sort_by = value.split(",")

        return True

    def main(self, prg, files):
        for name in files:
            prg.load(name)

        self.options["no_subsumption"] = self.__no_subsumption.flag
        handler = inc_lib.Handler(collect_options=self.options,
                                  base_bechmark_mode=self.__base_benchmark_mode.flag,
                                  sort_by=self.__sort_by,
                                  max_nogoods=self.__max_nogoods,
                                  nogoods_per_step=self.__nogoods_per_step,
                                  degreem1=self.__degreem1)

        imin   = get(prg.get_const("imin"), clingo.Number(0))
        imax   = prg.get_const("imax")
        istop  = get(prg.get_const("istop"), clingo.String("SAT"))
        imax = clingo.Number(150)
        step, ret = 0, None
        while ((imax is None or step < imax.number) and
            (step == 0 or step < imin.number or (
                (istop.string == "SAT"     and not ret.satisfiable) or
                (istop.string == "UNSAT"   and not ret.unsatisfiable) or 
                (istop.string == "UNKNOWN" and not ret.unknown)))):
            parts = []
            #parts.append(("check", [step]))
            if step > 0:
                #prg.release_external(clingo.Function("query", [step-1]))
                parts.append(("step", [clingo.Number(step)]))
                prg.cleanup()
            else:
                parts.append(("base", []))

            if step > 0 and step % 5 == 0:
                parts += handler.add_learned_rules(prg, step)

            prg.ground(parts)
            if step == 0:
                handler.prepare(prg)
            #prg.assign_external(clingo.Function("query", [step]), True)
            if step % 5 == 0:
                print("solving for step ", step)
                ret, step = prg.solve(assumptions=handler.assumptions_for_step(step)), step+1
            else:
                step += 1


def main():
	sys.exit(int(clingo.clingo_main(Application(), sys.argv[1:])))


if __name__ == "__main__":
	main()

