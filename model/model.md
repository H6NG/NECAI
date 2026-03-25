


The problem is searching 40 moves, 10 levels deep = 40^10 = billions of positions to evaluate. 
So I have to limit depth, which means missing the good moves.

What PyTorch adds:
Look at position
- PyTorch instantly scores all 40 moves  (learned from millions of games)
- keep only top 5 most promising
- C++ searches only those 5, but now 20 levels deep
- much better result, much less computation


The intuition comes from showing the model millions of positions played by strong players and teaching it to recognize what a good position looks like.

The model never reads rules. Tt discovers them purely from patterns in the data. That's the "learning" part.