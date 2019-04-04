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

time(0..degree+1).

first(0).
last(T) :- time(T), not time(T+1).

next(T-1, T) :- time(T), T>0.
#external external(next(X,Y)) : next(X,Y).

peg(1..4).
realdisk(N) :- disk(N), not peg(N).
% M is on N
on_domain(N,M) :- disk(N), realdisk(M), N < M.

% for each non peg, choose a position
1{on(N,M,T) : on_domain(N,M)} 1 :- realdisk(M), first(T).

% Specify valid arrangements of disks
% Basic condition. Smaller disks are on larger ones

:- time(T), on(N1,N,T), N1>=N.

% Specify a valid move (only for T < t)
% pick a disk to move

{ occurs(some_action,T) } :- time(T), not first(T).
1 { move(N,T) : disk(N) } 1 :- occurs(some_action,T).

% pick a disk onto which to move
1 { where(N,T) : disk(N) }1 :- occurs(some_action,T).

% pegs cannot be moved
:- move(N,T), N < 5.

% only top disk can be moved
:- on'(N,N1,T), move(N,T).

% a disk can be placed on top only.
:- on'(N,N1,T), where(N,T).

% no disk is moved in two consecutive moves
:- move(N,T), move'(N,T).

% Specify effects of a move
on(N1,N,T) :- move(N,T), where(N1,T).
on(N,N1,T) :- not first(T),
              on'(N,N1,T), not move(N1,T).

{ on'(N,M,T) } :- on_domain(N,M), time(T), not first(T).
:- on'(N,M,T), not on(N,M,TM1), not external(next(TM1, T)), next(TM1, T).
:- not on'(N,M,T), on(N,M,TM1), not external(next(TM1, T)), next(TM1, T).

{ move'(N,T) } :- disk(N), time(T), not first(T).
:- move'(N,T), not move(N,TM1), not external(next(TM1, T)), next(TM1, T).
:- not move'(N,T), move(N,TM1), not external(next(TM1, T)), next(TM1, T).


