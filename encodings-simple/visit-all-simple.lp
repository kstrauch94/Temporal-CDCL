time(T) :- step(T).

last(T) :- time(T), not time(T+1).

loc(X) :- at(X).
loc(X) :- connected(XX,X).
loc(X) :- connected(X,XX).


{atrobot(X,0) : loc(X)}.

{ occurs(some_action,T) } :- step(T).
atrobot(N,T) :- connected(C,N), C != N, step(T), not atother(N,T),     occurs(some_action,T).
atother(N,T) :- connected(C,N), C != N, step(T), atrobot(O,T), O != N, occurs(some_action,T).

move(C,N,T) :- atrobot(C,T-1), atrobot(N,T), connected(C,N), C != N, step(T).
done(T)     :- move(C,N,T), step(T).

:- step(T), not done(T), occurs(some_action,T).

visited(X,T) :- visited(X,T-1), step(T).
visited(X,T) :- atrobot(X,T), step(T).

% initial state
assumption(atrobot(X,0), true) :-     at(X).
assumption(atrobot(X,0),false) :- not at(X), loc(X).

% goal
assumption(visited(X,T), true) :- visit(X), last(T).