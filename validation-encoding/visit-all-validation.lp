time(1..degree+1).
max(T) :- time(T), not time(T+1).

last(T) :- max(T).

loc(X) :- at(X).
loc(X) :- connected(XX,X).
loc(X) :- connected(X,XX).

% generate all possible initial states
{atrobot(X,0) : loc(X)}.


{ occurs(some_action,T) } :- time(T).
atrobot(N,T) :- connected(C,N), C != N, time(T), not atother(N,T),     occurs(some_action,T).
atother(N,T) :- connected(C,N), C != N, time(T), atrobot(O,T), O != N, occurs(some_action,T).

%1 <= { atrobot( Nextpos,T ) : connected( Curpos,Nextpos ), Curpos != Nextpos } <= 1 :- T=t.

move(C,N,T) :- atrobot'(C,T), atrobot(N,T), connected(C,N), C != N, time(T).
done(T)     :- move(C,N,T), time(T).

:- time(T), not done(T), occurs(some_action,T).

visited(X,T) :- visited'(X,T), time(T).
visited(X,T) :- atrobot(X,T), time(T).


{ atrobot'(X,T) } :- loc(X), time(T), T > 0.
:- atrobot'(X,T), not atrobot(X,T-1), otime(T).
:- not atrobot'(X,T), atrobot(X,T-1), otime(T).

{ visited'(X,T) } :- loc(X), time(T), T > 0.
:- visited'(X,T), not visited(X,T-1), otime(T).
:- not visited'(X,T), visited(X,T-1), otime(T).

{ otime(T) } :- time(T).

% otime
assumption(otime(T),true) :- time(T).
