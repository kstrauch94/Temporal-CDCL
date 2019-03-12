max_steps(degree).

time(s(S)) :- max_steps(S),     0 < S.
time(s(T)) :- time(s(S)), T = S-1, 1 < S.

first(s(0)).
last(s(T)) :- time(s(T)), not time(s(T+1)).

next(s(T-1), s(T)) :- time(s(T)), T>0.
#external external(next(X,Y)) : next(X,Y).


dir(e). dir(w). dir(n). dir(s).
inverse(e,w). inverse(w,e).
inverse(n,s). inverse(s,n).

row(X) :- field(X,Y).
col(Y) :- field(X,Y).

num_rows(X) :- row(X), not row(XX), XX = X+1.
num_cols(Y) :- col(Y), not col(YY), YY = Y+1.

reachable(X,Y) :- init_on(X,Y).
reachable(XX,YY) :- reachable(X,Y), dneighbor(D,X,Y,XX,YY), connect(X,Y,D).

% since the goal is not relevant for state validation nothing was changed for it
1{goal(X,Y,T)}1   :- goal_on(X,Y), first(T).

% the initial reach is chosen from any point reachable from the first state
% to avoid starting in impossible states
1{reach(X,Y,T)}1  :- reachable(X,Y), first(T).

% connections are kept the same since we only care about validating on this specific instances no matter the starting point
{conn(X,Y,D,T)} :- connect(X,Y,D), first(T).

%%  Direct neighbors

dneighbor(n,X,Y,XX,Y) :- field(X,Y), field(XX,Y), XX = X+1.
dneighbor(s,X,Y,XX,Y) :- field(X,Y), field(XX,Y), XX = X-1.
dneighbor(e,X,Y,X,YY) :- field(X,Y), field(X,YY), YY = Y+1.
dneighbor(w,X,Y,X,YY) :- field(X,Y), field(X,YY), YY = Y-1.

%%  All neighboring fields

neighbor(D,X,Y,XX,YY) :- dneighbor(D,X,Y,XX,YY).
neighbor(n,X,Y, 1, Y) :- field(X,Y), num_rows(X).
neighbor(s,1,Y, X, Y) :- field(X,Y), num_rows(X).
neighbor(e,X,Y, X, 1) :- field(X,Y), num_cols(Y).
neighbor(w,X,1, X, Y) :- field(X,Y), num_cols(Y).


%%  Select a row or column to push

neg_goal(T) :- goal(X,Y,T), not reach(X,Y,T).

{ occurs(some_action,T) } :- time(T).
rrpush(T)   :- prev_neg_goal(T), not ccpush(T), occurs(some_action,T).
ccpush(T)   :- prev_neg_goal(T), not rrpush(T), occurs(some_action,T).

orpush(X,T) :- row(X), row(XX), rpush(XX,T), X != XX.
ocpush(Y,T) :- col(Y), col(YY), cpush(YY,T), Y != YY.

rpush(X,T)  :- row(X), rrpush(T), not orpush(X,T).
cpush(Y,T)  :- col(Y), ccpush(T), not ocpush(Y,T).

push(X,e,T) :- rpush(X,T), not push(X,w,T).
push(X,w,T) :- rpush(X,T), not push(X,e,T).
push(Y,n,T) :- cpush(Y,T), not push(Y,s,T).
push(Y,s,T) :- cpush(Y,T), not push(Y,n,T).

%%  Determine new position of a (pushed) field

shift(XX,YY,X,Y,T) :- neighbor(e,XX,YY,X,Y), push(XX,e,T).
shift(XX,YY,X,Y,T) :- neighbor(w,XX,YY,X,Y), push(XX,w,T).
shift(XX,YY,X,Y,T) :- neighbor(n,XX,YY,X,Y), push(YY,n,T).
shift(XX,YY,X,Y,T) :- neighbor(s,XX,YY,X,Y), push(YY,s,T).
shift( X, Y,X,Y,T) :- time(T), field(X,Y), not push(X,e,T), not push(X,w,T), not push(Y,n,T), not push(Y,s,T).

%%  Move connections around

conn(X,Y,D,T) :- prev_conn(XX,YY,D,T), dir(D), shift(XX,YY,X,Y,T).

%%  Location of goal after pushing

goal(X,Y,T) :- prev_goal(XX,YY,T), shift(XX,YY,X,Y,T).

%%  Locations reachable from new position

reach(X,Y,T) :- prev_reach(XX,YY,T), shift(XX,YY,X,Y,T).
reach(X,Y,T) :- reach(XX,YY,T), dneighbor(D,XX,YY,X,Y), conn(XX,YY,D,T), conn(X,Y,E,T), inverse(D,E).

{ prev_neg_goal(s(T)) } :- time(s(T)), T > 0.
:- prev_neg_goal(s(T)), not neg_goal(s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).
:- not prev_neg_goal(s(T)), neg_goal(s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).

domain_conn(X,Y,D) :- field(X,Y), dir(D).
{ prev_conn(X,Y,D,s(T)) } :- domain_conn(X,Y,D), time(s(T)), T > 0.
:- prev_conn(X,Y,D,s(T)), not conn(X,Y,D,s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).
:- not prev_conn(X,Y,D,s(T)), conn(X,Y,D,s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).

{ prev_goal(X,Y,s(T)) } :- field(X,Y), time(s(T)), T > 0.
:- prev_goal(X,Y,s(T)), not goal(X,Y,s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).
:- not prev_goal(X,Y,s(T)), goal(X,Y,s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).

{ prev_reach(X,Y,s(T)) } :- field(X,Y), time(s(T)), T > 0.
:- prev_reach(X,Y,s(T)), not reach(X,Y,s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).
:- not prev_reach(X,Y,s(T)), reach(X,Y,s(T-1)), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).


:- not hypothesisConstraint(s(0)).