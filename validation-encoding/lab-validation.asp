time(1..degree+1).

last(T) :- time(T), not time(T+1).

dir(e). dir(w). dir(n). dir(s).
inverse(e,w). inverse(w,e).
inverse(n,s). inverse(s,n).

row(X) :- field(X,Y).
col(Y) :- field(X,Y).

num_rows(X) :- row(X), not row(XX), XX = X+1.
num_cols(Y) :- col(Y), not col(YY), YY = Y+1.

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


{goal(X,Y,0) : domain_goal(X,Y)}.

reach_init(X,Y,0) :- init_on(X,Y).
reach_init(X,Y,0) :- reach_init(XX,YY,0), dneighbor(D,XX,YY,X,Y), conn(XX,YY,D,0), conn(X,Y,E,0), inverse(D,E).
{reach(X,Y,0): domain_reach(X,Y)}.

{conn(X,Y,D,0) : domain_conn(X,Y,D)}.

%%  Select a row or column to push

neg_goal(T) :- goal(X,Y,T), not reach(X,Y,T).

{ occurs(some_action,T) } :- time(T).
rrpush(T)   :- neg_goal'(T), not ccpush(T), occurs(some_action,T).
ccpush(T)   :- neg_goal'(T), not rrpush(T), occurs(some_action,T).

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

conn(X,Y,D,T) :- conn'(XX,YY,D,T), dir(D), shift(XX,YY,X,Y,T).

%%  Location of goal after pushing

goal(X,Y,T) :- goal'(XX,YY,T), shift(XX,YY,X,Y,T).

%%  Locations reachable from new position

reach(X,Y,T) :- reach'(XX,YY,T), shift(XX,YY,X,Y,T).
reach(X,Y,T) :- reach(XX,YY,T), dneighbor(D,XX,YY,X,Y), conn(XX,YY,D,T), conn(X,Y,E,T), inverse(D,E).


{ neg_goal'(T) } :- time(T), T>0.
:- neg_goal'(T), not neg_goal(T-1), otime(T).
:- not neg_goal'(T), neg_goal(T-1), otime(T).

domain_conn(X,Y,D) :- field(X,Y), dir(D).
{ conn'(X,Y,D,T) } :- domain_conn(X,Y,D), time(T), T>0.
:- conn'(X,Y,D,T), not conn(X,Y,D,T-1), otime(T).
:- not conn'(X,Y,D,T), conn(X,Y,D,T-1), otime(T).

domain_goal(X,Y) :- field(X,Y).
{ goal'(X,Y,T) } :- field(X,Y), time(T), T>0.
:- goal'(X,Y,T), not goal(X,Y,T-1), otime(T).
:- not goal'(X,Y,T), goal(X,Y,T-1), otime(T).

domain_reach(X,Y) :- field(X,Y).
{ reach'(X,Y,T) } :- field(X,Y), time(T), T>0.
:- reach'(X,Y,T), not reach(X,Y,T-1), otime(T).
:- not reach'(X,Y,T), reach(X,Y,T-1), otime(T).

{ otime(T) } :- time(T).

% otime
assumption(otime(T),true) :- time(T).