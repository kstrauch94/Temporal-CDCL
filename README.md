# Produce nogoods

To produce nogoods use produce_nogoods.py. To run it needs some files(encoding, etc) an instance an amount of nogoods to extract and a configuration. The configuration has to be a python file that contains a dictionary called CONFIG. An example configuration is given in the test_config.py file.

Sample call:

```
python produce_nogoods.py --files encodings/basic.lp --instance test-instances/blocks-11.lp --config test_config --nogoods-limit 10
```

Note that test_config does not have the .py suffix.

Additionally, pddl instances can be used instead of regular asp instances with the --pddl-instance option. The program will try to find the domain file in the same folder of the instance or in the parent folder. A domain can also be manually given with the --pddl-domain option.

Sample call:

```
python produce_nogoods.py --files encodings/basic.lp --pddl-instance path/to/pddl/instance.pddl --config test_config --nogoods-limit 10
```

For more option use --help

The nogoods will be saved into a file called conv_ng.lp

## Validating nogoods

To validate nogoods set the value of VALIDATE in test_config.py to a file that can be used to validate them. E.g state_prover.lp when using basic.lp as the encoding.

# Consuming nogoods

There are 2 options to consume nogoods. One is to consume the nogoods directly after producing them. Just use the --consume option along with the calls given above. 

The second option is to use the consume_nogoods.py program. A file containing the output nogoods from a produce_nogoods.py call have to be given as input with the --nogoods option.

Sample call:

```
python consume_nogoods.py --files encodings/basic.lp --instance test-instances/blocks-11.lp --nogoods conv_ng.lp 
```

Pddl instances are supported in the same way as in the produce_nogoods.py program.

