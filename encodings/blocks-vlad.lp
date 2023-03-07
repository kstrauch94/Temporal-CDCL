#const grippers=1.

time(1..horizon).

location(L) :- loc(L).

on(B,L,0) :- init(on(B,L)).

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

:- goal(on(B,B2)), not on(B,B2,horizon).

domain_on(B,L) :- block(B), loc(L).
{ on'(B,L,T) } :- domain_on(B,L), time(T), T>0.
:- on'(B,L,T), not on(B,L,T-1), otime(T).
:- not on'(B,L,T), on(B,L,T-1), otime(T).

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