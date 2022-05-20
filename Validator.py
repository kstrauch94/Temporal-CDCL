import subprocess
import os

from util import util
import config

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

    def __init__(self, validation_files, val_walltime=None) -> None:
        self.validation_files = validation_files
        self.val_walltime = val_walltime

    def validate_list(self, ng_list, nogoods_wanted):

        validated = []
        print(f"starting {len(ng_list)} validations")
        for i, ng in enumerate(ng_list):
            fail_reason = self.validate(ng)
            if fail_reason is not None:
                util.Count.add(f"Validation failed {fail_reason}")
                continue
            if i == len(ng_list):
                print(f"{i} validations performed")
            else:
                # \r at the end resets the position in the cmd to the start
                # we have to add end="" so that it doesnt go to a new line
                print(f"validations performed: {i}    \r", end="")

            util.Count.add("Validation Successful")
            validated.append(ng)

            if len(validated) == nogoods_wanted:
                break

        return validated

    @util.Timer("Validation")
    def validate(self, nogood):
        #walltime in seconds
        temp_validate = "temp_validate.lp"

        program = Validator.program.format(deg=nogood.degree, t=nogood.generalized, constraint=nogood.to_general_constraint())

        with open(temp_validate, "w") as f:
            f.write(program)

        # build call
        watcher_file = "runsolver.watcher"
        call = [config.RUNSOLVER_PATH, "-o", watcher_file]
        if self.val_walltime is not None:
            call += ["--real-time-limit={}".format(self.val_walltime)]

        call += ["clingo", "--quiet=2", "--stats", "--warn=none", temp_validate] + self.validation_files

        #print("calling : {}".format(" ".join(call)))

        try:
            output = subprocess.check_output(call).decode("utf-8")
        except subprocess.CalledProcessError as e:
            output = e.output.decode("utf-8")

        #print(output)

        os.remove(temp_validate)
        os.remove(watcher_file)

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
