%
% Nomystery for ASP 2013.
%
% Domain specification freely adapted from the plasp PDDL-to-ASP output
% (http://potassco.sourceforge.net/labs.html)
%
% Author (2013) GB Ianni
%
%
%
time(T) :- step(T).
last(T) :- time(T), not time(T+1).

truck(T) :- fuel(T,_).
package(P) :- at(P,L), not truck(P).
location(L) :- fuelcost(_,L,_).
location(L) :- fuelcost(_,_,L).
locatable(O) :- at(O,L).
%
domain_fuel(T,F) :- fuel(T,F).
domain_fuel(T,F-D) :- domain_fuel(T,F), fuelcost(D,_,_), F>=D.
%domain_fuel(T,F) :- truck(T), fuel(T,F2), F = 1..F2.

domain_at(O,L) :- truck(O), location(L).
domain_at(O,L) :- package(O), location(L).

domain_in(P,T) :- package(P), truck(T).


{at(O,L,0) : domain_at(O,L)}.
{in(P,T,0) : domain_in(P,T)}.
{fuel(T,F,0) : domain_fuel(T,F)}.
{done(0)}.

%

action(unload(P,T,L))  :- package( P ), truck( T ), location( L ).
action(load(P,T,L))    :- package( P ), truck( T ), location( L ).
action(drive(T,L1,L2)) :- fuelcost( Fueldelta,L1,L2 ) , truck( T ).

%
% GENERATE  >>>>>

{ occurs(A,S) : action(A) } <= 1 :- step(S). % :- step(S), 0 < S.

done(S) :- occurs(A,S), step(S).
%:- done(S), not done(S-1), 1 < S, step(S). % only valid from step 2 onwards?

unload( P,T,L,S )  :- occurs(unload(P,T,L),S), step(S).
load( P,T,L,S )    :- occurs(load(P,T,L),S), step(S).
drive( T,L1,L2,S ) :- occurs(drive(T,L1,L2),S), step(S).
% <<<<<  GENERATE

% unload/4, effects
at( P,L,S ) :- unload( P,T,L,S ), step(S).
del( in( P,T ),S ) :- unload( P,T,L,S ), step(S).

% load/4, effects
del( at( P,L ),S ) :- load( P,T,L,S ), step(S).
in( P,T,S ) :- load( P,T,L,S ), step(S).

% drive/4, effects
del( at( T,L1 ), S ) :- drive( T,L1,L2,S ), step(S).
at( T,L2,S ) :- drive( T,L1,L2,S), step(S).
del( fuel( T,Fuelpre ),S ) :- drive( T,L1,L2,S ), fuel(T, Fuelpre,S-1), step(S).
fuel( T,Fuelpre - Fueldelta,S ) :- drive( T,L1,L2,S ), fuelcost(Fueldelta,L1,L2), fuel(T,Fuelpre,S-1), Fuelpre >= Fueldelta, step(S).
% <<<<<  EFFECTS APPLY
%
% INERTIA  >>>>>
at( O,L,S ) :- at( O,L,S-1 ), not del( at( O,L ),S  ), step(S).
in( P,T,S ) :- in( P,T,S-1 ), not del( in( P,T ),S  ), step(S).
fuel( T,Level,S ) :- fuel( T,Level,S-1 ), not del( fuel( T,Level) ,S ), truck( T ), step(S).
% <<<<<  INERTIA
%

%
%
% PRECONDITIONS CHECK  >>>>>

% unload/4, preconditions
 :- unload( P,T,L,S ), not preconditions_u( P,T,L,S ), step(S).
preconditions_u( P,T,L,S ) :- step(S), at( T,L,S-1 ), in( P,T,S-1 ), package( P ), truck( T ).

% load/4, preconditions
 :- load( P,T,L,S ), not preconditions_l( P,T,L,S ), step(S).
preconditions_l( P,T,L,S ) :- step(S), at( T,L,S-1 ), at( P,L,S-1 ).

% drive/5, preconditions
 :- drive( T,L1,L2,S ), not preconditions_d( T,L1,L2,S ), step(S).
preconditions_d( T,L1,L2,S ) :- step(S), at( T,L1,S-1 ), fuel( T, Fuelpre, S-1), fuelcost(Fueldelta,L1,L2), Fuelpre >= Fueldelta.
% <<<<<  PRECONDITIONS HOLD
%

% initial state
assumption(at(O,L,0), true) :-     at(O,L).
assumption(at(O,L,0),false) :- not at(O,L), domain_at(O,L).

assumption(in(P,L,0),false) :- domain_in(P,L).

assumption(fuel(T,F,0), true) :-     fuel(T,F).
assumption(fuel(T,F,0),false) :- not fuel(T,F), domain_fuel(T,F).

assumption(done(0),false).
% goal
assumption(at(P,L,S),true) :- goal(P,L), last(S).
