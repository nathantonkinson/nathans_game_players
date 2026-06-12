# uniwar_ai
Attempts at a better uniwar.com computer player. I am not a developer but I'm trying lol.

This repo has various sub-projects where generally I'm trying to solve games with code and AI

# Notable projects:
- https://www.codingame.com/, specifically the fall. https://www.codingame.com/ide/puzzle/the-fall-episode-3
- Reversi - I thought this would be simple enough to do my first serious AI program on, but no luck thus far
- Blackjack - DONE a proof of concept AI. It figured out how to stay vs hit around 17 (infinite deck).
- Factorio - I had fun parsing lua data into a BOM structure but solving factorio speedrun with AI would be even harder than uniwar
    - removed right now from the git due to size
- tictactoe - an example/tutorial I downloaded
    - possibly stuff is not working with the git on this
- Farkle - DONE (mostly) hardcoded (not AI) player for the greedy dice game Farkle
- Cartpole - DONE, AI tutorial teaching an AI to balance a pole on a cart
- Kata - I also looked at codewars.com and tried a kata
- DialPuzzle - DONE just a puzzle I was given that I solved with code
- Propagation - attempts at solving a math problem with excel
- Generic AI - some of my early AI attempts with carpole, blackjack, gym, environments

# helm me out 
If you want to help me out (uniwar friends), mostly take a look at Reversi/reversi.py. It has MCTS, genetic algorithm, and generally my most advanced stuff. The current main problem is why can't MCTS or the genetic algorithm get a net to the point where it plays significantly better than random (best is a 70% winrate so far)? Do I just need more compute? 


# Git commands reference
Can use cmd
- git init - creates a repo in the current folder
- git remote add origin https://github.com/nathantonkinson/uniwar_ai.git - links to external repo
- git add . - stages all files for commit
- git commit -m "name of commit"
- git push -u origin HEAD - pushes back to external repo of whatever branch you're on right now. Good for first push of new branch?
- git push - will often work as simplified, git should complain if you didn't give it enough detail?
INFORMATION
- git submodule status - checks nested repos stuff. Also in root there would be .gitmodules if there were modules
    - remove them with command like git rm --cached tictactoe/AlphaZero-Tic-Tac-Toe-App -f
- git status - gets difference of current files from the known latest information on your branch, I think?
- git branch --show-current
- git log --oneline

- git rm --cached [folder path] to remove all edited files from that folder from the commit

- git branch -m master main - renames branch

MERGE
- git checkout [branchtoaddto]
- git merge [branchwithaddedinfo]
- git push origin [branchtoaddto]

