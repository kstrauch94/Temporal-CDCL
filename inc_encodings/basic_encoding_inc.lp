% Constant '_parallel' to enable parallel actions
% - value '0': parallel actions *without* checking for mutual disablement
% - value '1': "forall" parallel actions that can be arranged in any sequence
% - value '3': "exists" parallel actions omitting achievement of preconditions
% - value '5': sequential actions

#const _parallel = 5.
#const horizon = 30.
#const imax = horizon.

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

#program base.

% _parallel = 1
selfdefeat(A,X) :- action(A), precondition(A,X,V),
                       postcondition(A,_,X,_),
                   not postcondition(A,_,X,V), _parallel = 1.

% _parallel = 3
disable(A1,A2) :- action(A1), action(A2), A1 != A2, _parallel = 3,
                  postcondition(A1,_,X,V1), precondition(A2,X,V2), V1 != V2.

#program step(t).

% _parallel = 1
:- occurs(A,t),                              _parallel = 1,
   precondition(A,X,V), not postcondition(A,_,X,_), not holds(X,V,t).
single(X,t) :- occurs(A,t), selfdefeat(A,X), _parallel = 1.
:- single(X,t),                              _parallel = 1,
   #count{A : occurs(A,t),
                  postcondition(A,_,X,V),
              not precondition(A,X,V)} > 1.

% _parallel = 3
perform(A,t) :- action(A),                  _parallel = 3,
                alright(A1,t) : disable(A,A1).

alright(A,t) :- action(A), not occurs(A,t), _parallel = 3.
alright(A,t) :- perform(A,t),               _parallel = 3.

:- action(A), not alright(A,t),             _parallel = 3.

% _parallel = 5
:- 2 { occurs(A,t) },                       _parallel = 5.

