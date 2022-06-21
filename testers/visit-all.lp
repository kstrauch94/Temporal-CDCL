time(0).
:- atrobot(X,0), at(X).

loc(X) :- at(X).
loc(X) :- connected(XX,X).
loc(X) :- connected(X,XX).

{ atrobot(X,T-1) } :- loc(X), time(T).

{ visited(X,T-1) } :- loc(X), time(T).

{ occurs(some_action,T) } :- time(T).
atrobot(N,T) :- connected(C,N), C != N, time(T), not atother(N,T),     occurs(some_action,T).
atother(N,T) :- connected(C,N), C != N, time(T), atrobot(O,T), O != N, occurs(some_action,T).

move(C,N,T) :- atrobot(C,T-1), atrobot(N,T), connected(C,N), C != N, time(T).
done(T)     :- move(C,N,T), time(T).

:- time(T), not done(T), occurs(some_action,T).

visited(X,T) :- visited(X,T-1), time(T).
visited(X,T) :- atrobot(X,T), time(T).

%:- visit(X), not visited(X,T), time(T), not time(T+1).

#show atrobot/2.