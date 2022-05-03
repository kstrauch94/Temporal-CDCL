%
% Sokoban domain IPC 2008
%
% Adaptment from IPC 2008 domain description by GB Ianni, using the PDDL2ASP PLASP converter
% http://www.cs.uni-potsdam.de/wv/pdfformat/gekaknsc11a.pdf 
%
% 
#program base.

loc(L) :- isgoal(L).
loc(L) :- isnongoal(L).

domain_at(P,L) :- loc(L), player(P).
domain_at(S,L) :- loc(L), stone(S).
domain_clear(L) :- loc(L).
domain_at_goal(S) :- stone(S).

{at(P,L,0) : domain_at(P,L)} = 1 :- player(P).
{at(S,L,0) : domain_at(S,L)} = 1 :- stone(S).

{clear(L,0) : domain_clear(L)}.

atgoal_init(S,0) :- isgoal(L), stone(S), at(S,L).

{atgoal(S,0) : domain_at_goal(S)}. 

% initial state
assumption_init(at(PS,L,0), true) :-     at(PS,L).
assumption_init(at(PS,L,0),false) :- not at(PS,L), domain_at(PS,L).

assumption_init(clear(L,0), true) :-     clear(L).
assumption_init(clear(L,0),false) :- not clear(L), domain_clear(L).

assumption_init(atgoal(S,0), true) :-     atgoal_init(S).
assumption_init(atgoal(S,0),false) :- not atgoal_init(S), domain_at_goal(S).

% goal
assumption_goal(atgoal(S),true) :- stone(S).

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
clear( L,t ) :- clear'( L,t ), not del( clear( L ),t  ).
atgoal( S,t ) :- atgoal'( S,t ), not del( atgoal( S ),t ), stone( S ).
at( T,L,t ) :- at'( T,L,t ), not del( at( T,L ) ,t  ).
% <<<<<  INERTIA
% 

% 
% 
% PRECONDITIONS HOLD  >>>>>

% push-to-nongoal/6, preconditions
 :- pushtonongoal( P,S,Ppos,From,To,Dir,t ), not preconditions_png( P,S,Ppos,From,To,Dir,t ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
preconditions_png( P,S,Ppos,From,To,Dir,t ) :- at'( P,Ppos,t ), at'( S,From,t ), clear'( To,t ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.

% move/4, preconditions
 :- move( P,From,To,Dir,t ), not preconditions_m( P,From,To,Dir,t ), movedir( From,To,Dir ), player( P ), From != To.
preconditions_m( P,From,To,Dir,t ) :- at'( P,From,t ), clear'( To,t ), movedir( From,To,Dir ), movedir( From,To,Dir ), player( P ), From != To.

% push-to-goal/6, preconditions
 :- pushtogoal( P,S,Ppos,From,To,Dir,t ), not preconditions_pg( P,S,Ppos,From,To,Dir,t ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
preconditions_pg( P,S,Ppos,From,To,Dir,t ) :- at'( P,Ppos,t ), at'( S,From,t ), clear'( To,t ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.

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

