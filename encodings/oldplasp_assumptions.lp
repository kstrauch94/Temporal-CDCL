#const horizon = 30.
time(0..horizon).

% Initial situation

{ holds(X,V,0) } :- contains(X,V).

% actions
1 { occurs(A,T) : action(A) } 1 :- time(T), T > 0.

% effects
holds(X,V,T):- occurs(A,T), postcondition(A,_,X,V), time(T), T > 0.

% preconditions
:- occurs(A,T), precondition(A,X,V), not holds'(X,V,T), time(T), T > 0.

% inertia
%:- holds(X,V,T), not holds(X,V,T-1), time(T),
%   not occurs(A,T) : postcondition(A,_,X,V).
%holds(X,V,T) :- holds'(X,V,T), not occurs(A,T) : postcondition(A,_,X,V2), V != V2 ; time(T), T > 0.

del(X,V,T) :- holds'(X,V,T), occurs(A,T), postcondition(A,_,X,V2), V2 != V, time(T), T > 0.
holds(X,V,T) :- holds'(X,V,T), not del(X,V,T), time(T), T > 0.

% existence and uniqueness of value
%:- not 1 { holds(X,V,T) } 1, variable(X), time(T).

%
% Additional rules
%

% open holds'
{ holds'(X,V,T) } :- contains(X,V), time(T), T > 0.
% holds' at T is equivalent to holds at T-1 (when otime at T is true)
:- holds'(X,V,T), not holds(X,V,T-1), otime(T).
:- not holds'(X,V,T), holds(X,V,T-1), otime(T).
% open otime
{ otime(T) } :- time(T).


%
% Define assumptions
%

% initial state
assumption(holds(X,V,0), true) :-     initialState(X,V).
assumption(holds(X,V,0),false) :- not initialState(X,V), contains(X,V).
% goal
assumption(holds(X,V,horizon),true) :- goal(X,V).
% otime
assumption(otime(T),true) :- time(T).