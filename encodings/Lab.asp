time(S) :- max_steps(S),     0 < S.
time(T) :- time(S), T = S-1, 1 < S.

first(0).
last(T) :- time(T), not time(T+1).

next(T-1,T) :- time(T), T>0.
#external external(next(X,Y)) : next(X,Y).


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


% set initial state
#external external(goal(X,Y,T)) : goal_on(X,Y), first(T).
:- not goal(X,Y,T), not external(goal(X,Y,T)), goal_on(X,Y), first(T).

% set initial state
#external external(reach_init(X,Y,T)) : init_on(X,Y), first(T).
:- not reach_init(X,Y,T), not external(reach_init(X,Y,T)), init_on(X,Y), first(T).

domain_conn(X,Y,D) :- field(X,Y), dir(D).

% set initial state
#external external(conn(X,Y,D,T)) : connect(X,Y,D), first(T).
:- not conn(X,Y,D,T), not external(conn(X,Y,D,T)), connect(X,Y,D), first(T).

% conn not in init state is false
#external false_external(conn(X,Y,D,T)) : not connect(X,Y,D), domain_conn(X,Y,D), first(T).
:- conn(X,Y,D,T), not false_external(conn(X,Y,D,T)), not connect(X,Y,D), domain_conn(X,Y,D), first(T).

%reach is expanded on a later rule so we can't set upper limit to 1
1 {goal(X,Y,T) : field(X,Y)} 1  :-  first(T).
1 {reach_init(X,Y,T): field(X,Y)} 1  :- first(T).
reach(X,Y,T) :- reach_init(X,Y,T).

{conn(X,Y,D,T) : domain_conn(X,Y,D)} :-  first(T).

%{goal(X,Y,T)}   :- goal_on(X,Y), first(T).
%{reach_init(X,Y,T)}  :- init_on(X,Y), first(T).
%{conn(X,Y,D,T)} :- connect(X,Y,D), first(T).

% set goal
#external external(neg_goal(T)) : last(T).
:- neg_goal(T), not external(neg_goal(T)), last(T).


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


{ neg_goal'(T) } :- time(T), not first(T).
:- neg_goal'(T), not neg_goal(TM1), not external(next(TM1, T)), next(TM1, T).
:- not neg_goal'(T), neg_goal(TM1), not external(next(TM1, T)), next(TM1, T).

{ conn'(X,Y,D,T) } :- domain_conn(X,Y,D), time(T), not first(T).
:- conn'(X,Y,D,T), not conn(X,Y,D,TM1), not external(next(TM1, T)), next(TM1, T).
:- not conn'(X,Y,D,T), conn(X,Y,D,TM1), not external(next(TM1, T)), next(TM1, T).

{ goal'(X,Y,T) } :- field(X,Y), time(T), not first(T).
:- goal'(X,Y,T), not goal(X,Y,TM1), not external(next(TM1, T)), next(TM1, T).
:- not goal'(X,Y,T), goal(X,Y,TM1), not external(next(TM1, T)), next(TM1, T).

{ reach'(X,Y,T) } :- field(X,Y), time(T), not first(T).
:- reach'(X,Y,T), not reach(X,Y,TM1), not external(next(TM1, T)), next(TM1, T).
:- not reach'(X,Y,T), reach(X,Y,TM1), not external(next(TM1, T)), next(TM1, T).
