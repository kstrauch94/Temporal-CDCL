import subprocess
import os

from util import util


RUNSOLVER_PATH = "./runsolver"

UNSAT = "UNSATISFIABLE"
UNK = "UNKNOWN"
TIMEOUT = "TIMEOUT"
INTERRUPTED = "INTERRUPTED"
SAT = "SATISFIABLE"

class Validator:

    program = """#const degree={deg}.
hypothesisConstraint({t}-degree) {constraint}
:- not hypothesisConstraint(1).
"""

    def __init__(self, validation_files) -> None:
        self.validation_files = validation_files


    def validate_list(self, ng_list, walltime=0):

        validated = []
        for ng in ng_list:
            fail_reason = self.validate(ng, walltime)
            if fail_reason is not None:
                util.Count.add(f"Validation failed {fail_reason}")
                continue
            
            util.Count.add("Validation Successful")
            validated.append(ng)

        return validated
    
    @util.Timer("Validation")
    def validate(self, nogood, walltime=0):
        #walltime in seconds

        temp_validate = "temp_validate.lp"

        program = Validator.program.format(deg=nogood.degree, t=nogood.generalized, constraint=nogood.to_general_constraint())

        with open(temp_validate, "w") as f:
            f.write(program)

        # build call
        call = [RUNSOLVER_PATH, "-w", "runsolver.watcher"]
        if walltime is not None:
            call += ["-W", "{}".format(walltime)]

        call += ["clingo", "--quiet=2", "--stats", "--warn=none", temp_validate] + self.validation_files

        #print("calling : {}".format(" ".join(call)))

        try:
            output = subprocess.check_output(call).decode("utf-8")
        except subprocess.CalledProcessError as e:
            output = e.output.decode("utf-8")

        print(output)

        os.remove(temp_validate)
        os.remove("runsolver.watcher")

        if UNSAT in output:
            fail_reason = None

        else:
            self.validated = False

            print("not validated: {}".format(nogood.to_general_constraint()))
            print("number: {}".format(nogood.order))
            if TIMEOUT in output:
                print("validation timed out!")

            fail_reason = "unknown"
            if SAT in output:
                fail_reason = "sat"
            if TIMEOUT in output or INTERRUPTED in output:
                fail_reason = "timeout"

            print("fail reason: {}".format(fail_reason))


        return fail_reason
