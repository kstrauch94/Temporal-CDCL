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

time(1..degree+1).

% from here on we will use S and not T for time because of the truck T

domain_fuel(T,F) :- fuel(T,F).
domain_fuel(T,F-D) :- domain_fuel(T,F), fuelcost(D,_,_), F>=D.
%domain_fuel(T,F) :- truck(T), fuel(T,F2), F = 1..F2.

domain_at(O,L) :- truck(O), location(L).
domain_at(O,L) :- package(O), location(L).

{at(O,L,0) : domain_at(O,L)}.

{fuel(T,F,0) : domain_fuel(T,F)} :- truck(T).

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

{ occurs(A,S) : action(A) } <= 1 :- time(S). % :- step(S), S > 0.

done(S) :- occurs(A,S), time(S).
:- done(S), not done(S-1), S > 1, time(S).

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
del( fuel( T,Fuelpre ),S ) :- drive( T,L1,L2,S ), fuel(T, Fuelpre,S-1), time(S).
fuel( T,Fuelpre - Fueldelta,S ) :- drive( T,L1,L2,S ), fuelcost(Fueldelta,L1,L2), fuel(T,Fuelpre,S-1), Fuelpre >= Fueldelta, time(S).
% <<<<<  EFFECTS APPLY
%
% INERTIA  >>>>>
at( O,L,S ) :- at( O,L,S-1 ), not del( at( O,L ),S  ), time(S).
in( P,T,S ) :- in( P,T,S-1 ), not del( in( P,T ),S  ), time(S).
fuel( T,Level,S ) :- fuel( T,Level,S-1 ), not del( fuel( T,Level) ,S ), truck( T ), time(S).
% <<<<<  INERTIA
%

%
%
% PRECONDITIONS CHECK  >>>>>

% unload/4, preconditions
 :- unload( P,T,L,S ), not preconditions_u( P,T,L,S ), time(S).
preconditions_u( P,T,L,S ) :- time(S), at( T,L,S-1 ), in( P,T,S-1 ), package( P ), truck( T ).

% load/4, preconditions
 :- load( P,T,L,S ), not preconditions_l( P,T,L,S ), time(S).
preconditions_l( P,T,L,S ) :- time(S), at( T,L,S-1 ), at( P,L,S-1 ).

% drive/5, preconditions
 :- drive( T,L1,L2,S ), not preconditions_d( T,L1,L2,S ), time(S).
preconditions_d( T,L1,L2,S ) :- time(S), at( T,L1,S-1 ), fuel( T, Fuelpre, S-1), fuelcost(Fueldelta,L1,L2), Fuelpre >= Fueldelta.
% <<<<<  PRECONDITIONS HOLD
%
