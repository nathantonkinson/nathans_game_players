# Uniwar solver

Project to try to make better computer players for uniwar

https://www.uniwar.com/home.page
https://play.google.com/store/apps/details?id=android.uniwar 
Can also be played on bluestacks


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
    - popup bonus for underling and sub/kraken = 4 I think, uniwar.com might have some things
    - tp no zone of control
    - emp no zone of control
    - can't convert capturing unit
    - can uv capturing units
    - uv not affecting underwater? what about buried?
    - engineer immune to plage, same with sapeins
    - uv affects both sapien and kraahl
    - map starting credits to all first turn. 1st player doesn't get base income
    - terrain bonuses are by unit type, not specific unit
    - glitch where move after attack allows a unit to live
    - can't attack what you can't see
    - ? can build sub under friendly or enemy unit on water base?
- known ways to exploit existing AIS

# Stragegy/heuristics
- https://tinyurl.com/TheArtOfUniwar
- Saved replays from various players - no good way I know of to export these

# Progression plan
- Carpole tutorial (done)
- Blackjack on my own (failed by self, worked with replit)
- Reversi 4x4 (done, the AI is just as good as perfect player)
- Reversi 8x8 (MCTS and genetic are both plateauing at 70% vs random)
- Uniwar - no income, no healing, player vs player, only marines, only plains
- AI to play this simplified version, try to get it near human level
- Add terrain
- Add different unit types, races
- Big threshold adding healing
- Big threshold adding income/bases/capturing