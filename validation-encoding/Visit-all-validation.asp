time(s(1..degree+1)).
max(T) :- time(s(T)), not time(s(T+1)).

first(s(0)).
last(s(T)) :- max(T).

next(s(T-1), s(T)) :- time(s(T)), T>0.
#external external(next(X,Y)) : next(X,Y).

loc(X) :- at(X).
loc(X) :- loc(XX), connected(XX,X).
loc(X) :- loc(XX), connected(X,XX).

% generate all possible initial states
1{atrobot(X,T)}1 :- loc(X), first(T).


{ occurs(some_action,T) } :- time(T), not first(T).
atrobot(N,T) :- connected(C,N), C != N, time(T), not atother(N,T),     occurs(some_action,T).
atother(N,T) :- connected(C,N), C != N, time(T), atrobot(O,T), O != N, occurs(some_action,T).

%1 <= { atrobot( Nextpos,T ) : connected( Curpos,Nextpos ), Curpos != Nextpos } <= 1 :- T=t.

move(C,N,T) :- prev_atrobot(C,T), atrobot(N,T), connected(C,N), C != N, time(T).
done(T)     :- move(C,N,T), time(T).

:- time(T), not done(T), occurs(some_action,T).

visited(X,T) :- prev_visited(X,T), time(T).
visited(X,T) :- atrobot(X,T), time(T).



{ prev_atrobot(X,T) } :- loc(X), time(T).
:- prev_atrobot(X,T), not atrobot(X,TM1), not external(next(TM1, T)), next(TM1, T).
:- not prev_atrobot(X,T), atrobot(X,TM1), not external(next(TM1, T)), next(TM1, T).

{ prev_visited(X,T) } :- loc(X), time(T), T=s(TT), TT>1.
:- prev_visited(X,T), not visited(X,TM1), not external(next(TM1, T)), next(TM1, T).
:- not prev_visited(X,T), visited(X,TM1), not external(next(TM1, T)), next(TM1, T).


%% uncomment to test
% and run this encoding with asp-planning-benchmarks/Visit-all/0009-visitall-36-1.asp
% clingo validation-encoding/Visit-all-validation.asp asp-planning-benchmarks/Visit-all/0009-visitall-36-1.asp

%#const degree=3.
%hypothesisConstraint(s(T-degree)) :- not occurs(some_action,s(T-3)), visited(loc_x0_y2,s(T)), not prev_visited(loc_x0_y2,s(T-3)), not external(next(s(T-2),s(T-1))), not external(next(s(T-1),s(T))), not external(next(s(T-3),s(T-2))), next(s(T-2),s(T-1)), next(s(T-1),s(T)), next(s(T-3),s(T-2)), T-3 > 0.
%:- not hypothesisConstraint(s(1)).

