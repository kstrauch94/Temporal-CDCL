% The meaning of the time predicate is self-evident. As for the disk
% predicate, there are k disks 1,2,...,k. Disks 1, 2, 3, 4 denote pegs. 
% Disks 5, ... are "movable". The larger the number of the disk, 
% the "smaller" it is.
%
% The program uses additional predicates:
% on(T,N,M), which is true iff at time T, disk M is on disk N
% move(t,N), which is true iff at time T, it is disk N that will be
% moved
% where(T,N), which is true iff at time T, the disk to be moved is moved
% on top of the disk N.
% goal, which is true iff the goal state is reached at time t
% steps(T), which is the number of time steps T, required to reach the goal (provided part of Input data)

first(s(0)).
last(s(T)) :- time(s(T)), not time(s(T+1)).

time(s(1..degree)).

next(s(T-1), s(T)) :- time(s(T)), T>0.
#external external(next(X,Y)) : next(X,Y).

peg(1..4).
on_domain(N,M) :- disk(N), disk(M), N < M, not peg(M).

{ prev_on(T,N,M) } :- on_domain(N,M), time(T), not first(T).
:- prev_on(T,N,M), not on(TM1,N,M), not external(next(TM1, T)), next(TM1, T).
:- not prev_on(T,N,M), on(TM1,N,M), not external(next(TM1, T)), next(TM1, T).

{ prev_move(T,N) } :- disk(N), time(T), not first(T).
:- prev_move(T,N), not move(TM1,N), not external(next(TM1, T)), next(TM1, T).
:- not prev_move(T,N), move(TM1,N), not external(next(TM1, T)), next(TM1, T).

% for each non peg, choose a position
1{on(T,N,M)}1 :- on_domain(N,M), not peg(M), first(T).

% Specify valid arrangements of disks
% Basic condition. Smaller disks are on larger ones

:- time(T), on(T,N1,N), N1>=N.

% Specify a valid move (only for T < t)
% pick a disk to move

{ occurs(some_action,T) } :- time(T), not first(T).
1 { move(T,N) : disk(N) } 1 :- occurs(some_action,T).

% pick a disk onto which to move
1 { where(T,N) : disk(N) }1 :- occurs(some_action,T).

% pegs cannot be moved
:- move(T,N), N < 5.

% only top disk can be moved
:- prev_on(T,N,N1), move(T,N).

% a disk can be placed on top only.
:- prev_on(T,N,N1), where(T,N).

% no disk is moved in two consecutive moves
:- move(T,N), prev_move(T,N).

% Specify effects of a move
on(T,N1,N) :- move(T,N), where(T,N1).
on(T,N,N1) :- not first(T),
              prev_on(T,N,N1), not move(T,N1).


:- not hypothesisConstraint(s(0)).

