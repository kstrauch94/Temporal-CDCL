
time(0..degree+1).

peg(1..4).
realdisk(N) :- disk(N), not peg(N).
% M is on N
domain_on(N,M) :- disk(N), realdisk(M), N < M.

{on(N,M,0) : domain_on(N,M)} :- realdisk(M).

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
:- on(N,N1,T-1), move(N,T), time(T).

% a disk can be placed on top only.
:- on(N,N1,T-1), where(N,T), time(T).

% no disk is moved in two consecutive moves
:- move(N,T), move(N,T-1), time(T).

% Specify effects of a move
on(N1,N,T) :- move(N,T), where(N1,T).
on(N,N1,T) :- T > 0,
              on(N,N1,T-1), not move(N1,T), time(T).
