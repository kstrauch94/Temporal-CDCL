MINIMAL = "minimal" # Minize nogoods, requires validation

SORTBY = "sortby" # list of properties to sort the nogoods in order of sorting priority
                  # possible values: degree, literal_count, ordering, lbd

REVERSE_SORT = "reverse_sort" # sort in reverse order

CONFIG = {  MINIMAL : False,
            SORTBY : ["degree", "literal_count"],
            REVERSE_SORT : False,
}
