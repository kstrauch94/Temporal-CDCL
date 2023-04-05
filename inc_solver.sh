#!/bin/bash
cd "$(dirname $0)"
#first agument must always be the max nogoods per step outputted by clingo
OUTMAX=$1
#shift if used to shit arguments so that $@ takes all arguments but the first one
shift
python inc_generalize.py --lemma-out-txt --lemma-out=ng_temp.lp --lemma-out-dom=output --lemma-out-max=$OUTMAX $@