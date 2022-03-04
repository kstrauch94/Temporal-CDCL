

%#const horizon=1.
time(1..horizon).

direction((X,Y)) :- X=-1..1, Y=-1..1, |X+Y|=1.
nextto((X,Y),(DX,DY),(X',Y')) :- direction((DX,DY)), position((X,Y)), position((X',Y')),
                                 (X,Y)=(X'-DX,Y'-DY), (X',Y')=(X+DX,Y+DY).

{ move(R,D,T) : direction(D) } 1 :- isRobot(R), time(T).

% - move/3 ----------------------------------------------------------------------
position(R,C,T) :- move(R,D,T), position'(R,C',T),     nextto(C',D,C).
                :- move(R,D,T), position'(R,C ,T), not nextto(C ,D,_).

% - inertia ---------------------------------------------------------------------
position(R,C,T) :- position'(R,C,T), not move(R,_,T), isRobot(R), time(T).

% - edge collision --------------------------------------------------------------
moveto(C',C,T) :- nextto(C',D,C), position'(R,C',T), move(R,D,T).
 :- moveto(C',C,T), moveto(C,C',T), C < C'.

% - vertex collision ------------------------------------------------------------
 :- { position(R,C,T) : isRobot(R) }  > 1, position(C), time(T).

% - auxiliaries -----------------------------------------------------------------
 :- { position(R,C,T) } != 1, isRobot(R), time(T).    % REDUNDANT but PERFORMANT?
 
 
% goal

processed(A,R) :- ordered(O,A), shelved(S,A), isRobot(R), position(S,C,0),
                  position(R,C,horizon).
processed(A)   :- processed(A,R).

%:- ordered(O,A), not processed(A).


% --------------------------------------------------------------------------------
% REPRESENTATION

robot(R)                     :- init(object(robot,R),          _).
shelf(S)                     :- init(object(shelf,S),          _).
station(P)                   :- init(object(pickingStation,P), _).
product(A)                   :- init(object(product,A),        _).

    isRobot(robot(R)) :- robot(R).
    isShelf(shelf(S)) :- shelf(S).
isStation(station(T)) :- station(T).
isProduct(product(A)) :- product(A).
    isOrder(order(O)) :- order(O).

  order(      O            ) :- init(object(order,O),          _).
ordered(order(O),product(A)) :- init(object(order,O),          value(line,(A,_))).      % IGNORING QUANTITIES
 target(order(O),station(P)) :- init(object(order,O),          value(pickingStation,P)).

shelved(shelf(S),product(A)) :- init(object(product,A),        value(on,(S,_))).        % IGNORING QUANTITIES

position(           (X,Y))   :- init(object(node,_),           value(at,(X,Y))).

position(station(P),(X,Y))   :- init(object(pickingStation,P), value(at,(X,Y))).

%position(  robot(R),(X,Y),0) :- init(object(robot,R),          value(at,(X,Y))).
position(  shelf(S),(X,Y),0) :- init(object(shelf,S),          value(at,(X,Y))).

highway(            C    )   :- init(object(highway,_),        value(at,C)).


domain_position(R,C) :- isRobot(R), position(C).
{ position'(R,C,T) } :- domain_position(R,C), time(T), T > 0.
:- position'(R,C,T), not position(R,C,T-1), otime(T).
:- not position'(R,C,T), position(R,C,T-1), otime(T).

{ otime(T) } :- time(T), T > 0.

%
% Define assumptions
%

% initial state
assumption(position(robot(R),(X,Y),0), true) :-     init(object(robot,R), value(at,(X,Y))).
assumption(position(robot(R),(X,Y),0),false) :- not init(object(robot,R), value(at,(X,Y))), domain_position(robot(R),(X,Y)).
% goal
assumption(position(R,C,T),true) :- ordered(O,A), shelved(S,A), isRobot(R), position(S,C,0), time(T), not time(T+1).
% otime
assumption(otime(T),true) :- time(T).