#script (python) 

import clingo

def get_assumptions(prg):
    truth_dict = {"true": True,
                  "false": False}

    assumptions = []

    for x in prg.symbolic_atoms:
            if x.is_fact:
                atom = x.symbol
                if atom.name == "assumption":
                    truth_val = truth_dict[atom.arguments[1].name]
                        
                    assumptions.append([atom.arguments[0], truth_val])
    
    return assumptions

def main(prg):

    ret = None

    # ground program
    prg.ground([("base", [])])

    assumptions = get_assumptions(prg)
    ret = prg.solve(assumptions=assumptions)
#end.
