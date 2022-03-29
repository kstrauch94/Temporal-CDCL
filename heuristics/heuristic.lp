#heuristic holds(X,V,T-1) : holds(X,V,T), time(T).     [10000-T+1,true]
#heuristic holds(X,V,T-1) : not holds(X,V,T), time(T). [10000-T+1,false]