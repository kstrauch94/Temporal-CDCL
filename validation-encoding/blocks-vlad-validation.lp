% for PDDL instances

block(B) :- has(constant(B), type("block")).
loc(L) :- block(L).
loc(table).

init(on(B,L)) :- initialState(variable(("on", constant(B), constant(L))), value(variable(("on", constant(B), constant(L))), true)).

init(on(B,table)) :- initialState(variable(("ontable", constant(B))), value(variable(("ontable", constant(B))), true)).

goal(on(B,L)) :- goal(variable(("on", constant(B), constant(L))), value(variable(("on", constant(B), constant(L))), true)).

%

#const grippers=1.

time(1..degree+1).

location(L) :- loc(L).

{on(B,L,0) : location(L)} :- block(B).

% GENERATE
{move(B,L,T) : block(B), location(L)} grippers :- time(T).

% DEFINE
% effect of moving a block
on(B,L,T) :- move(B,L,T), block(B), location(L), time(T).

% inertia
on(B,L,T) :- on(B,L,T-1), not -on(B,L,T), location(L), block(B), time(T).

% uniqueness of location
-on(B,L1,T) :- on(B,L,T), L!=L1, block(B), location(L), location(L1), time(T).

% TEST
% two blocks cannot be on top of the same block

:- 2 {on(B1,B,T) : block(B1)}, block(B), time(T).

% a block can’t be moved unless it is clear
:- move(B,L,T), on(B1,B,T-1), block(B), block(B1), location(L), time(T).

% a block can’t be moved onto a block that is being moved also
:- move(B,B1,T), move(B1,L,T), block(B), block(B1), location(L), time(T), grippers > 1.


%#show move/3.