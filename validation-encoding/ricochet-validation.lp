%#const row =  1.
%#const col = -1.

dir(west, -1, 0).
dir(east,  1, 0).
dir(north, 0,-1).
dir(south, 0, 1).

dl(west, -1).
dl(north,-1).
dl(east,  1).
dl(south, 1).

dir(west, 1).   %dir(west, row).
dir(east, 1).   %dir(east, row).
dir(north, -1). %dir(north,col).
dir(south, -1). %dir(south,col).

dir(D) :- dir(D,_).

robot(R) :- pos(R,_,_).

time(1..degree+1).

last(T) :- time(T), not time(T+1).

domO(1).domO(-1).
pos_domain(R,O,IJ) :- robot(R), domO(O), dim(IJ).
go_domain(R,D,O) :- robot(R), dir(D,O).

{pos(R,O,IJ,0) : pos_domain(R,O,IJ)}.  

barrier(I+1,J,west ) :- barrier(I,J,east ), dim(I), dim(J), dim(I+1).
barrier(I,J+1,north) :- barrier(I,J,south), dim(I), dim(J), dim(J+1).
barrier(I-1,J,east ) :- barrier(I,J,west ), dim(I), dim(J), dim(I-1).
barrier(I,J-1,south) :- barrier(I,J,north), dim(I), dim(J), dim(I-1).

conn(D,I,J) :- dir(D,-1), dir(D,_,DJ), not barrier(I,J,D), dim(I), dim(J), dim(J+DJ). %conn(D,I,J) :- dir(D,col), dir(D,_,DJ), not barrier(I,J,D), dim(I), dim(J), dim(J+DJ).
conn(D,J,I) :- dir(D,1), dir(D,DI,_), not barrier(I,J,D), dim(I), dim(J), dim(I+DI).  %conn(D,J,I) :- dir(D,row), dir(D,DI,_), not barrier(I,J,D), dim(I), dim(J), dim(I+DI).

{ occurs(some_action,T) } :- time(T).
1 <= { selectRobot(R,T) : robot(R) } <= 1 :- time(T), occurs(some_action,T).
1 <= { selectDir(D,O,T) : dir(D,O) } <= 1 :- time(T), occurs(some_action,T).

go(R,D,O,T) :- selectRobot(R,T), selectDir(D,O,T), time(T).
go_(R,O,T)   :- go(R,_,O,T), time(T).
go(R,D,T) :- go(R,D,_,T), time(T).

sameLine(R,D,O,RR,T)  :- go(R,D,O,T), pos(R,-O,L,T-1), pos(RR,-O,L,T-1), R != RR, time(T).
blocked(R,D,O,I+DI,T) :- go(R,D,O,T), pos(R,-O,L,T-1), not conn(D,L,I), dl(D,DI), dim(I), dim(I+DI), time(T).
blocked(R,D,O,L,T)    :- sameLine(R,D,O,RR,T), pos(RR,O,L,T-1), time(T).

reachable(R,D,O,I,   T) :- go(R,D,O,T), pos(R,O,I,T-1), time(T).
reachable(R,D,O,I+DI,T) :- reachable(R,D,O,I,T), not blocked(R,D,O,I+DI,T), dl(D,DI), dim(I+DI), time(T).

:- go(R,D,O,T), pos(R,O,I,T-1), blocked(R,D,O,I+DI,T), dl(D,DI), time(T).
:- go(R,D,O,T), go(R,DD,O,T-1), time(T).

pos(R,O,I,T) :- reachable(R,D,O,I,T), not reachable(R,D,O,I+DI,T), dl(D,DI), time(T).
pos(R,O,I,T) :- pos(R,O,I,T-1), not go_(R,O,T), time(T).

selectDir(O,T) :- selectDir(D,O,T), time(T).

%:- target(R,I,_), not pos(R,1,I,X), length(X). 
%:- target(R,_,J), not pos(R,-1,J,X), length(X). 

%:- target(R,I,_), not pos(R,1,I,s(X)), time(s(X)), not time(s(X+1)).
%:- target(R,_,J), not pos(R,-1,J,s(X)), time(s(X)), not time(s(X+1)).
