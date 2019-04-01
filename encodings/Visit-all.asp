time(s(T)) :- step(T).
max(T) :- time(s(T)), not time(s(T+1)).

first(s(0)).
last(s(T)) :- max(T).

next(s(T-1), s(T)) :- time(s(T)), T>0.
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

move(C,N,T) :- prev_atrobot(C,T), atrobot(N,T), connected(C,N), C != N, time(T).
done(T)     :- move(C,N,T), time(T).

:- time(T), not done(T), occurs(some_action,T).

visited(X,T) :- prev_visited(X,T), time(T).
visited(X,T) :- atrobot(X,T), time(T).


{ prev_atrobot(X,T) } :- loc(X), time(T), not first(T).
:- prev_atrobot(X,T), not atrobot(X,TM1), not external(next(TM1, T)), next(TM1, T).
:- not prev_atrobot(X,T), atrobot(X,TM1), not external(next(TM1, T)), next(TM1, T).

{ prev_visited(X,T) } :- loc(X), time(T), not first(T).
:- prev_visited(X,T), not visited(X,TM1), not external(next(TM1, T)), next(TM1, T).
:- not prev_visited(X,T), visited(X,TM1), not external(next(TM1, T)), next(TM1, T).