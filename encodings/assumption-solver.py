#script (python) 

import clingo

def get_assumptions(prg):

    assumptions = []

    for x in prg.symbolic_atoms:
            if x.is_fact:
                atom = x.symbol
                if atom.name == "assumption":
                    if atom.arguments[1].name == "true":
                        truth_val = True
                    elif atom.arguments[1].name == "false":
                        truth_val = False
                        
                    assumptions.append([atom.arguments[0], truth_val])
    
    return assumptions

def main(prg):

    ret = None

    # ground program
    prg.ground([("base", [])])

    assumptions = get_assumptions(prg)
    ret = prg.solve(assumptions=assumptions)
#end.
