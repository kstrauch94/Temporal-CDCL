at(R,P,0) :- start(R,P).

time(1..horizon).

{ move(R,U,V,T) : edge(U,V)} 1 :- agent(R), time(T).

% - move ------------------------------------------------------------------
at(R,V,T) :- move(R,_,V,T).
          :- move(R,U,_,T), not at(R,U,T-1).

% - inertia ---------------------------------------------------------------
at(R,V,T) :- at(R,V,T-1), not move(R,V,_,T), time(T).

:- { at(R,V,T) : agent(R) }  > 1, vertex(V), time(T).

:- move(_,U,V,T), move(_,V,U,T), U < V.

:- { at(R,V,T) } != 1, agent(R), time(T).

:- goal(R,V), not at(R,V,horizon).