time(s(1..degree+1)).

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


domain_conn(X,Y,D) :- field(X,Y), dir(D).

1 {goal(X,Y,T) : field(X,Y)} 1  :-  first(T).
1 {reach_init(X,Y,T): field(X,Y)} 1  :- first(T).
reach(X,Y,T) :- reach_init(X,Y,T).

%{conn(X,Y,D,T) : field(X,Y), dir(D)} :-  first(T).

%{goal(X,Y,T)}   :- goal_on(X,Y), first(T).
%{reach(X,Y,T)}  :- init_on(X,Y), first(T).
%{conn(X,Y,D,T)} :- connect(X,Y,D), first(T).
conn(X,Y,D,T) :- connect(X,Y,D), first(T).

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



{ prev_neg_goal(T) } :- time(T), not first(T).
:- prev_neg_goal(T), not neg_goal(TM1), not external(next(TM1, T)), next(TM1, T).
:- not prev_neg_goal(T), neg_goal(TM1), not external(next(TM1, T)), next(TM1, T).

{ prev_conn(X,Y,D,T) } :- domain_conn(X,Y,D), time(T), not first(T).
:- prev_conn(X,Y,D,T), not conn(X,Y,D,TM1), not external(next(TM1, T)), next(TM1, T).
:- not prev_conn(X,Y,D,T), conn(X,Y,D,TM1), not external(next(TM1, T)), next(TM1, T).

{ prev_goal(X,Y,T) } :- field(X,Y), time(T), not first(T).
:- prev_goal(X,Y,T), not goal(X,Y,TM1), not external(next(TM1, T)), next(TM1, T).
:- not prev_goal(X,Y,T), goal(X,Y,TM1), not external(next(TM1, T)), next(TM1, T).

{ prev_reach(X,Y,T) } :- field(X,Y), time(T), not first(T).
:- prev_reach(X,Y,T), not reach(X,Y,TM1), not external(next(TM1, T)), next(TM1, T).
:- not prev_reach(X,Y,T), reach(X,Y,TM1), not external(next(TM1, T)), next(TM1, T).

%% uncomment to test
% and run this encoding with asp-planning-benchmarks/Labyrinth/0045-labyrinth-11-0.asp 
% clingo validation-encoding/lab-validation.asp asp-planning-benchmarks/Labyrinth/0045-labyrinth-11-0.asp 

%#const degree=0.
%hypothesisConstraint(s(T-degree)) :- shift(2,10,2,1,s(T)), prev_goal(1,2,s(T)), not prev_reach(10,2,s(T)), not prev_reach(2,2,s(T)), not prev_reach(1,2,s(T)), not conn(1,2,w,s(T)), not prev_reach(1,1,s(T)), not prev_conn(1,2,e,s(T)), not prev_reach(1,3,s(T)), not prev_conn(1,2,s,s(T)), not prev_conn(2,1,s,s(T)), not shift(2,1,2,10,s(T)), T-0 > 0, time(s(T)).
%:- not hypothesisConstraint(s(1)).
