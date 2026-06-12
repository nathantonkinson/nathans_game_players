# Nathan's code projects
Various code projects, mostly trying to use code to solve games
I am not trained as software engineer but I'm having fun lol

# Projects list:
(A lot of files were accidentally lost when I put this on github, so stuff is missing from some of these projects)
- CodinGame - https://www.codingame.com/, specifically the fall. https://www.codingame.com/ide/puzzle/the-fall-episode-3
- Reversi - I thought this would be simple enough to do my first serious AI program on, but no luck thus far
    - The genetic algorithm work on this got deleted
- Blackjack - DONE a proof of concept AI. It figured out how to stay vs hit around 17 (infinite deck).
- tictactoe - an example/tutorial I downloaded to try and get AI training best practices
    - not included right now due to size and nested gits
- Cartpole - DONE, AI tutorial teaching an AI to balance a pole on a cart
- Generic AI - some of my early AI attempts with carpole, blackjack, gym, environments
    - not included right now due to size and nested gits
- Kata - I also looked at codewars.com and tried a kata
- DialPuzzle - DONE just a puzzle I was given that I solved with code
- Propagation - attempts at solving a math problem with excel
- Farkle - DONE (mostly) hardcoded (not AI) player for the greedy dice game Farkle
- Factorio - I had fun parsing lua data into a BOM structure but solving factorio speedrun with AI would be even harder than uniwar
- UniWar - try to write AI (or any computer player) for mobile game UniWar, https://www.uniwar.com/. That folder has it's own [readme](UniWar/README.md).

# My current work / Help me out 
If you want to help me out (uniwar friends), mostly take a look at Reversi/reversi.py. It has MCTS, genetic algorithm, and generally my most advanced stuff. The current main problem is why can't MCTS or the genetic algorithm get a net to the point where it plays significantly better than random (best is a 70% winrate so far)? Do I just need more compute? Idk how replit solved my blackjack, code looks similar, so hard to pull lesson from that.

# Git commands reference
Can use cmd
In commit message editor, use ESC then ":wq" to get out
## Hard reset procedure
- something to delete all the .git
- git init - creates a repo in the current folder
- git remote add origin https://github.com/nathantonkinson/uniwar_ai.git - links to external repo
- git branch -m master main - branch might default to master, set it to main to match the external
This stuff less confident in
- git fetch origin
- git checkout -b main origin/main
## Adding normal commits
- git add . - stages all files for commit
- git rm --cached [folder path] to remove all edited files from that folder from the commit
- git commit -m "Notes about commit"
- git push
Might need this stuff for first commits
- git push -u origin HEAD - pushes back to external repo of whatever branch you're on right now. Good for first push of new branch?
## Information gathering
- git submodule status - checks nested repos stuff. Also in root there would be .gitmodules if there were modules
    - remove them with command like git rm --cached tictactoe/AlphaZero-Tic-Tac-Toe-App -f
- git status - gets difference of current files from the known latest information on your branch, I think?
- git branch --show-current
- git log --oneline
## Remove files from latest commit that is not yet pushed
- git rm --cached path/to/bigfile
- git commit --amend
    - then you need ESC and :wq

