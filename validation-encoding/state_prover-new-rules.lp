
time(s(T)) :- T= 0..degree.

next(s(T-1), s(T)) :- time(s(T)), T>0.
#external external(next(X,Y)) : next(X,Y).

mutex(G,X) :- mutexGroup(G), contains(G,X,V). %, fluent(X,V).
mutex(G)   :- mutexGroup(G), #count{X : mutex(G,X)} > 1.



% No action can be done at time 0
%#external external(occurs(A,s(0))) : action(A).
%:-  occurs(A,s(0)), not external(occurs(A,s(0))), action(A).

% generate (a SAT problem)
{ occurs(A,T) : action(A) }  :- time(T).

{ prev_holds(X,V,s(T)) } :- contains(X,V), time(s(T)), T > 0.
:- prev_holds(X,V,s(T)), not holds(X,V,s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).
:- not prev_holds(X,V,s(T)), holds(X,V,s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).

% at most one action
:- 2{occurs(A,T) : action(A)}, time(T).

% effects
:- occurs(A,T), postcondition(A,_,X,V), not holds(X,V,T).
%holds(X,V,T) :- occurs(A,T), postcondition(A,_,X,V).

% preconditions
:- occurs(A,s(T)), precondition(A,X,V), not prev_holds(X,V,s(T)).

%prev_holds(X,V,s(T)) :- occurs(A,s(T)), precondition(A,X,V).


% inertia
:- holds(X,V,s(T)), not holds(X,V,s(T-1)), 
   not occurs(A,s(T)) : postcondition(A,_,X,V)  ; not external(next(s(T-1), s(T))), next(s(T-1), s(T)).

%holds(X,V,s(T)) :- prev_holds(X,V,s(T)), not occurs(A,s(T)) : postcondition(A,_,X,V2), V2 != V; T>0.

% existence and uniqueness of value
:- not 1 { holds(X,V,T) } 1, variable(X), time(T).

% mutexes
:- 2 #sum { 1,X,V: holds(X,V,T), contains(G,X,V) }, mutex(G), time(T).



{ holds(X,V,T) } :- contains(X,V), time(T).

:- not hypothesisConstraint(s(0)).

