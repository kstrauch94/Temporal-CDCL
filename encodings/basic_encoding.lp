%
% Domain
%

#const horizon = 35.
time(1..horizon).


%
% Preprocessing
%

mutex(G,X) :- mutexGroup(G), contains(G,X,V).
mutex(G)   :- mutexGroup(G), #count{X : mutex(G,X)} > 1.


%
% Initial situation
%

% open initial situation
{ holds(X,V,0) } :- contains(X,V).


%
% Transition
%

% generate (a SAT problem)
{     holds(X,V,T) } :- contains(X,V), time(T).
{ occurs(A,T) : action(A) }  :- time(T).

% at most one action
:- 2 { occurs(A,T) : action(A) }, time(T).

% effects
:- occurs(A,T), postcondition(A,_,X,V), not holds (X,V,T).

% preconditions
:- occurs(A,T),    precondition(A,X,V), not holds'(X,V,T).

% inertia
:- holds(X,V,T), not holds'(X,V,T), time(T),
   not occurs(A,T) : postcondition(A,_,X,V).

% existence and uniqueness of value
:- not 1 { holds(X,V,T) } 1, variable(X), time(T).

% mutexes
:- 2 #sum { 1,X,V: holds(X,V,T), contains(G,X,V) }, mutex(G), time(T).


%
% Additional rules
%

% open holds'
{ holds'(X,V,T) } :- contains(X,V), time(T).
% holds' at T is equivalent to holds at T-1 (when step at T is true)
:- holds'(X,V,T), not holds(X,V,T-1), step(T).
:- not holds'(X,V,T), holds(X,V,T-1), step(T).
% open step
{ step(T) } :- time(T).


%
% Define assumptions
%

% initial state
assumption(holds(X,V,0), true) :-     initialState(X,V).
assumption(holds(X,V,0),false) :- not initialState(X,V), contains(X,V).
% goal
assumption(holds(X,V,horizon),true) :- goal(X,V).
% step
assumption(step(T),true) :- time(T).
