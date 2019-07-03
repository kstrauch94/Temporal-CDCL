#const horizon = 30.
time(0..horizon).

% Initial situation

holds(X,V,0) :- initialState(X,V).

% actions
1 { occurs(A,T) : action(A) } 1 :- time(T), T > 0.

% effects
holds(X,V,T):- occurs(A,T), postcondition(A,_,X,V), time(T).

% preconditions
:- occurs(A,T), precondition(A,X,V), not holds(X,V,T-1), time(T), time(T-1).

% inertia
%:- holds(X,V,T), not holds(X,V,T-1), time(T),
%   not occurs(A,T) : postcondition(A,_,X,V).
%holds(X,V,T) :- holds(X,V,T-1), not occurs(A,T) : postcondition(A,_,X,V2), V != V2 ; time(T), time(T-1).

del(X,V,T) :- holds(X,V,T-1), occurs(A,T), postcondition(A,_,X,V2), V2 != V, time(T), T > 0.
holds(X,V,T) :- holds(X,V,T-1), not del(X,V,T), time(T), T > 0.

% existence and uniqueness of value
%:- not 1 { holds(X,V,T) } 1, variable(X), time(T).

% Verify that goal is met
:- goal(X,V), not holds(X,V,horizon).

#show occurs/2.