%
% Sokoban domain IPC 2008
%
% Adaptment from IPC 2008 domain description by GB Ianni, using the PDDL2ASP PLASP converter
% http://www.cs.uni-potsdam.de/wv/pdfformat/gekaknsc11a.pdf 
%
% 

time(T) :- step(T).

% GENERATE  >>>>>
{ occurs(some_action,T) } :- step(T).
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
    noop(T) } <= 1 :- step(T), occurs(some_action,T).

% <<<<<  GENERATE
% 

% 
%
% Initial state
at(P,To,0) :- at(P,To).
clear(P,0) :- clear(P).
atgoal(S,0) :- isgoal(L), stone(S), at(S,L).
 

% to comply with initial state being complete
% assuming previous state is the same as initial state
preconditions_png( P,S,Ppos,From,To,Dir,0 ) :- at( P,Ppos,0), at( S,From,0 ), clear( To,0 ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.

% move/4, preconditions
preconditions_m( P,From,To,Dir,0 ) :- at( P,From,0), clear( To,0 ), movedir( From,To,Dir ), movedir( From,To,Dir ), player( P ), From != To.

% push-to-goal/6, preconditions
preconditions_pg( P,S,Ppos,From,To,Dir,0 ) :- at( P,Ppos,0 ), at( S,From,0 ), clear( To,0 ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.


% EFFECTS APPLY  >>>>>

% push-to-nongoal/7, effects
del( at( P,Ppos ),Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), 
                          movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
del( at( S,From ),Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
del( clear( To ),Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
at( P,From,Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
at( S,To,Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
clear( Ppos,Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
del( atgoal( S ),Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).

% move/5, effects
del( at( P,From ),Ti ) :- move( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To, step(Ti).
del( clear( To ),Ti ) :- move( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To, step(Ti).
at( P,To,Ti ) :- move( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To, step(Ti).
clear( From,Ti ) :- move( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To, step(Ti).

% push-to-goal/7, effects
del( at( P,Ppos ),Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                          movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
del( at( S,From ),Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                          movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
del( clear( To ),Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                         movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
at( P,From,Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                   movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
at( S,To,Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                 movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
clear( Ppos,Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                    movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
atgoal( S,Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                  stone( S ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
% <<<<<  EFFECTS APPLY
% 

% 
% 
% INERTIA  >>>>>
clear( L,Ti ) :- clear( L,Ti-1 ), not del( clear( L ),Ti  ), step(Ti).
atgoal( S,Ti ) :- atgoal( S,Ti-1 ), not del( atgoal( S ),Ti ), stone( S ), step(Ti).
at( T,L,Ti ) :- at( T,L,Ti-1 ), not del( at( T,L ) ,Ti  ), step(Ti).
% <<<<<  INERTIA
% 

% 
% 
% PRECONDITIONS HOLD  >>>>>

% push-to-nongoal/6, preconditions
 :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), not preconditions_png( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
preconditions_png( P,S,Ppos,From,To,Dir,Ti ) :- at( P,Ppos,Ti-1 ), at( S,From,Ti-1 ), clear( To,Ti-1 ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).

% move/4, preconditions
 :- move( P,From,To,Dir,Ti ), not preconditions_m( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To, step(Ti).
preconditions_m( P,From,To,Dir,Ti ) :- at( P,From,Ti-1 ), clear( To,Ti-1 ), movedir( From,To,Dir ), movedir( From,To,Dir ), player( P ), From != To, step(Ti).

% push-to-goal/6, preconditions
 :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), not preconditions_pg( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
preconditions_pg( P,S,Ppos,From,To,Dir,Ti ) :- at( P,Ppos,Ti-1 ), at( S,From,Ti-1 ), clear( To,Ti-1 ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).

% <<<<<  PRECONDITIONS HOLD
% 
%
% Goal Reached check 
%
%goalreached :- step(T), N = #count{ X : atgoal(X,T) , goal(X) }, N = #count{ X1 : goal(X1) }.
%:- not goalreached.

goalreached(T) :- goalreached(T-1), step(T).
goalreached(T) :- step(T), N = #count{ X : atgoal(X,T) , goal(X) }, N = #count{ X1 : goal(X1) }.

:- not goalreached(T), step(T), not step(T+1).

% Gringo directives to show / hide particular literals
%#hide.
#show pushtonongoal/7.
#show move/5.
#show pushtogoal/7.