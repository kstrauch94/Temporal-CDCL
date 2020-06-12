#const imax = horizon.

#program base.

% Horizon, must be defined externally
%time(0..horizon).

fluent(F) :- init(F).
fluent(F) :- adds(A,F).

% initial state
assumption_init(holds(F, 0), true) :-     init(F).
assumption_init(holds(F, 0),false) :- not init(F), fluent(F).

% goal
assumption_goal(holds(F),V) :- goal(F,V).

domain_holds(F) :- fluent(F).

% Establish initial state
fluent(F) :- init(F).
fluent(F) :- adds(A,F).
{ holds(F, 0) } :- fluent(F).


#program step(t).
% Perform actions
1 {apply(A, t) : action(A)} 1.

% Check preconditions
:- apply(A, t), demands(A, F, true), not holds'(F, t).
:- apply(A, t), demands(A, F, false), holds'(F, t).

% Apply effects
holds(F, t) :- apply(A, t), adds(A, F), action(A).
del(F, t) :- apply(A, t), deletes(A, F), action(A).
holds(F, t) :- holds'(F, t), not del(F, t).
