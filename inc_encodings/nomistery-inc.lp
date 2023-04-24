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

#program base.

%%%
% define domains
%%%
domain_fuel(T,F) :- fuel(T,F).
domain_fuel(T,F-D) :- domain_fuel(T,F), fuelcost(D,_,_), F>=D.

domain_at(O,L) :- truck(O), location(L).
domain_at(O,L) :- package(O), location(L).

domain_in(P,T) :- package(P), truck(T).

domain_done.

{at(O,L,0) : domain_at(O,L)}.
{in(P,T,0) : domain_in(P,T)}.
{fuel(T,F,0) : domain_fuel(T,F)}.
{done(0)}.

truck(T) :- fuel(T,_).
package(P) :- at(P,L), not truck(P).
location(L) :- fuelcost(_,L,_).
location(L) :- fuelcost(_,_,L).
locatable(O) :- at(O,L).

action(unload(P,T,L))  :- package( P ), truck( T ), location( L ).
action(load(P,T,L))    :- package( P ), truck( T ), location( L ).
action(drive(T,L1,L2)) :- fuelcost( Fueldelta,L1,L2 ) , truck( T ).

% initial state
assumption_init(at(O,L,0), true) :-     at(O,L).
assumption_init(at(O,L,0),false) :- not at(O,L), domain_at(O,L).

assumption_init(in(P,L,0),false) :- dom_in(P,L).

assumption_init(fuel(T,F,0), true) :-     fuel(T,F).
assumption_init(fuel(T,F,0),false) :- not fuel(T,F), domain_fuel(T,F).

assumption_init(done(0),false).
% goal
assumption_goal(at(P,L),true) :- goal(P,L).

% make sure these exist to fullfill condition that init state must be complete
% assuming "previous" state is the same state as init state
preconditions_u( P,T,L,0 ) :- at( T,L,0 ), in( P,T,0 ), package( P ), truck( T ).

% load/4, preconditions
preconditions_l( P,T,L,0 ) :- at( T,L,0 ), at( P,L,0 ).

% drive/5, preconditions
preconditions_d( T,L1,L2,0 ) :- at( T,L1,0 ), fuel( T, Fuelpre, 0), fuelcost(Fueldelta,L1,L2), Fuelpre >= Fueldelta.


#program step(t).
%
% GENERATE  >>>>>

{ occurs(A,t) : action(A) } <= 1.

done(t) :- occurs(A,t).
:- done(t), not done'(t), t > 1.

unload( P,T,L,t )  :- occurs(unload(P,T,L),t).
load( P,T,L,t )    :- occurs(load(P,T,L),t).
drive( T,L1,L2,t ) :- occurs(drive(T,L1,L2),t).
% <<<<<  GENERATE

% unload/4, effects
at( P,L,t ) :- unload( P,T,L,t ).
del( in( P,T ),t ) :- unload( P,T,L,t ).

% load/4, effects
del( at( P,L ),t ) :- load( P,T,L,t ).
in( P,T,t ) :- load( P,T,L,t ).

% drive/4, effects
del( at( T,L1 ), t ) :- drive( T,L1,L2,t ).
at( T,L2,t ) :- drive( T,L1,L2,t).
del( fuel( T,Fuelpre ),t ) :- drive( T,L1,L2,t ), fuel'(T, Fuelpre,t).
fuel( T,Fuelpre - Fueldelta,t ) :- drive( T,L1,L2,t ), fuelcost(Fueldelta,L1,L2), fuel'(T,Fuelpre,t), Fuelpre >= Fueldelta.
% <<<<<  EFFECTS APPLY
%
% INERTIA  >>>>>
at( O,L,t ) :- at'( O,L,t ), not del( at( O,L ),t  ).
in( P,T,t ) :- in'( P,T,t ), not del( in( P,T ),t  ).
fuel( T,Level,t ) :- fuel'( T,Level,t ), not del( fuel( T,Level) ,t ), truck( T ).
% <<<<<  INERTIA
%

%
%
% PRECONDITIONS CHECK  >>>>>

% unload/4, preconditions
 :- unload( P,T,L,t ), not preconditions_u( P,T,L,t ).
preconditions_u( P,T,L,t ) :- at'( T,L,t ), in'( P,T,t ), package( P ), truck( T ).

% load/4, preconditions
 :- load( P,T,L,t ), not preconditions_l( P,T,L,t ).
preconditions_l( P,T,L,t ) :- at'( T,L,t ), at'( P,L,t ).

% drive/5, preconditions
 :- drive( T,L1,L2,t ), not preconditions_d( T,L1,L2,t ).
preconditions_d( T,L1,L2,t ) :- at'( T,L1,t ), fuel'( T, Fuelpre, t), fuelcost(Fueldelta,L1,L2), Fuelpre >= Fueldelta.
% <<<<<  PRECONDITIONS HOLD
%
