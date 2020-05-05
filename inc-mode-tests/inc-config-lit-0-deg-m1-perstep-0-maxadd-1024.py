#script (python) 

OPTIONS = {"inc_t": True,
            "max_lit_count": 0,
            "max_deg": -1,
            "grab_last": False,
            "nogoods_wanted": 0,
            "nogoods_wanted_by_count" :-1,
            "sortby": ["literal_count"], 
            "validate_files": None, 
            "reverse_sort": False,
            "validate_instance": False,
            "validate_instance_files": None,
            "transform_prime": False,
            "no_nogood_stats": False,
            "val_walltime": None}

# This is the maximum nogoods to add across ALL time steps
# after this amount of nogoods have been added,
# no more generalization will take place
MAX_NOGOODS_TO_ADD = 1024

#end.
