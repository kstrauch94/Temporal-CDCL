% Constant '_parallel' to enable parallel actions
% - value '0': parallel actions *without* checking for mutual disablement
% - value '1': "forall" parallel actions that can be arranged in any sequence
% - value '3': "exists" parallel actions omitting achievement of preconditions
% - value '5': sequential actions

%#const horizon = 30.
%#const imax = horizon.

#program base. % as strips-incremental.lp

% Define unsubsumed mutexes

mutex(G,X) :- mutexGroup(G), contains(G,X,V). %, fluent(X,V).
mutex(G)   :- mutexGroup(G), #count{X : mutex(G,X)} > 1.

%
% Define assumptions
%

% initial state
assumption_init(holds(X,V,0), true) :-     initialState(X,V).
assumption_init(holds(X,V,0),false) :- not initialState(X,V), contains(X,V).

% goal
assumption_goal(holds(X,V),true) :- goal(X,V).

%
% Define domains
%
domain_holds(X,V) :- contains(X,V).

% Open initial situation
{ holds(X,V,0) } :- domain_holds(X,V).


#program step(t). % new

% generate (a SAT problem)
{     holds(X,V,t) } :- domain_holds(X,V).
{ occurs(A,t) : action(A) }.

% effects
:- occurs(A,t), postcondition(A,_,X,V), not holds(X,V,t).

% preconditions
:- occurs(A,t), precondition(A,X,V),    not holds'(X,V,t).

% inertia
:- holds(X,V,t), not holds'(X,V,t),
   not occurs(A,t) : postcondition(A,_,X,V).

% existence and uniqueness of value
:- not 1 { holds(X,V,t) } 1, variable(X).

% mutexes
:- 2 #sum { 1,X,V: holds(X,V,t), contains(G,X,V) }, mutex(G).

%
% Parallel planning settings
%
