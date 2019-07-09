%
% Domain
%

time(1..degree+1).


%
% Preprocessing
%

mutex(G,X) :- mutexGroup(G), contains(G,X,V).
mutex(G)   :- mutexGroup(G), #count{X : mutex(G,X)} > 1.


%
% Initial situation
%

% open initial situation
{ holds(X,V,0) } :- contains(X,V).


%
% Transition
%

% generate (a SAT problem)
{     holds(X,V,T) } :- contains(X,V), time(T).
{ occurs(A,T) : action(A) }  :- time(T).

% at most one action
:- 2 { occurs(A,T) : action(A) }, time(T).

% effects
:- occurs(A,T), postcondition(A,_,X,V), not holds (X,V,T).

% preconditions
:- occurs(A,T),    precondition(A,X,V), not holds'(X,V,T).

% inertia
:- holds(X,V,T), not holds'(X,V,T), time(T),
   not occurs(A,T) : postcondition(A,_,X,V).

% existence and uniqueness of value
:- not 1 { holds(X,V,T) } 1, variable(X), time(T).

% mutexes
:- 2 #sum { 1,X,V: holds(X,V,T), contains(G,X,V) }, mutex(G), time(T).


%
% Additional rules
%

% open holds'
{ holds'(X,V,T) } :- contains(X,V), time(T).
% holds' at T is equivalent to holds at T-1 (when otime at T is true)
:- holds'(X,V,T), not holds(X,V,T-1), otime(T).
:- not holds'(X,V,T), holds(X,V,T-1), otime(T).
% otime
otime(T) :- time(T).

