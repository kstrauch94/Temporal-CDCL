#program base.

assumption_init(atrobot(X,0), true) :- at(X).
assumption_init(atrobot(X,0),false) :- not at(X), dom_atrobot(X).
assumption_init(visited(X,0),false) :- loc(X).

assumption_goal(visited(X), true) :- visit(X).

loc(X) :- at(X).
loc(X) :- loc(XX), connected(XX,X).
loc(X) :- loc(XX), connected(X,XX).

dom_atrobot(X) :- loc(X).
dom_visited(X) :- loc(X).

{atrobot(X,0) :  dom_atrobot(X)}.
{visited(X,0) :loc(X)}.

#program step(t).

{ occurs(some_action,t) }.
%inertia
atrobot(X,t) :- atrobot(X,t-1), not occurs(some_action,t).

atrobot(N,t) :- connected(C,N), C != N, not atother(N,t),     occurs(some_action,t).
atother(N,t) :- connected(C,N), C != N, atrobot(O,t), O != N, occurs(some_action,t).

%1 <= { atrobot( Nextpos,T ) : connected( Curpos,Nextpos ), Curpos != Nextpos } <= 1 :- T=t.

move(C,N,t) :- atrobot(C,t-1), atrobot(N,t), connected(C,N), C != N.
done(t)     :- move(C,N,t).

:- not done(t), occurs(some_action,t).

visited(X,t) :- visited(X,t-1).
visited(X,t) :- atrobot(X,t), occurs(some_action,t).
