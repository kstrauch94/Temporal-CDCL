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


#const maxtime = 6.
time(s(0..maxtime)).
next(s(T-1), s(T)) :- time(s(T)), T>0.
#external external(next(X,Y)) : next(X,Y).

first(s(0)).
last(s(maxtime)).


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


{ prev_holds(X,V,T) } :- contains(X,V), time(T), not first(T).
:- prev_holds(X,V,s(T)), not holds(X,V,s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).
:- not prev_holds(X,V,s(T)), holds(X,V,s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).

% at most one action
:- 2{occurs(A,T) : action(A)}, time(T).

% effects
%:- occurs(A,T), postcondition(A,_,X,V), not holds(X,V,T).
holds(X,V,T) :- occurs(A,T), postcondition(A,_,X,V).

% preconditions
%:- occurs(A,T), precondition(A,X,V), not prev_holds(X,V,T).

prev_holds(X,V,T) :- occurs(A,T), precondition(A,X,V).

% inertia
:- holds(X,V,T), not prev_holds(X,V,T), 
   not occurs(A,T) : postcondition(A,_,X,V) ; time(T), not first(T).

%holds(X,V,T) :- prev_holds(X,V,T), not occurs(A,T) : postcondition(A,_,X,V2), V2 != V; not first(T).

% existence and uniqueness of value
:- not 1 { holds(X,V,T) } 1, variable(X), time(T).

% mutexes
:- 2 #sum { 1,X,V: holds(X,V,T), contains(G,X,V) }, mutex(G), time(T).

% Check goal conditions

% goal must hold at the last time point
#external external(holds(X,V,T)) : goal(X,V), last(T).
:- not holds(X,V,T), not external(holds(X,V,T)), goal(X,V), last(T).


