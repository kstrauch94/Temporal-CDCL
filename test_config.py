MINIMAL = "minimal" # Minize nogoods, requires validation

SORTBY = "sortby" # list of properties to sort the nogoods in order of sorting priority
                  # possible values: degree, literal_count, ordering, lbd

REVERSE_SORT = "reverse_sort" # sort in reverse order

VALIDATE_FILES = "validate_files" # if file is given it will validate using this file
                                  # use None to disable validation

CONFIG = {  MINIMAL : False,
            SORTBY : ["degree", "literal_count"],
            REVERSE_SORT : False,
            VALIDATE_FILES : ["validation-encoding/state_prover.lp"]
            #VALIDATE_FILES : ["state_prover-new-rules.lp"]
}
