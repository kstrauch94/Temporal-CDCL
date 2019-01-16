time(s(T)) :- step(T).
max(T) :- time(s(T)), not time(s(T+1)).

next(s(T-1), s(T)) :- time(s(T)), T>0.
#external external(next(X,Y)) : next(X,Y).


#external external(atrobot(X,s(0))) : at(X).
:- not atrobot(X,s(0)), not external(atrobot(X,s(0))) , at(X).

{atrobot(X,s(0))} :- at(X).

%#external external(visited(X,s(T))) : visit(X), max(T).
%:- not visited(X,s(T)), not external(visited(X,s(T))) , visit(X), max(T).

%{visited(X,s(T))} :- visit(X), max(T).

{ occurs(some_action,T) } :- time(T).
atrobot(N,T) :- connected(C,N), C != N, time(T), not atother(N,T),     occurs(some_action,T).
atother(N,T) :- connected(C,N), C != N, time(T), atrobot(O,T), O != N, occurs(some_action,T).

%1 <= { atrobot( Nextpos,T ) : connected( Curpos,Nextpos ), Curpos != Nextpos } <= 1 :- T=t.

move(C,N,T) :- prev_atrobot(C,T), atrobot(N,T), connected(C,N), C != N, time(T).
done(T)     :- move(C,N,T), time(T).

:- time(T), not done(T), occurs(some_action,T).

visited(X,T) :- prev_visited(X,T), time(T).
visited(X,T) :- atrobot(X,T), time(T).

:- visit(X), not visited(X,s(T)), max(T).


loc(X) :- connected(X,_).
loc(X) :- connected(_,X).

{ prev_atrobot(X,s(T)) } :- loc(X), time(s(T)), T > 0.
:- prev_atrobot(X,s(T)), not atrobot(X,s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).
:- not prev_atrobot(X,s(T)), atrobot(X,s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).

{ prev_visited(X,s(T)) } :- loc(X), time(s(T)), T > 0.
:- prev_visited(X,s(T)), not visited(X,s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).
:- not prev_visited(X,s(T)), visited(X,s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).
