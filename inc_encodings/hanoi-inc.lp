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


#program base.

peg(1..4).
realdisk(N) :- disk(N), not peg(N).
% M is on N

domain_on(N,M) :- disk(N), realdisk(M), N < M.
%domain_move(N) :- disk(N).

{on(N,M,0) : domain_on(N,M)} :- realdisk(M).

%
% Define assumptions
%

% initial state
assumption_init(on(N1,N,0), true) :-     on0(N,N1).
assumption_init(on(N1,N,0),false) :- not on0(N,N1), domain_on(N1,N).
% goal
assumption_goal(on(N1,N),true) :- ongoal(N,N1).

#program step(t).

% Specify valid arrangements of disks
% Basic condition. Smaller disks are on larger ones

:- on(N1,N,t), N1>=N.

% Specify a valid move (only for T < t)
% pick a disk to move

{ occurs(some_action,t) }.
1 { move(N,t) : disk(N) } 1 :- occurs(some_action,t).

% pick a disk onto which to move
1 { where(N,t) : disk(N) }1 :- occurs(some_action,t).

% pegs cannot be moved
:- move(N,t), N < 5.

% only top disk can be moved
:- on(N,N1,t-1), move(N,t), otime(t).

% a disk can be placed on top only.
:- on(N,N1,t-1), where(N,t), otime(t).

% no disk is moved in two consecutive moves
:- move(N,t), move(N,t-1), otime(t).

% Specify effects of a move
on(N1,N,t) :- move(N,t), where(N1,t).
on(N,N1,t) :- on'(N,N1,t), not move(N1,t).
