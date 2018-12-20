#const maxtime = 50.
time(s(0..maxtime)).
next(s(T-1), s(T)) :- time(s(T)), T>0.
#external external(next(X,Y)) : next(X,Y).


% Define initial state
% Define initialstate as external
% use the external formalism to make init state true

mutex(G,X) :- mutexGroup(G), contains(G,X,V). %, fluent(X,V).
mutex(G)   :- mutexGroup(G), #count{X : mutex(G,X)} > 1.


% set initial state
#external external(holds(X,V,s(0))) : initialState(X,V).
:- not holds(X,V,s(0)), not external(holds(X,V,s(0))), initialState(X,V).

% No action can be done at time 0
#external external(occurs(A,s(0))) : action(A).
:-  occurs(A,s(0)), not external(occurs(A,s(0))), action(A).

% generate (a SAT problem)
{     holds(X,V,T) } :- contains(X,V), time(T).
{ occurs(A,T) : action(A) }  :- time(T).

% at most one action
:- 2{occurs(A,T) : action(A)}, time(T).

% effects
:- occurs(A,T), postcondition(A,_,X,V), not holds(X,V,T).
%holds(X,V,T) :- occurs(A,T), postcondition(A,_,X,V).

% preconditions
:- occurs(A,s(T)), precondition(A,X,V), not holds(X,V,s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).

% inertia
:- holds(X,V,s(T)), not holds(X,V,s(T-1)), 
   not occurs(A,s(T)) : postcondition(A,_,X,V) ; not external(next(s(T-1), s(T))), next(s(T-1), s(T)).

% existence and uniqueness of value
:- not 1 { holds(X,V,T) } 1, variable(X), time(T).

% mutexes
:- 2 #sum { 1,X,V: holds(X,V,T), contains(G,X,V) }, mutex(G), time(T).

% Check goal conditions
% use external formalism to make goal true
% for now we set the goal for the last time step

% goal must hold at the last time point
#external external(holds(X,V,s(maxtime))) : goal(X,V).
:- not holds(X,V,s(maxtime)), not external(holds(X,V,s(maxtime))), goal(X,V).
