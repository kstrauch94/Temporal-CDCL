%Take as input a set of rules of the form:
%  a(T) :- b(T), not c(T), d(T-1), not e(T-1).
%Translate then into a set of rules of the form 
%  a(T) :- b(T), not c(T), prev_d(T), not prev_e(T).
%together with the rules:
%  { prev_x(T) }.
%  :- prev_x(T), not x(T-1), next(T-1,T).
%  :- not prev_x(T), x(T-1), next(T-1,T).
%for every atom x such that x(T-1) appears 
%in some body of the set of rules of the input.


#const horizon = 35.
time(0..horizon).

first(0).
last(horizon).

next(T-1,T) :- time(T), T>0.
#external external(next(X,Y)) : next(X,Y).

% Define initial state
% Define initialstate as external
% use the external formalism to make init state true

mutex(G,X) :- mutexGroup(G), contains(G,X,V). %, fluent(X,V).
mutex(G)   :- mutexGroup(G), #count{X : mutex(G,X)} > 1.


% set initial state
#external external(holds(X,V,T)) : initialState(X,V), first(T).
:- not holds(X,V,T), not external(holds(X,V,T)), initialState(X,V), first(T).

% Check goal conditions

% goal must hold at the last time point
#external external(holds(X,V,T)) : goal(X,V), last(T).
:- not holds(X,V,T), not external(holds(X,V,T)), goal(X,V), last(T).

% No action can be done at time 0
#external external(occurs(A,T)) : action(A), first(T).
:-  occurs(A,T), not external(occurs(A,T)), action(A), first(T).

% generate (a SAT problem)
{     holds(X,V,T) } :- contains(X,V), time(T).
{ occurs(A,T) : action(A) }  :- time(T).

% at most one action
:- 2{occurs(A,T) : action(A)}, time(T).

% effects
%:- occurs(A,T), postcondition(A,_,X,V), not holds(X,V,T).
holds(X,V,T) :- occurs(A,T), postcondition(A,_,X,V).

% preconditions
%:- occurs(A,T), precondition(A,X,V), not holds'(X,V,T).
holds'(X,V,T) :- occurs(A,T), precondition(A,X,V).

% inertia
%:- holds(X,V,T), not holds'(X,V,T), 
%   not occurs(A,T) : postcondition(A,_,X,V) ; time(T), not first(T).

holds(X,V,T) :- holds'(X,V,T), not occurs(A,T) : postcondition(A,_,X,V2), V2 != V; not first(T).

% existence and uniqueness of value
:- not 1 { holds(X,V,T) } 1, variable(X), time(T).

% mutexes
:- 2 #sum { 1,X,V: holds(X,V,T), contains(G,X,V) }, mutex(G), time(T).


{ holds'(X,V,T) } :- contains(X,V), time(T), not first(T).
:- holds'(X,V,T), not holds(X,V,TM1), not external(next(TM1,T)), next(TM1,T).
:- not holds'(X,V,T), holds(X,V,TM1), not external(next(TM1,T)), next(TM1,T).
