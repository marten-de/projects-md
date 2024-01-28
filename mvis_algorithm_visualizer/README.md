# mvis - Algorithm Visualizer
<br />

### Introduction:

mvis is an algorithm visualizer for the popular A* path finding algorithm. It has a GUI where the user can set a start and end point, as well as some barriers. Once the algorithm is started, the visited nodes (possible paths) will be visualized.

### Quick Start Guide

Run the script astar.py in your terminal e.g. by moving to the according directory and typing:

```
python3 astar.py
```

This works for Mac OS X; on Windows, `python3` needs to be replaced with `python`.

Once the GUI opens, your fist left-click will place the starting point for the algorithm, the second left-click will place the end point. All subsequent left-clicks will place barriers, that the algorithm can't cross.

Right-clicks will remove the placed feature.

Once there is at least a start and end point, the algorithm can be started by pressing `SPACE`. Pressing `c` clears the whole screen, and pressing `r` removes start and end points, but keeps barriers that were already placed. Both `r` and `c` can also be used after the algorithm finishes running.

### Acknowledgements

I used the following video by Tech With Tim both as idea and template for the code, before I made some adjustments/ improvements on my own:

https://www.youtube.com/watch?v=JtiK0DOeI4A

### How Does mvis Work?

mvis uses pygame for the graphical representation of nodes. Each node (class Square) can have one of many possible traits, such as start, end, barrier, path, visited, etc., which are represented by a different color each. 

The algorithm, in this case A*, can change these traits according to its progress. This means that the user can track what the algorithm is doing at which point in time, by looking at the color representation of each node. To prevent the algorithm from running to fast, a sleep time can be set.

The script has a main function that runs an infinite loop, constantly updating the status of each node, until it is cancelled manually.

### Limits of mvis

So far mvis only supports the A* algorithm. It would be possible to include other algorithms such as Dijkstra (which is basically the same as A*, but without the distance estimation function h), or Bellman-Ford.

### Developing Process:

Since I used the code provided in the video tutorial as a template, I did not need to develop everything from scratch. However, I implemented numerous changes:

I wanted the algorithm to work with diagonal paths (8-directional), not only 4-directional paths. This meant, I had to update the Square class to contain 8 neighbors instead of 4, and also I needed to change the h-function, which is the distance estimation, to be euclidean distance instead of manhattan distance.

Also, I didn't like that in the initial code, each node's status was directly determined by its color. I think this might be difficult to update, in case one wants a different color scheme. So I used a string as the status and a dictionary that linked each of these different statuses to their respective color. That way, only this dictionary needs to be adjusted if a color change is needed. In fact I directly adjusted the colors to blue shades.

I needed to do two minor adjustments as well: In the original code, the coordinates x, y were flipped. This didn't cause any error because the area used was a square, but for my version, I used a rectangle shape and it didn't function properly; after tracking down the bug and using using x, y in the correct way, it worked. Also, once the algorithm finishes, the starting square's color got changed to the path color. I didn't like this behavior, so in my version the start and end point always keep their color.

Finally, I added a function that allows the user to clear everything but the already placed barriers (by pressing `r`). If a user draws a complex shape and then realizes there is a small mistake once the algorithm already ran, then he/ she does not need to redraw the whole shape, but can adjust it instead.

