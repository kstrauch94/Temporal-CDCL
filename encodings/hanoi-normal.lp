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

last(T) :- time(T), not time(T+1).

time(T) :- timestep(T).

peg(1..4).
realdisk(N) :- disk(N), not peg(N).
% M is on N

on(N1,N,0) :- on0(N,N1).
% Specify valid arrangements of disks
% Basic condition. Smaller disks are on larger ones

:- time(T), on(N1,N,T), N1>=N.

% Specify a valid move (only for T < t)
% pick a disk to move

{ occurs(some_action,T) } :- time(T), T > 0.
1 { move(N,T) : disk(N) } 1 :- occurs(some_action,T).

% pick a disk onto which to move
1 { where(N,T) : disk(N) }1 :- occurs(some_action,T).

% pegs cannot be moved
:- move(N,T), N < 5.

% only top disk can be moved
:- on(N,N1,T-1), move(N,T).

% a disk can be placed on top only.
:- on(N,N1,T-1), where(N,T).

% no disk is moved in two consecutive moves
:- move(N,T), move(N,T-1), time(T).

% Specify effects of a move
on(N1,N,T) :- move(N,T), where(N1,T).
on(N,N1,T) :- T > 0,
              on(N,N1,T-1), not move(N1,T), time(T).

% Goal description
:- not on(N,N1,T), ongoal(N1,N), last(T).
:- on(N,N1,T), not ongoal(N1,N), last(T).
