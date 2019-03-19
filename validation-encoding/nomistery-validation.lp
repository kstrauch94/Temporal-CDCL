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

time(s(1..degree)).

first(s(0)).
second(s(1)).
last(s(T)) :- time(s(T)), not time(s(T+1)).

next(s(T-1), s(T)) :- time(s(T)), T>0.
#external external(next(X,Y)) : next(X,Y).

% from here on we will use S and not T for time because of the truck T



1 {at(P,L,S) : location(L)} 1 :- package(P), first(S).
1 {at(T,L,S) : location(L)} 1 :- truck(T), first(S).
fuel(T,F,S) :- fuel(T,F), first(S).

truck(T) :- fuel(T,_).
package(P) :- at(P,L), not truck(P).
location(L) :- fuelcost(_,L,_).
location(L) :- fuelcost(_,_,L).
locatable(O) :- at(O,L).

action(unload(P,T,L))  :- package( P ), truck( T ), location( L ).
action(load(P,T,L))    :- package( P ), truck( T ), location( L ).
action(drive(T,L1,L2)) :- fuelcost( Fueldelta,L1,L2 ) , truck( T ).

%
% GENERATE  >>>>>

{ occurs(A,S) : action(A) } <= 1 :- time(S). % :- step(S), 0 < S.

done(S) :- occurs(A,S), time(S).
:- done(S), not prev_done(S), not first(S), not second(S), time(S).

unload( P,T,L,S )  :- occurs(unload(P,T,L),S), time(S).
load( P,T,L,S )    :- occurs(load(P,T,L),S), time(S).
drive( T,L1,L2,S ) :- occurs(drive(T,L1,L2),S), time(S).
% <<<<<  GENERATE

% unload/4, effects
at( P,L,S ) :- unload( P,T,L,S ), time(S).
del( in( P,T ),S ) :- unload( P,T,L,S ), time(S).

% load/4, effects
del( at( P,L ),S ) :- load( P,T,L,S ), time(S).
in( P,T,S ) :- load( P,T,L,S ), time(S).

% drive/4, effects
del( at( T,L1 ), S ) :- drive( T,L1,L2,S ), time(S).
at( T,L2,S ) :- drive( T,L1,L2,S), time(S).
del( fuel( T,Fuelpre ),S ) :- drive( T,L1,L2,S ), prev_fuel(T, Fuelpre,S), time(S).
fuel( T,Fuelpre - Fueldelta,S ) :- drive( T,L1,L2,S ), fuelcost(Fueldelta,L1,L2), prev_fuel(T,Fuelpre,S), Fuelpre >= Fueldelta, time(S).
% <<<<<  EFFECTS APPLY
%
% INERTIA  >>>>>
at( O,L,S ) :- prev_at( O,L,S ), not del( at( O,L ),S  ), time(S).
in( P,T,S ) :- prev_in( P,T,S ), not del( in( P,T ),S  ), time(S).
fuel( T,Level,S ) :- prev_fuel( T,Level,S ), not del( fuel( T,Level) ,S ), truck( T ), time(S).
% <<<<<  INERTIA
%

%
%
% PRECONDITIONS CHECK  >>>>>

% unload/4, preconditions
 :- unload( P,T,L,S ), not preconditions_u( P,T,L,S ), time(S).
preconditions_u( P,T,L,S ) :- time(S), prev_at( T,L,S ), prev_in( P,T,S ), package( P ), truck( T ).

% load/4, preconditions
 :- load( P,T,L,S ), not preconditions_l( P,T,L,S ), time(S).
preconditions_l( P,T,L,S ) :- time(S), prev_at( T,L,S ), prev_at( P,L,S ).

% drive/5, preconditions
 :- drive( T,L1,L2,S ), not preconditions_d( T,L1,L2,S ), time(S).
preconditions_d( T,L1,L2,S ) :- time(S), prev_at( T,L1,S ), prev_fuel( T, Fuelpre, S), fuelcost(Fueldelta,L1,L2), Fuelpre >= Fueldelta.
% <<<<<  PRECONDITIONS HOLD
%

% GOAL CHECK
%:- goal(P,L), not at(P,L,S), step(S), not step(S+1).
%:- goal(P,L), step(S), not step(S+1), not at(P,L,S).

% goalreached :- step(S),  N = #count{ P,L : at(P,L,S) , goal(P,L) }, N = #count{ P1,L1 : goal(P1,L1) }.
% :- not goalreached.


{prev_done(S)} :- time(S), not first(S).
:- prev_done(S), not done(SM1), not external(next(SM1,S)), next(SM1,S).
:- not prev_done(S), done(SM1), not external(next(SM1,S)), next(SM1,S).


fuel_domain(T,F) :- fuel(T,F).
fuel_domain(T,F-D) :- fuel_domain(T,F), fuelcost(D,_,_), F>=D.
%fuel_domain(T,F) :- truck(T), fuel(T,F2), F = 1..F2.
{prev_fuel(T,F,S)} :- fuel_domain(T,F), time(S), not first(S).
:- prev_fuel(T,F,S), not fuel(T,F,SM1), not external(next(SM1,S)), next(SM1,S).
:- not prev_fuel(T,F,S), fuel(T,F,SM1), not external(next(SM1,S)), next(SM1,S).

at_domain(O,L) :- truck(O), location(L).
at_domain(O,L) :- package(O), location(L).
{prev_at(O,L,S)} :- at_domain(O,L), time(S), not first(S).
:- prev_at(O,L,S), not at(O,L,SM1), not external(next(SM1,S)), next(SM1,S).
:- not prev_at(O,L,S), at(O,L,SM1), not external(next(SM1,S)), next(SM1,S).

in_domain(P,T) :- package(P), truck(T).
{prev_in(P,T,S)} :- in_domain(P,T), time(S), not first(S).
:- prev_in(P,T,S), not in(P,T,SM1), not external(next(SM1,S)), next(SM1,S).
:- not prev_in(P,T,S), in(P,T,SM1), not external(next(SM1,S)), next(SM1,S).

% Gringo directives to show / hide particular literals
%#hide.
%#show unload/4.
%#show load/4.
%#show drive/4.
%#show at/2.
%#show at/3.
%#show occurs/2.


:- not hypothesisConstraint(s(0)).
