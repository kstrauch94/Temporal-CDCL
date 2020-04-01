### Using Generalized Nogoods with Incremental Mode

To run clingo in incremental mode we need an incremental encoding with the correct format, and instance, and the correct clingo parameters that tells it to log the nogoods it learns. 

Additionally, we have to create a copy of the inc_config_file.py.example and rename the copy so that it doesnt contain the ".example".

An example command is as follows:

```
clingo inc_generalize.py inc_encodings/basic_encoding_inc.lp blocks-11-nofd.lp --lemma-out-txt --lemma-out=ng_temp.lp --lemma-out-dom=output --heuristic=Domain --dom-mod=level,show --quiet=2 --stats --loops=no --reverse-arcs=0 --otfs=0 --lemma-out-max=1024
```

The parameter *--lemma-out-max=<n>* is used to define how many nogoods to log. Note that the number n means it will log that amount of nogoods **per step**.

To further customize the generalization process we can tweak the values inside the configuration file.