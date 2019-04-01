
time(s(0..degree+1)).

first(s(0)).
last(s(T)) :- time(s(T)), not time(s(T+1)).

next(s(T-1), s(T)) :- time(s(T)), T>0.
#external external(next(X,Y)) : next(X,Y).

mutex(G,X) :- mutexGroup(G), contains(G,X,V). %, fluent(X,V).
mutex(G)   :- mutexGroup(G), #count{X : mutex(G,X)} > 1.

% generate (a SAT problem)
{ holds(X,V,T) } :- contains(X,V), time(T).
{ occurs(A,T) : action(A) }  :- time(T).

% at most one action
:- 2{occurs(A,T) : action(A)}, time(T).

% effects
%:- occurs(A,T), postcondition(A,_,X,V), not holds(X,V,T).
holds(X,V,T) :- occurs(A,T), postcondition(A,_,X,V).

% preconditions
%:- occurs(A,s(T)), precondition(A,X,V), not prev_holds(X,V,s(T)).

prev_holds(X,V,s(T)) :- occurs(A,s(T)), precondition(A,X,V).


% inertia
%:- holds(X,V,s(T)), not holds(X,V,s(T-1)), 
%   not occurs(A,s(T)) : postcondition(A,_,X,V)  ; not external(next(s(T-1), s(T))), next(s(T-1), s(T)).

holds(X,V,T) :- prev_holds(X,V,T), not occurs(A,T) : postcondition(A,_,X,V2), V2 != V; not first(T).

% existence and uniqueness of value
:- not 1 { holds(X,V,T) } 1, variable(X), time(T).

% mutexes
:- 2 #sum { 1,X,V: holds(X,V,T), contains(G,X,V) }, mutex(G), time(T).

{ prev_holds(X,V,T) } :- contains(X,V), time(T), not first(T).
:- prev_holds(X,V,T), not holds(X,V,TM1), not external(next(TM1,T)), next(TM1,T).
:- not prev_holds(X,V,T), holds(X,V,TM1), not external(next(TM1,T)), next(TM1,T).