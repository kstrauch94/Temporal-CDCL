%% preproces.lp file from plasp

% Constant '_closure' to (de)activate analysis of potentially relevant actions
% - value '1': forward chaining of effects w.r.t. initial variable values
% - value '2': backward regression of effects w.r.t. goal variable values
% - value '3': both forward chaining and backward regression of effects
% - otherwise: off

#const _closure = 3.

% BASE PROGRAM

% Check feature requirements

:- requires(feature(actionCosts)).
:- requires(feature(axiomRules)).
:- requires(feature(conditionalEffects)).

% Basic redundancy check for actions

postcondition(A,X,V) :- postcondition(A,E,X,V).

has_condition(A,X,0) :- action(A), precondition(A,X,V).
has_condition(A,X,1) :- action(A), postcondition(A,X,V).

inconsistent(A) :- has_condition(A,X,P),
                   #count{V : precondition(A,X,V), P = 0;
                          V : postcondition(A,X,V), P = 1} > 1.
consistent(A)   :- action(A), not inconsistent(A).
irredundant(A)  :- consistent(A), postcondition(A,X,V), not precondition(A,X,V).

% Forward chaining of effects w.r.t. initial variable values

feasible(X,V) :- initialState(X,V).
feasible(X,V) :- possible(A), postcondition(A,X,V).

possible(A) :- irredundant(A), feasible(X,V) : precondition(A,X,V).
possible(A) :- irredundant(A), _closure != 1, _closure != 3.

:- goal(X,V), not feasible(X,V).

% Backward regression of effects w.r.t. goal variable values

produce(X,V) :- goal(X,V), not initialState(X,V).
produce(X,V) :- active(A), precondition(A,X,V), not initialState(X,V).
produce(X,V) :- persist(X,V), active(A), has_condition(A,X,1), not postcondition(A,X,V).

persist(X,V) :- goal(X,V), initialState(X,V).
persist(X,V) :- active(A), precondition(A,X,V), initialState(X,V).

active(A) :- possible(A), postcondition(A,X,V), produce(X,V).
active(A) :- possible(A), _closure != 2, _closure != 3.


% Constant '_parallel' to enable parallel actions
% - value '0': parallel actions *without* checking for mutual disablement
% - value '1': "forall" parallel actions that can be arranged in any sequence
% - value '2': "exists" parallel actions that can be arranged in some sequence
% - value '3': "exists" parallel actions omitting achievement of preconditions
% - value '4': "exists" parallel actions like '3' implemented by acyclicity
% - otherwise: sequential actions

#const _parallel = 1.

% Constant '_shallow' to cheaply approximate mutually disabling parallel actions
% - value '0': detect incompatible pre/postconditions to reduce parallel actions
% - otherwise: over-approximate parallel actions (in testing mutual disablement)

#const _shallow = 0.

% Constant '_inertia' to choose flat or tiered format for transition constraints
% - value '0': use flat rules (integrity constraints) for transition constraints
% - otherwise: use rules that provide auxiliary atoms for transition constraints

#const _inertia = 0.

% Constant 'planner_on' to enable encoding support for ASP-based planner
% - value '0': no compatibility to ASP-based planner (no idle steps permitted)
% - otherwise: compatibility to ASP-based planner (idle steps permitted)

#const planner_on = 1.

% BASE PROGRAM

% Define auxiliary predicates for actions w.r.t. parallel mode

selfdefeat(A,X) :- active(A), precondition(A,X,V), _parallel = 1,
                   has_condition(A,X,1), not postcondition(A,X,V).

diverge(A1,A2,X) :- active(A1), active(A2), postcondition(A1,X,V),
                    has_condition(A2,X,1), not postcondition(A2,X,V),
                    0 <= _parallel, _parallel < 5, _shallow = 0.
diverge(A1,A2)   :- diverge(A1,A2,X).

exclude(A1,A2) :- active(A1), active(A2), precondition(A1,X,V),
                  has_condition(A2,X,0), not precondition(A2,X,V),
                  0 <= _parallel, _parallel < 5, _parallel != 2, _shallow = 0.

disable(A1,A2) :- active(A1), active(A2), A1 != A2, postcondition(A1,X,V),
                  has_condition(A2,X,0), not precondition(A2,X,V),
                  not diverge(A1,A2), not exclude(A1,A2),
                  1 < _parallel, _parallel < 5.

disable :- _parallel = 4, #sum{1,A1 : disable(A1,A2); -1,A2 : disable(A1,A2)} > 0.

scope(X,V) :- active(A), precondition(A,X,V), _parallel = 2.

% Define relevant fluents w.r.t. parallel mode

fluent(X,V) :- produce(X,V).
fluent(X,V) :- persist(X,V).
fluent(X,V) :- initialState(X,V), fluent(X).
fluent(X,V) :- active(A), postcondition(A,X,V), fluent(X).
fluent(X)   :- fluent(X,V).
fluent(X)   :- diverge(A1,A2,X), not exclude(A1,A2).
fluent(X)   :- active(A), has_condition(A,X,1), 0 <= _parallel, _parallel < 5, _shallow != 0.

% Define unsubsumed mutexes

mutex(G,X) :- mutexGroup(G), contains(G,X,V), fluent(X,V).
mutex(G)   :- mutexGroup(G), #count{X : mutex(G,X)} > 1.

%
% Define assumptions
%

% initial state
assumption_init(holds(X,V,0), true) :-     initialState(X,V).
assumption_init(holds(X,V,0),false) :- not initialState(X,V), contains(X,V).

% goal
assumption_goal(holds(X,V),true) :- goal(X,V).

% Define initial state

% if there is no domain_holds predicate then holds' will not be generated
%domain_holds(X,V) :- fluent(X,V).

% Open initial situation
{ holds(X,V,0) : fluent(X,V)} :- fluent(X).

:- fluent(X), #count{V : holds(X,V,0)} > 1.
:- mutex(G), #count{X,V : holds(X,V,0), contains(G,X,V)} > 1.

% STEP PROGRAM

#program step(t).

% Generate successor state

1 {holds(X,V,t) : fluent(X,V)} 1 :- fluent(X).

:- mutex(G), #count{X,V : holds(X,V,t), contains(G,X,V)} > 1.

% this rule doesnt matter since we use _inertia = 0
change(X,t) :- holds(X,V,t-1), not holds(X,V,t), _inertia != 0.

% Generate actions

{occurs(A,t)} :- active(A).

:- planner_on = 0, not occurs(A,t) : active(A).

:- occurs(A,t), postcondition(A,X,V), fluent(X), not holds(X,V,t).

effect(X,t) :- occurs(A,t), postcondition(A,X,V), fluent(X), not precondition(A,X,V),
               _inertia != 0.

:- change(X,t), not effect(X,t).

:- _inertia = 0, holds(X,V,t), not holds(X,V,t-1),
   not occurs(A,t) : active(A), postcondition(A,X,V), not precondition(A,X,V); otime(t).

% Checks w.r.t. parallel mode

:- _parallel != 0, _parallel != 1, _parallel != 2, _parallel != 3, _parallel != 4,
   #count{A : occurs(A,t)} > 1.

:- _parallel != 2, occurs(A,t), precondition(A,X,V), not holds(X,V,t-1), otime(t).

:- _parallel = 1, occurs(A,t), precondition(A,X,V), not has_condition(A,X,1), not holds(X,V,t).

single(X,t) :- occurs(A,t), selfdefeat(A,X).

:- single(X,t), #count{A : occurs(A,t), postcondition(A,X,V), not precondition(A,X,V)} > 1.

proceed(X,V,t) :- holds(X,V,t-1), scope(X,V).
proceed(X,V,t) :- perform(A,t), scope(X,V), postcondition(A,X,V), not precondition(A,X,V),
                  occurs(A,t).

perform(A,t) :- active(A), 1 < _parallel, _parallel < 4,
                proceed(X,V,t) : precondition(A,X,V), _parallel = 2;
                alright(A1,t) : disable(A,A1).

alright(A,t) :- active(A), 1 < _parallel, _parallel < 4, not occurs(A,t).
alright(A,t) :- perform(A,t).

:- 1 < _parallel, _parallel < 4, active(A), not alright(A,t).

#edge((A1,t),(A2,t)) : disable(A1,A2), occurs(A1,t), _parallel = 4, not disable.
#edge((A1,t),(A2,t)) : disable(A1,A2), occurs(A2,t), disable.


%#show occurs/2.
