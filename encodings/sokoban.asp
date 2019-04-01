%
% Sokoban domain IPC 2008
%
% Adaptment from IPC 2008 domain description by GB Ianni, using the PDDL2ASP PLASP converter
% http://www.cs.uni-potsdam.de/wv/pdfformat/gekaknsc11a.pdf 
%
% 
time(s(T)) :- step(T).

first(s(0)).
last(s(T)) :- time(s(T)), not time(s(T+1)).

next(s(T-1), s(T)) :- time(s(T)), T>0.
#external external(next(X,Y)) : next(X,Y).


% initial state
#external external(at(PS,L,T)) : at(PS,L), first(T).
:- not at(PS,L,T), not external(at(PS,L,T)), at(PS,L), first(T).

#external external(clear(L,T)) : clear(L), first(T).
:- not clear(L,T), not external(clear(L,T)), clear(L), first(T).

#external false_external(clear(L,T)) : not clear(L), loc(L), first(T).
:- clear(L,T), not false_external(clear(L,T)), not clear(L), loc(L), first(T).

#external external(atgoal(S,T)) : isgoal(L), stone(S), at(S,L), first(T).
:- not atgoal(S,T), not external(atgoal(S,T)), isgoal(L), stone(S), at(S,L), first(T).

not_atgoal(S) :- stone(S), not at(S,L) : isgoal(L).
#external false_external(atgoal(S,T)) : not_atgoal(S), first(T).
:- atgoal(S,T), not false_external(atgoal(S,T)), not_atgoal(S), first(T).

% goal
#external external(atgoal(S,T)) : goal(S), last(T).
:- not atgoal(S,T), not external(atgoal(S,T)), goal(S), last(T).

loc(L) :- isgoal(L).
loc(L) :- isnongoal(L).

at_domain(P,L) :- loc(L), player(P).
at_domain(S,L) :- loc(L), stone(S).

1 {at(P,L,T) : at_domain(P,L)} 1 :- player(P), first(T).
1 {at(S,L,T) : at_domain(S,L)} 1 :- stone(S), first(T).

{clear(L,T)} :- loc(L), first(T).

{atgoal(S,T)} :- stone(S), first(T).
%atgoal(S,T) :- isgoal(L), stone(S), at(S,L), first(T).

%at(P,To,s(0)) :- at(P,To).
%clear(P,s(0)) :- clear(P).
%atgoal(S,s(0)) :- isgoal(L), stone(S), at(S,L).

% GENERATE  >>>>>
{ occurs(some_action,T) } :- time(T).
1 <= { pushtonongoal( P,S,Ppos,From,To,Dir,T ) : 
	movedir( Ppos,From,Dir ) ,
	movedir( From,To,Dir ) , 
	isnongoal( To ) , 
	player( P ) , 
	stone( S ) , Ppos != To , Ppos != From , From != To; 
    move( P,From,To,Dir,T ) : 
	movedir( From,To,Dir ) , 
	player( P ) , From != To;
    pushtogoal( P,S,Ppos,From,To,Dir,T ) : 
	movedir( Ppos,From,Dir ) , 
	movedir( From,To,Dir ) , 
	isgoal( To ) , player( P ) , stone( S ) , Ppos != To , Ppos != From , From != To;
    noop(T) } <= 1 :- time(T), occurs(some_action,T).

% <<<<<  GENERATE
% 
 
% EFFECTS APPLY  >>>>>

% push-to-nongoal/7, effects
del( at( P,Ppos ),Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), 
                          movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
del( at( S,From ),Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
del( clear( To ),Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
at( P,From,Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
at( S,To,Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
clear( Ppos,Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
del( atgoal( S ),Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).

% move/5, effects
del( at( P,From ),Ti ) :- move( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To, time(Ti).
del( clear( To ),Ti ) :- move( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To, time(Ti).
at( P,To,Ti ) :- move( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To, time(Ti).
clear( From,Ti ) :- move( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To, time(Ti).

% push-to-goal/7, effects
del( at( P,Ppos ),Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                          movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
del( at( S,From ),Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                          movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
del( clear( To ),Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                         movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
at( P,From,Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                   movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
at( S,To,Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                 movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
clear( Ppos,Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                    movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
atgoal( S,Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                  stone( S ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
% <<<<<  EFFECTS APPLY
% 

% 
% 
% INERTIA  >>>>>
clear( L,Ti ) :- prev_clear( L,Ti ), not del( clear( L ),Ti  ), time(Ti).
atgoal( S,Ti ) :- prev_atgoal( S,Ti ), not del( atgoal( S ),Ti ), stone( S ), time(Ti).
at( T,L,Ti ) :- prev_at( T,L,Ti ), not del( at( T,L ) ,Ti  ), time(Ti).
% <<<<<  INERTIA
% 

% 
% 
% PRECONDITIONS HOLD  >>>>>

% push-to-nongoal/6, preconditions
 :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), not preconditions_png( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
preconditions_png( P,S,Ppos,From,To,Dir,Ti ) :- prev_at( P,Ppos,Ti ), prev_at( S,From,Ti ), prev_clear( To,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).

% move/4, preconditions
 :- move( P,From,To,Dir,Ti ), not preconditions_m( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To, time(Ti).
preconditions_m( P,From,To,Dir,Ti ) :- prev_at( P,From,Ti ), prev_clear( To,Ti ), movedir( From,To,Dir ), movedir( From,To,Dir ), player( P ), From != To, time(Ti).

% push-to-goal/6, preconditions
 :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), not preconditions_pg( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
preconditions_pg( P,S,Ppos,From,To,Dir,Ti ) :- prev_at( P,Ppos,Ti ), prev_at( S,From,Ti ), prev_clear( To,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).

% <<<<<  PRECONDITIONS HOLD
% 
%
% Goal Reached check 
%
%goalreached :- step(T), N = #count{ X : atgoal(X,T) , goal(X) }, N = #count{ X1 : goal(X1) }.
%:- not goalreached.

%goalreached(s(T)) :- goalreached(s(T-1)), time(s(T)).
%goalreached(T) :- time(T), N = #count{ X : atgoal(X,T) , goal(X) }, N = #count{ X1 : goal(X1) }.

%:- not goalreached(T), last(T).

{prev_clear(L,T)} :- loc(L), time(T), not first(T).
:- prev_clear(L,T), not clear(L,TM1), not external(next(TM1,T)), next(TM1,T).
:- not prev_clear(L,T), clear(L,TM1), not external(next(TM1,T)), next(TM1,T).

{prev_at(PS,L,T)} :- at_domain(PS,L), time(T), not first(T).
:- prev_at(PS,L,T), not at(PS,L,TM1), not external(next(TM1,T)), next(TM1,T).
:- not prev_at(PS,L,T), at(PS,L,TM1), not external(next(TM1,T)), next(TM1,T).

{prev_atgoal(S,T)} :- stone(S), time(T), not first(T).
:- prev_atgoal(S,T), not atgoal(S,TM1), not external(next(TM1,T)), next(TM1,T).
:- not prev_atgoal(S,T), atgoal(S,TM1), not external(next(TM1,T)), next(TM1,T).

