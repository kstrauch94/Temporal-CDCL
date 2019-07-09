% Horizon, must be defined externally
time(0..degree+1).

% Establish initial state
fluent(F) :- init(F).
fluent(F) :- adds(A,F).
{ holds(F, 0) } :- fluent(F).

% Perform actions
1 {apply(A, T) : action(A)} 1 :- time(T), T > 0.

% Check preconditions
:- apply(A, T), demands(A, F, true), not holds'(F, T), time(T), time(T - 1).
:- apply(A, T), demands(A, F, false), holds'(F, T), time(T), time(T - 1).

% Apply effects
holds(F, T) :- apply(A, T), adds(A, F), action(A), time(T).
del(F, T) :- apply(A, T), deletes(A, F), action(A), time(T).
holds(F, T) :- holds'(F, T), not del(F, T), time(T), time(T - 1).

% Verify that goal is met
%:- goal(F, true), not holds(F, horizon).
%:- goal(F, false), holds(F, horizon).

% open holds'
{ holds'(F,T) } :- fluent(F), time(T), T > 0.
% holds' at T is equivalent to holds at T-1 (when otime at T is true)
:- holds'(F,T), not holds(F,T-1), otime(T).
:- not holds'(F,T), holds(F,T-1), otime(T).
% open otime
otime(T) :- time(T), T > 0.


