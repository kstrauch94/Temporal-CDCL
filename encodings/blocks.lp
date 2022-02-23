
time(0..horizon).

action(move(B,L)) :- block(B), loc(L), B != L.


{ on(B,L,0) } :- domain_on(B,L).

{do(A,T) : action(A)} 1 :- time(T), T>0.

clear(B,T) :- not on(B2,B,T) : block(B2), B2 != B; block(B), time(T).
clear(table,T) :- time(T).

%precondition
:- do(move(B,L),T), not clear'(L,T).
:- do(move(B,L),T), not clear'(B,T).

%postcodition
on(B,L,T) :- do(move(B,L),T).

%inertia
on(B,L,T) :- on'(B,L,T), not do(move(B,L2),T) : loc(L2), L2 != L ; block(B), time(T), T>0.

% cant have 2 blocks on 1 block
:- on(B1,B,T), on(B2,B,T), B1 < B2, block(B).

% cant have 1 block on 2 blocks
:- on(B,B1,T), on(B,B2,T), B1 < B2.

% block can't be on top of each other
:- on(B1,B2,T), on(B2,B1,T).

% block can't be on itself
:- on(B,B,T), time(T).


domain_on(B,L) :- block(B), loc(L), L != B.
{ on'(B,L,T) } :- domain_on(B,L), time(T), T>0.
:- on'(B,L,T), not on(B,L,T-1), otime(T).
:- not on'(B,L,T), on(B,L,T-1), otime(T).

domain_clear(L) :- loc(L).
{ clear'(L,T) } :- domain_clear(L), time(T), T>0.
:- clear'(L,T), not clear(L,T-1), otime(T).
:- not clear'(L,T), clear(L,T-1), otime(T).

{ otime(T) } :- time(T).

%
% Define assumptions
%

% initial state
assumption(on(B,L,0), true) :-     init(on(B,L)).
assumption(on(B,L,0),false) :- not init(on(B,L)), domain_on(B,L).
% goal
assumption(on(B,L,horizon),true) :- goal(on(B,L)).
% otime
assumption(otime(T),true) :- time(T).
