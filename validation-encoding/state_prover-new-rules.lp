
time(0..degree+1).

first(0).
last(degree+1).

next(T-1,T) :- time(T), T>0.
#external external(next(X,Y)) : next(X,Y).

mutex(G,X) :- mutexGroup(G), contains(G,X,V). %, fluent(X,V).
mutex(G)   :- mutexGroup(G), #count{X : mutex(G,X)} > 1.

% generate (a SAT problem)
{ holds(X,V,T) } :- contains(X,V), time(T).
{ occurs(A,T) : action(A) }  :- time(T).

% at most one action
:- 2{occurs(A,T) : action(A)}, time(T).

% effects
:- occurs(A,T), postcondition(A,_,X,V), not holds(X,V,T).

% preconditions
:- occurs(A,T), precondition(A,X,V), not holds'(X,V,T).

% inertia
:- holds(X,V,T), not holds'(X,V,T), 
   not occurs(A,T) : postcondition(A,_,X,V)  ; not external(next(T-1,T)), next(T-1,T).

% existence and uniqueness of value
:- not 1 { holds(X,V,T) } 1, variable(X), time(T).

% mutexes
:- 2 #sum { 1,X,V: holds(X,V,T), contains(G,X,V) }, mutex(G), time(T).

{ holds'(X,V,T) } :- contains(X,V), time(T).
% holds' at T is equivalent to holds at T-1 (when step at T is true)
:- holds'(X,V,T), not holds(X,V,T-1), step(T).
:- not holds'(X,V,T), holds(X,V,T-1), step(T).

step(T) :- time(T).
