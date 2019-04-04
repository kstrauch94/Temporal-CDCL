time(T) :- step(T).
max(T) :- time(T), not time(T+1).

first(0).
last(T) :- max(T).

next(T-1,T) :- time(T), T>0.
#external external(next(X,Y)) : next(X,Y).


#external external(atrobot(X,T)) : at(X), first(T).
:- not atrobot(X,T), not external(atrobot(X,T)), at(X), first(T).

#external external(visited(X,T)) : visit(X), last(T).
:- not visited(X,T), not external(visited(X,T)), visit(X), last(T).

loc(X) :- at(X).
loc(X) :- loc(XX), connected(XX,X).
loc(X) :- loc(XX), connected(X,XX).

1{atrobot(X,T)}1 :- loc(X), first(T).

%%%%%%%%%%%%%%%
%%%
%%%%%%%%%%%%%%%

{ occurs(some_action,T) } :- time(T).
atrobot(N,T) :- connected(C,N), C != N, time(T), not atother(N,T),     occurs(some_action,T).
atother(N,T) :- connected(C,N), C != N, time(T), atrobot(O,T), O != N, occurs(some_action,T).

%1 <= { atrobot( Nextpos,T ) : connected( Curpos,Nextpos ), Curpos != Nextpos } <= 1 :- T=t.

move(C,N,T) :- atrobot'(C,T), atrobot(N,T), connected(C,N), C != N, time(T).
done(T)     :- move(C,N,T), time(T).

:- time(T), not done(T), occurs(some_action,T).

visited(X,T) :- visited'(X,T), time(T).
visited(X,T) :- atrobot(X,T), time(T).


{ atrobot'(X,T) } :- loc(X), time(T), not first(T).
:- atrobot'(X,T), not atrobot(X,TM1), not external(next(TM1, T)), next(TM1, T).
:- not atrobot'(X,T), atrobot(X,TM1), not external(next(TM1, T)), next(TM1, T).

{ visited'(X,T) } :- loc(X), time(T), not first(T).
:- visited'(X,T), not visited(X,TM1), not external(next(TM1, T)), next(TM1, T).
:- not visited'(X,T), visited(X,TM1), not external(next(TM1, T)), next(TM1, T).