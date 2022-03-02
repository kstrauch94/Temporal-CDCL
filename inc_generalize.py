#script (python) 

import clingo
import inc_lib

def get(val, default):
    return val if val != None else default

def main(prg):
    handler = inc_lib.Handler()

    imin   = get(prg.get_const("imin"), clingo.Number(0))
    imax   = prg.get_const("imax")
    istop  = get(prg.get_const("istop"), clingo.String("SAT"))

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

        if step > 0:
            parts += handler.add_learned_rules(prg, step)

        print(parts)
        prg.ground(parts)
        if step == 0:
            handler.prepare(prg)
        print(step)
        #prg.assign_external(clingo.Function("query", [step]), True)
        if step % 5 == 0:
            print("solving for step ", step)
            ret, step = prg.solve(assumptions=handler.assumptions_for_step(step)), step+1
        else:
            step += 1
#end.

#program check(t).
#external query(t).