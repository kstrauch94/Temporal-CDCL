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

time(s(T)) :- timestep(T).
next(s(T-1), s(T)) :- time(s(T)), T>0.
#external external(next(X,Y)) : next(X,Y).

peg(1..4).
on_domain(N,M) :- disk(N), disk(M), N < M, not peg(M).

{ prev_on(s(T),N,M) } :- on_domain(N,M), time(s(T)), T > 0.
:- prev_on(s(T),N,M), not on(s(T-1),N,M), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).
:- not prev_on(s(T),N,M), on(s(T-1),N,M), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).

{ prev_move(s(T),N) } :- disk(N), time(s(T)), T > 0.
:- prev_move(s(T),N), not move(s(T-1),N), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).
:- not prev_move(s(T),N), move(s(T-1),N), not external(next(s(T-1), s(T))), next(s(T-1), s(T)).

% Read in data
%on(s(0),N1,N) :- on0(N,N1).
%onG(K,N1,N) :- ongoal(N,N1), steps(K).

% set initial state
#external external(on(s(0),N1,N)) : on0(N,N1).
:- not on(s(0),N1,N), not external(on(s(0),N1,N)), on0(N,N1).

{on(s(0),N1,N)} :- on0(N,N1).

% Specify valid arrangements of disks
% Basic condition. Smaller disks are on larger ones

:- time(T), on(T,N1,N), N1>=N.

% Specify a valid move (only for T < t)
% pick a disk to move

{ occurs(some_action,s(T)) } :- time(s(T)), T>0.
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
on(s(T),N,N1) :- time(s(T)), T>0,
              prev_on(s(T),N,N1), not move(s(T),N1).


% Goal description
:- not on(s(T),N,N1), ongoal(N1,N), steps(T).
:- on(s(T),N,N1), not ongoal(N1,N), steps(T).

% goal must hold at the last time point
%#external external(on(s(T),N1,N)) : ongoal(N,N1), steps(T).
%:- not on(s(T),N1,N), not external(on(s(T),N1,N)), ongoal(N,N1), steps(T).

% Solution
%#show put(M,N,T) : move(T,N), where(T,M).

