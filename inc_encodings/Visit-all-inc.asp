#program base.

assumption_init(atrobot(X,0), true) :- at(X).
assumption_init(atrobot(X,0),false) :- not at(X), domain_atrobot(X).

assumption_goal(visited(X), true) :- visit(X).

loc(X) :- at(X).
loc(X) :- loc(XX), connected(XX,X).
loc(X) :- loc(XX), connected(X,XX).

domain_atrobot(X) :- loc(X).
domain_visited(X) :- loc(X).

{atrobot(X,0)} :- domain_atrobot(X).

#program step(t).

{ occurs(some_action,t) }.
atrobot(N,t) :- connected(C,N), C != N, not atother(N,t),     occurs(some_action,t).
atother(N,t) :- connected(C,N), C != N, atrobot(O,t), O != N, occurs(some_action,t).

%1 <= { atrobot( Nextpos,T ) : connected( Curpos,Nextpos ), Curpos != Nextpos } <= 1 :- T=t.

move(C,N,t) :- atrobot'(C,t), atrobot(N,t), connected(C,N), C != N.
done(t)     :- move(C,N,t).

:- not done(t), occurs(some_action,t).

visited(X,t) :- visited'(X,t).
visited(X,t) :- atrobot(X,t).
