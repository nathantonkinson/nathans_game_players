# Uniwar solver

Project to try to make better computer players for uniwar

https://www.uniwar.com/home.page
https://play.google.com/store/apps/details?id=android.uniwar 
Can also be played on bluestacks, steam


# Mechanics/rules/UI
- hashtag commands
- vision persisting
- damage mechanic
    - [Link to spank's janky uniwar calculator](https://docs.google.com/spreadsheets/d/1e7OUe35zL6X2NbSPIwrTGR9NpJ-h-ATceUM90gxSsE8/edit#gid=1537685831)
    - https://unicalc.github.io/web/
    - full rng p damage mechanics described
    - my python with math simplification
    - attempt to back into it via symbolic regression
        - I had TuringBot_3.3.1_windows64.exe in here but it's too big for github so it's in .gitignore, but you can download it yourself. Also we don't need it because Spanky's Janky uniwar calculator I think has the true accurate code/process
    - new numbers generated start of each turn right, not across whole game?
- advanced rules/mechancis
    - heavy ground on buried underling
    - buried can't attach each other
    - sub vs underling on water road etc etc
    - popup bonus for underling and sub/kraken = 4 per uniwar.com. Need to recalc these. Skimmer definitely has a bonus
    - tp no zone of control
    - emp no zone of control
    - can't convert capturing unit
    - can uv capturing units
    - uv not affecting underwater? what about buried?
    - engineer immune to plage, same with submarine
    - uv affects both sapien and kraahl
    - map starting credits to all first turn. 1st player doesn't get base income
    - terrain bonuses are by unit type, not specific unit
    - glitch where move after attack allows a unit to live
    - can't attack what you can't see
    - ? can build sub under friendly or enemy unit on water base?
    - plague affects all other sapiens, spreads at start of turn of being infected unit from any adjacent?
    - ? sub zone of control?
    - no fow can target subs
- map hashtags
    - #SPC - turns Single Player Challenge mode for the map. The games are automatically started vs BOT and can be easily restarted.
    - #TEAM - enables team mode for this SPC map.
    - #NOFOW - disable Fog Of War for this SPC map.
    - #AI1 / #AI2 / #AI3 - force BOT algorithm for this SPC map.
    - #RNG123 - 123 can be any number used as random seed at start of the SPC game. This makes attacks in the game to have repeatable outcomes for every player.
    - #BLITZ2 - 2 is the number of minutes that the timer gets reset when player in turn opens the game. This modifier lets you have the usual 24 hours to make your turn, but only 2 minutes to think about the moves.
    - #BLIM5 - 5 is the round number during the game when the bases get depleted and do not produce crystals anymore. Cities, however, provide crystals during the whole game.
    - #RNGBUILD - fun game mode that makes all your empty bases to build random units for free. This way players do not have control on what to build.
    - #RNGBUILDANY - same as above, but player bases build random units of any race. Even more fun!
- known ways to exploit existing AIS

# Stragegy/heuristics
- https://tinyurl.com/TheArtOfUniwar
- Saved replays from various players - no good way I know of to export these

# Progression plan
- Carpole tutorial (done)
- Blackjack on my own (failed by self, worked with replit)
- Reversi 4x4 (done, the AI is just as good as perfect player)
- Reversi 8x8 (MCTS and genetic are both plateauing at 70% vs random)
- Uniwar - no income, no healing, player vs player, only marines, only plains, games capped at 10 rounds or something
- AI to play this simplified version, try to get it near human level
- Add terrain
- Add different unit types, races
- Big threshold adding healing
- Big threshold adding income/bases/capturing

# Architecture plan for uniwar (object based)
- at root will be executable "main" stuff.. or should that still be src? Nah. We will want to run the low level stuff manually, still put in src but do lightweight mains on outside?? Then step debug doesn't work... does it?
- src folder for all the engine code stuff
- gameData folder
    - Terrain types
    - Unit classes
    - Units
    - Images for units and terrain
- Unit class
    - number of actions/turn
    - action list available to it
    - maybe inherit unit type (heavy ground) or custom stats (must still declare a type)
    - normal stats like atk vs types
    - max hp
    - current hp
    - current veterancy
- Action and/or ability class?? maybe not, but there is a list of abilities
- Hex class??
    - id?
    - terrain type
    - contains maybe units
- Game state class
    - list of hexes and the units on them
    - turn order / player list with their credits
    - is fog of war on and other config (random unit building and stuff, win conditions)
    - rng list (if we take a partial turn, used rngs get removed from front of list)
- Move class
    - Ordered list of units (hex and state in that hex) and their actions
    - Action possibilities (and potentially multiple actions per unit)
        - Move
        - Attack
        - Move after attack
        - Heal
        - Special (convert, UV, EMP, submerge/bury, surface)
    - Maybe something special for pass turn - either call unit at 0,0 or it's just an action available to all units, idk
    - Do we build in the results of actions to this or not?
- Game history class
    - The initial map/game state (probably contains full map data, not just a link to the map)
    - List of move class
    - Somehow also need the results (damage and stuff), 
- Game engine class
    - versions that are much simpler, version that are more complicated or full
    - runs a single game
    - pass it a game state to start
    - call its currentState() to get state - needs ability to fog of war
    - then pass moves
    - validate moves (reject if invalid etc)
    - apply moves, update itself
    - builds a game history
    - pass it a game state on initialization (to handle first turnm it is 1st players turn already with start cred)
- Player class
    - people should "inherit" this to make their own
    - we can modify this to communicate locally or API or whatever?? or separate class for the commuication?
- Game master class (match runner)
    - for 1 to 100
    - initialize engine
    - pass state to player, get move from player, pass that to engine, get state back
- Submissions folder in the github whose members inherit player class
- Maps folder (These are just game states)
- Match history folder containing game history
- Visualizer class
    - 

# Architecture tweaks for AI
- several arrays faster than objects (classes)
- map
    - an array or matrix representing terrain (x, y) = type
    - an array or matrix represeting where units are (x, y) = unit index
    - tiles are adjacent to: prev row same and -1, current row +1/-1, next row 0/+1
- units a set of arrays representing the units properties, one index per unit, each array holding a basic stat info for unit at index i
    - owner, type, x, y (or maybe terrain index?), hp, actons remain
- ?? wrap core functions in numba jit?? I don't know what this means
- probs the "available moves" function returns the deltas of future states from current (atk and def unit)
    - separate each action, and atk vs move vs else whatever

# Best practice stuff
- all folders are packages with __init__.py in them, so that if I move files around inside the package, it still works
- all files have a hardcoded reference back to root (can't really do helper function because I can't find helper if I can't find root lol)
- run/test all code from top level main folder

# Glossary
- tile - one cell on a map 
    - cell - synonym
    - hex - synonym
- state - surfaceair vs underwater vs underground.
    - mode - synonym, trying to find something better
- terrain - mountain, forest etc. Includes base, void, etc
- map - submitted map intended for play, whatever
- game state - mid state of game, compatible with map
- action - normal units get one per turn. things that require action like attack, heal, assimilate, plague. Some allow movement before
- ability - active and passive abilities that units have
- force - can use this to refer to passive abilities
- unit - all moveable units
- race - sapiens, titans, krahleans
- null - no unit at this location, or whatever
    - -1 - can use neg1 as well
    - None - the python data type for missing/empty
    - missing
    - empty

