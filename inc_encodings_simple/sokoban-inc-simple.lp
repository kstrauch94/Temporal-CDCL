%
% Sokoban dom IPC 2008
%
% Adaptment from IPC 2008 dom description by GB Ianni, using the PDDL2ASP PLASP converter
% http://www.cs.uni-potsdam.de/wv/pdfformat/gekaknsc11a.pdf 
%
% 
#program base.

loc(L) :- isgoal(L).
loc(L) :- isnongoal(L).

dom_at(P,L) :- loc(L), player(P).
dom_at(S,L) :- loc(L), stone(S).
dom_clear(L) :- loc(L).
dom_atgoal(S) :- stone(S).

{at(P,L,0) : dom_at(P,L)} :- player(P).
{at(S,L,0) : dom_at(S,L)} :- stone(S).

{clear(L,0) : dom_clear(L)}.

atgoal_init(S) :- isgoal(L), stone(S), at(S,L).

{atgoal(S,0) : dom_atgoal(S)}. 

% initial state
assumption_init(at(PS,L,0), true) :-     at(PS,L).
assumption_init(at(PS,L,0),false) :- not at(PS,L), dom_at(PS,L).

assumption_init(clear(L,0), true) :-     clear(L).
assumption_init(clear(L,0),false) :- not clear(L), dom_clear(L).

assumption_init(atgoal(S,0), true) :-     atgoal_init(S).
assumption_init(atgoal(S,0),false) :- not atgoal_init(S), dom_atgoal(S).

% goal
assumption_goal(atgoal(S),true) :- stone(S).

% to comply with initial state being complete
% assuming previous state is the same as initial state
preconditions_png( P,S,Ppos,From,To,Dir,0 ) :- at( P,Ppos,0), at( S,From,0 ), clear( To,0 ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.

% move/4, preconditions
preconditions_m( P,From,To,Dir,0 ) :- at( P,From,0), clear( To,0 ), movedir( From,To,Dir ), movedir( From,To,Dir ), player( P ), From != To.

% push-to-goal/6, preconditions
preconditions_pg( P,S,Ppos,From,To,Dir,0 ) :- at( P,Ppos,0 ), at( S,From,0 ), clear( To,0 ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.


#program step(t).

% GENERATE  >>>>>
{ occurs(some_action,t) }.
1 <= { pushtonongoal( P,S,Ppos,From,To,Dir,t ) : 
	movedir( Ppos,From,Dir ) ,
	movedir( From,To,Dir ) , 
	isnongoal( To ) , 
	player( P ) , 
	stone( S ) , Ppos != To , Ppos != From , From != To; 
    move( P,From,To,Dir,t ) : 
	movedir( From,To,Dir ) , 
	player( P ) , From != To;
    pushtogoal( P,S,Ppos,From,To,Dir,t ) : 
	movedir( Ppos,From,Dir ) , 
	movedir( From,To,Dir ) , 
	isgoal( To ) , player( P ) , stone( S ) , Ppos != To , Ppos != From , From != To;
    noop(t) } <= 1 :- occurs(some_action,t).

% <<<<<  GENERATE
% 
 
% EFFECTS APPLY  >>>>>

% push-to-nongoal/7, effects
del( at( P,Ppos ),t ) :- pushtonongoal( P,S,Ppos,From,To,Dir,t ), 
                          movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
del( at( S,From ),t ) :- pushtonongoal( P,S,Ppos,From,To,Dir,t ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
del( clear( To ),t ) :- pushtonongoal( P,S,Ppos,From,To,Dir,t ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
at( P,From,t ) :- pushtonongoal( P,S,Ppos,From,To,Dir,t ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
at( S,To,t ) :- pushtonongoal( P,S,Ppos,From,To,Dir,t ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
clear( Ppos,t ) :- pushtonongoal( P,S,Ppos,From,To,Dir,t ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
del( atgoal( S ),t ) :- pushtonongoal( P,S,Ppos,From,To,Dir,t ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.

% move/5, effects
del( at( P,From ),t ) :- move( P,From,To,Dir,t ), movedir( From,To,Dir ), player( P ), From != To.
del( clear( To ),t ) :- move( P,From,To,Dir,t ), movedir( From,To,Dir ), player( P ), From != To.
at( P,To,t ) :- move( P,From,To,Dir,t ), movedir( From,To,Dir ), player( P ), From != To.
clear( From,t ) :- move( P,From,To,Dir,t ), movedir( From,To,Dir ), player( P ), From != To.

% push-to-goal/7, effects
del( at( P,Ppos ),t ) :- pushtogoal( P,S,Ppos,From,To,Dir,t ), 
                          movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
del( at( S,From ),t ) :- pushtogoal( P,S,Ppos,From,To,Dir,t ), 
                          movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
del( clear( To ),t ) :- pushtogoal( P,S,Ppos,From,To,Dir,t ), 
                         movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
at( P,From,t ) :- pushtogoal( P,S,Ppos,From,To,Dir,t ), 
                   movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
at( S,To,t ) :- pushtogoal( P,S,Ppos,From,To,Dir,t ), 
                 movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
clear( Ppos,t ) :- pushtogoal( P,S,Ppos,From,To,Dir,t ), 
                    movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
atgoal( S,t ) :- pushtogoal( P,S,Ppos,From,To,Dir,t ), 
                  stone( S ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
% <<<<<  EFFECTS APPLY
% 

% 
% 
% INERTIA  >>>>>
clear( L,t ) :- clear( L,t-1 ), not del( clear( L ),t  ).
atgoal( S,t ) :- atgoal( S,t-1 ), not del( atgoal( S ),t ), stone( S ).
at( T,L,t ) :- at( T,L,t-1 ), not del( at( T,L ) ,t  ).
% <<<<<  INERTIA
% 

% 
% 
% PRECONDITIONS HOLD  >>>>>

% push-to-nongoal/6, preconditions
 :- pushtonongoal( P,S,Ppos,From,To,Dir,t ), not preconditions_png( P,S,Ppos,From,To,Dir,t ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
preconditions_png( P,S,Ppos,From,To,Dir,t ) :- at( P,Ppos,t-1 ), at( S,From,t-1 ), clear( To,t-1 ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.

% move/4, preconditions
 :- move( P,From,To,Dir,t ), not preconditions_m( P,From,To,Dir,t ), movedir( From,To,Dir ), player( P ), From != To.
preconditions_m( P,From,To,Dir,t ) :- at( P,From,t-1 ), clear( To,t-1 ), movedir( From,To,Dir ), movedir( From,To,Dir ), player( P ), From != To.

% push-to-goal/6, preconditions
 :- pushtogoal( P,S,Ppos,From,To,Dir,t ), not preconditions_pg( P,S,Ppos,From,To,Dir,t ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
preconditions_pg( P,S,Ppos,From,To,Dir,t ) :- at( P,Ppos,t-1 ), at( S,From,t-1 ), clear( To,t-1 ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.

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

