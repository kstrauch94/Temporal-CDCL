%
% Sokoban domain IPC 2008
%
% Adaptment from IPC 2008 domain description by GB Ianni, using the PDDL2ASP PLASP converter
% http://www.cs.uni-potsdam.de/wv/pdfformat/gekaknsc11a.pdf 
%
% 
time(T) :- step(T).

last(T) :- time(T), not time(T+1).

loc(L) :- isgoal(L).
loc(L) :- isnongoal(L).

domain_at(P,L) :- loc(L), player(P).
domain_at(S,L) :- loc(L), stone(S).
domain_clear(L) :- loc(L).
domain_at_goal(S) :- stone(S).

{at(P,L,0) : domain_at(P,L)} :- player(P).
{at(S,L,0) : domain_at(S,L)} :- stone(S).

{clear(L,0) : domain_clear(L)}.

atgoal_init(S) :- isgoal(L), stone(S), at(S,L).

{atgoal(S,0) : domain_at_goal(S)}. 

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
clear( L,Ti ) :- clear'( L,Ti ), not del( clear( L ),Ti  ), time(Ti).
atgoal( S,Ti ) :- atgoal'( S,Ti ), not del( atgoal( S ),Ti ), stone( S ), time(Ti).
at( T,L,Ti ) :- at'( T,L,Ti ), not del( at( T,L ) ,Ti  ), time(Ti).
% <<<<<  INERTIA
% 

% 
% 
% PRECONDITIONS HOLD  >>>>>

% push-to-nongoal/6, preconditions
 :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), not preconditions_png( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
preconditions_png( P,S,Ppos,From,To,Dir,Ti ) :- at'( P,Ppos,Ti ), at'( S,From,Ti ), clear'( To,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).

% move/4, preconditions
 :- move( P,From,To,Dir,Ti ), not preconditions_m( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To, time(Ti).
preconditions_m( P,From,To,Dir,Ti ) :- at'( P,From,Ti ), clear'( To,Ti ), movedir( From,To,Dir ), movedir( From,To,Dir ), player( P ), From != To, time(Ti).

% push-to-goal/6, preconditions
 :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), not preconditions_pg( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
preconditions_pg( P,S,Ppos,From,To,Dir,Ti ) :- at'( P,Ppos,Ti ), at'( S,From,Ti ), clear'( To,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).

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

{clear'(L,T)} :- loc(L), time(T), T > 0.
:- clear'(L,T), not clear(L,T-1), otime(T).
:- not clear'(L,T), clear(L,T-1), otime(T).

{at'(PS,L,T)} :- domain_at(PS,L), time(T), T > 0.
:- at'(PS,L,T), not at(PS,L,T-1), otime(T).
:- not at'(PS,L,T), at(PS,L,T-1), otime(T).

{atgoal'(S,T)} :- stone(S), time(T), T > 0.
:- atgoal'(S,T), not atgoal(S,T-1), otime(T).
:- not atgoal'(S,T), atgoal(S,T-1), otime(T).

{ otime(T) } :- time(T).

% initial state
assumption(at(PS,L,0), true) :-     at(PS,L).
assumption(at(PS,L,0),false) :- not at(PS,L), domain_at(PS,L).

assumption(clear(L,0), true) :-     clear(L).
assumption(clear(L,0),false) :- not clear(L), domain_clear(L).

assumption(atgoal(S,0), true) :-     atgoal_init(S).
assumption(atgoal(S,0),false) :- not atgoal_init(S), domain_at_goal(S).

% goal
assumption(atgoal(S,T),true) :- goal(S), last(T).
% otime
assumption(otime(T),true) :- time(T).