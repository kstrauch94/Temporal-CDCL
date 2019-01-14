# Produce nogoods

To produce nogoods use __produce_nogoods.py__. To run it needs some files(encoding, etc), an instance, an amount of nogoods to extract and a configuration. The configuration has to be a python file that contains a dictionary called CONFIG. An example configuration is given in the __test_config.py__ file.

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

For more options use --help

The nogoods will be saved into a file called __conv_ng.lp__

## Validating nogoods

To validate nogoods use the option --validate-files. The value of the option must be a file(s) that can be used to validate them. E.g __validation-encoding/state_prover.lp__ when using basic.lp as the encoding.

# Consuming nogoods

There are 2 options to consume nogoods. One is to consume the nogoods directly after producing them. Just use the --consume option along with the calls given above. 

The second option is to use the __consume_nogoods.py__ program. A file containing the output nogoods from a __produce_nogoods.py__ call have to be given as input with the --nogoods option.

Sample call:

```
python consume_nogoods.py --files encodings/basic.lp --instance test-instances/blocks-11.lp --nogoods conv_ng.lp 
```

Pddl instances are supported in the same way as in the produce_nogoods.py program.

## Scaling

The nogoods are consumed based on a set scaling given with the --scaling option. The input has 3 values separated by a comma. The first value is that starting amount of nogoods. The second value is the increase factor. The third value is how many iterations to perform.

For example, a scaling of 8,2,5 will start by using 8 nogoods. The noogods used will be doubled after every iteration and there will be a total of 5 iterations. So, there will be 5 clingo calls where 8, 16, 32, 64 and 128 nogoods are consumed.

