% background
variable(loaded). variable(alive(1)). variable(alive(2)).
value(true). value(false).

contains(F,V) :- variable(F), value(V).

action(load).
action(shoot(1..2)).

precondition(load,loaded,false).
postcondition(load,no,loaded,true).

precondition(shoot(P),loaded,true) :- P=1..2.
postcondition(shoot(P),no,alive(P),false) :- P=1..2.
postcondition(shoot(P),no,loaded,false) :- P=1..2.

initialState(loaded,false).
initialState(alive(1..2),true).

goal(alive(1..2),false).