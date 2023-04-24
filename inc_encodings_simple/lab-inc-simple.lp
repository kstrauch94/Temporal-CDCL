#program base.

% initial state
assumption_init(goal(X,Y,0), true) :-     goal_on(X,Y).
assumption_init(goal(X,Y,0),false) :- not goal_on(X,Y), dom_goal(X,Y).

assumption_init(reach(X,Y,0), true) :-     reach_init(X,Y).
assumption_init(reach(X,Y,0),false) :- not reach_init(X,Y), dom_reach(X,Y).

assumption_init(conn(X,Y,D,0), true) :-     connect(X,Y,D).
assumption_init(conn(X,Y,D,0),false) :- not connect(X,Y,D), dom_conn(X,Y,D).

% goal
assumption_goal(neg_goal,false).

% Domains for prime variables
dom_conn(X,Y,D) :- field(X,Y), dir(D).
dom_goal(X,Y) :- field(X,Y).
dom_reach(X,Y) :- field(X,Y).


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


%reach is expanded on a later rule so we can't set upper limit to 1
{goal(X,Y,0) : dom_goal(X,Y)}.

reach_init(X,Y) :- init_on(X,Y).
reach_init(X,Y) :- reach_init(XX,YY), dneighbor(D,XX,YY,X,Y), connect(XX,YY,D), connect(X,Y,E), inverse(D,E).

{reach(X,Y,0): dom_reach(X,Y)}.

{conn(X,Y,D,0) : dom_conn(X,Y,D)}.

% duplicate of neg goal rule for initial situation
% since t does not exist for time 0
neg_goal(0) :- goal(X,Y,0), not reach(X,Y,0).

% to have a complete initial state
shift( X, Y,X,Y,0) :- field(X,Y).

#program step(t).

%%  Select a row or column to push

neg_goal(t) :- goal(X,Y,t), not reach(X,Y,t).

{ occurs(some_action,t) }.
rrpush(t)   :- neg_goal(t-1), not ccpush(t), occurs(some_action,t).
ccpush(t)   :- neg_goal(t-1), not rrpush(t), occurs(some_action,t).

orpush(X,t) :- row(X), row(XX), rpush(XX,t), X != XX.
ocpush(Y,t) :- col(Y), col(YY), cpush(YY,t), Y != YY.

rpush(X,t)  :- row(X), rrpush(t), not orpush(X,t).
cpush(Y,t)  :- col(Y), ccpush(t), not ocpush(Y,t).

push(X,e,t) :- rpush(X,t), not push(X,w,t).
push(X,w,t) :- rpush(X,t), not push(X,e,t).
push(Y,n,t) :- cpush(Y,t), not push(Y,s,t).
push(Y,s,t) :- cpush(Y,t), not push(Y,n,t).

%%  Determine new position of a (pushed) field

shift(XX,YY,X,Y,t) :- neighbor(e,XX,YY,X,Y), push(XX,e,t).
shift(XX,YY,X,Y,t) :- neighbor(w,XX,YY,X,Y), push(XX,w,t).
shift(XX,YY,X,Y,t) :- neighbor(n,XX,YY,X,Y), push(YY,n,t).
shift(XX,YY,X,Y,t) :- neighbor(s,XX,YY,X,Y), push(YY,s,t).
shift( X, Y,X,Y,t) :- field(X,Y), not push(X,e,t), not push(X,w,t), not push(Y,n,t), not push(Y,s,t).

%%  Move connections around

conn(X,Y,D,t) :- conn(XX,YY,D,t-1), dir(D), shift(XX,YY,X,Y,t).

%%  Location of goal after pushing

goal(X,Y,t) :- goal(XX,YY,t-1), shift(XX,YY,X,Y,t).

%%  Locations reachable from new position

reach(X,Y,t) :- reach(XX,YY,t-1), shift(XX,YY,X,Y,t).
reach(X,Y,t) :- reach(XX,YY,t), dneighbor(D,XX,YY,X,Y), conn(XX,YY,D,t), conn(X,Y,E,t), inverse(D,E).

