%
% Sokoban domain IPC 2008
%
% Adaptment from IPC 2008 domain description by GB Ianni, using the PDDL2ASP PLASP converter
% http://www.cs.uni-potsdam.de/wv/pdfformat/gekaknsc11a.pdf 
%
% 

time(0).

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

% 
%
% Initial state
:- at(P,To,0), at(P,To).
:- clear(P,0), clear(P).
:- atgoal(S,0), isgoal(L), stone(S), at(S,L).
 
loc(L) :- isgoal(L).
loc(L) :- isnongoal(L).

domain_at(P,L) :- loc(L), player(P).
domain_at(S,L) :- loc(L), stone(S).
domain_clear(L) :- loc(L).
domain_at_goal(S) :- stone(S).

{clear(L,T-1)} :- loc(L), time(T).

{at(PS,L,T-1)} :- domain_at(PS,L), time(T).

{atgoal(S,T-1)} :- stone(S), time(T).

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
clear( L,Ti ) :- clear( L,Ti-1 ), not del( clear( L ),Ti  ), time(Ti).
atgoal( S,Ti ) :- atgoal( S,Ti-1 ), not del( atgoal( S ),Ti ), stone( S ), time(Ti).
at( T,L,Ti ) :- at( T,L,Ti-1 ), not del( at( T,L ) ,Ti  ), time(Ti).
% <<<<<  INERTIA
% 

% 
% 
% PRECONDITIONS HOLD  >>>>>

% push-to-nongoal/6, preconditions
 :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), not preconditions_png( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
preconditions_png( P,S,Ppos,From,To,Dir,Ti ) :- at( P,Ppos,Ti-1 ), at( S,From,Ti-1 ), clear( To,Ti-1 ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).

% move/4, preconditions
 :- move( P,From,To,Dir,Ti ), not preconditions_m( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To, time(Ti).
preconditions_m( P,From,To,Dir,Ti ) :- at( P,From,Ti-1 ), clear( To,Ti-1 ), movedir( From,To,Dir ), movedir( From,To,Dir ), player( P ), From != To, time(Ti).

% push-to-goal/6, preconditions
 :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), not preconditions_pg( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).
preconditions_pg( P,S,Ppos,From,To,Dir,Ti ) :- at( P,Ppos,Ti-1 ), at( S,From,Ti-1 ), clear( To,Ti-1 ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, time(Ti).

% <<<<<  PRECONDITIONS HOLD
% 
%
% Goal Reached check 
%
%goalreached :- time(T), N = #count{ X : atgoal(X,T) , goal(X) }, N = #count{ X1 : goal(X1) }.
%:- not goalreached.

%goalreached(T) :- goalreached(T-1), time(T).
%goalreached(T) :- time(T), N = #count{ X : atgoal(X,T) , goal(X) }, N = #count{ X1 : goal(X1) }.

%:- not goalreached(T), time(T), not time(T+1).

% Gringo directives to show / hide particular literals
%#hide.
#show pushtonongoal/7.
#show move/5.
#show pushtogoal/7.