import textwrap
import random

GRAPH = {'A': ['B', 'C'],
         'B': ['A', 'D', 'E'],
         'C': ['A', 'F'],
         'D': ['B'],
         'E': ['B', 'F'],
         'F': ['C', 'E']}

MAZE = 'xxxxxxxxxx'\
       'x........x'\
       'x......E.x'\
       'x........x'\
       'x..xxxx..x'\
       'x.....x..x'\
       'x.....x..x'\
       'x.S......x'\
       'x........x'\
       'xxxxxxxxxx'

MAZE = [textwrap.wrap(el, 1) for el in [line for line in textwrap.wrap(MAZE, 10)]]

def dfs(begin):
    steps, visited, stack = [], set(), [begin]
    while stack:
        vertex = stack.pop()
        if(vertex not in visited):
            visited.add(vertex)
            steps.append(vertex)
            stack.extend([el for el in GRAPH[vertex] if el not in visited])
    return steps

def dfs_paths(start, end):
    visited, stack = set(), [(start, [start])]
    while stack:
        vertex, path = stack.pop()
        if vertex not in visited:
            visited.add(vertex)
        for n in [el for el in GRAPH[vertex] if el not in visited]:
            if(n == end):
                yield path + [n]
            else:
                stack.append((n, path + [n]))
                
def bfs(begin):
    steps, visited, queue = [], set(), [begin]
    while queue:
        vertex = queue.pop(0)
        if(vertex not in visited):
            visited.add(vertex)
            steps.append(vertex)
            queue.extend([el for el in GRAPH[vertex] if el not in visited])
    return steps

def bfs_paths(start, end):
    visited, queue = set(), [(start, [start])]
    while queue:
        vertex, path = queue.pop(0)
        if vertex not in visited:
            visited.add(vertex)
        for n in [el for el in GRAPH[vertex] if el not in visited]:
            if(n == end):
                yield path + [n]
            else:
                queue.append((n, path + [n]))

def bfs_shortest_path(start, end):
    try:
        return next(bfs_paths(start, end))
    except StopIteration:
        return None

def maze_solver_DFS():
    stack = [(1, 0)]
    visited = set()
    steps = []
    while stack:
        position = stack.pop()
        if position not in visited:
            visited.add(position)
        else:
            continue 
        y, x = position
        cur_val = MAZE[y][x]
        if(cur_val == 'E'):
            return steps
        if(cur_val == 'x'):
            continue
        if(cur_val == '.'):
            steps.append((y, x))
            MAZE[y][x] = '?'
        stack.append((y + 1, x))
        stack.append((y, x + 1))
        stack.append((y - 1, x))
        stack.append((y, x - 1))

def maze_solver_BFS(maze, start, height, width):
    queue = [(start, [start])]
    visited = set()
    steps = [(1, 0)]
    while queue:
        position, path = queue.pop(0)
        y, x = position
        if position not in visited:
            visited.add(position)
        for n in [d for d in [(y + 1, x), (y, x + 1), (y - 1, x), (y, x - 1)] if d not in visited]:
            y, x = n
            if(y >= 0 and y < height and x >= 0 and x < width):
                cur_val = maze[y][x]
                if(cur_val == 'E'):
                    return path + [(y, x)]
                elif(cur_val == 'x'):
                    continue
                else:
                    maze[y][x] = '?'
                    queue.append(((y, x), path + [(y, x)]))
def print_maze(maze):
    for line in maze:
        for pos in line:
            print(pos, end='')
        print()
    print('==================================')
    
def maze_generator(height, width):
    start = (2, 2)
    stack = [start]
    maze = [['x' for _ in range(width)] for __ in range(height)]
    dx = [0, 1, 0, -1]
    dy = [-1, 0, 1, 0]
    while stack:
        y, x = stack[-1]
        #print('x, y = {}, {}'.format(x, y))
        maze[y][x] = '.'    
        nlist = []
        for i in range(4):
            ny = y + dy[i]
            nx = x + dx[i]
            #print('  nx, ny = {}, {} -> {} value: {}'.format(nx, ny, nx >= 1 and nx < (width - 1) and ny >= 1 and  ny < (height - 1), maze[ny][nx]))
            if(nx >= 1 and nx < (width - 1) and ny >= 1 and  ny < (height - 1)):
                if(maze[ny][nx] == 'x'):
                    ctr = 0
                    for j in range(4):
                        ey = ny + dy[j]
                        ex = nx + dx[j]
                        #print('    ex, ey = {}, {} -> {} value: {}'.format(ex, ey, ex >= 1 and ex < (width - 1) and ey >= 1 and  ey < (height - 1), maze[ey][ex]))
                        if(ex >= 1 and ex < (width - 1) and ey >= 1 and  ey < (height - 1)):
                            if(maze[ey][ex] == '.'):
                                ctr += 1                               
                                #print(ey, ex)
                    if(ctr == 1):
                        #print(i, ctr)
                        nlist.append(i)
        #print(nlist)
        if(len(nlist) > 0):
            i = nlist[random.randint(0, len(nlist) - 1)]
            #i = nlist[0]
            y += dy[i]
            x += dx[i]          
            stack.append((y ,x))
        else:
            stack.pop()
        #print_maze(maze)
        #print('stack: ', stack)
    maze[2][2] = 'S'
    maze[height - 2][width - 1] = 'E'
    return maze, start
##def maze_solver_BFS():
##    queue = [((1, 0), (1, 0))]
##    visited = set()
##    steps = [(1, 0)]
##    while queue:
##        position, path = queue.pop(0)
##        y, x = position
##        if position not in visited:
##            visited.add(position)
##        else: continue
##        for n in [el for el in [(y + 1, x), (y, x + 1), (y - 1, x), (y, x - 1)] if el not in visited]:
##            y, x = n
##        cur_val = MAZE[y][x]
##        if(cur_val == 'E'):
##            return steps
##        if(cur_val == 'x'):
##            continue
##        if(cur_val == '.'):
##            steps.append((y, x))
##            MAZE[y][x] = '?'
##        queue.append((y + 1, x))
##        queue.append((y, x + 1))
##        queue.append((y - 1, x))
##        queue.append((y, x - 1))

def main():
##    print('DFS connection component:')
##    print(dfs('A'))
##    print('DFS dfs paths:')
##    for path in dfs_paths('A', 'F'):
##        print(path)
##    print('BFS connection component:')
##    print(bfs('A'))
##    print('BFS dfs paths:')
##    for path in bfs_paths('A', 'F'):
##        print(path)
##    print('BFS shortest path:')
##    print(bfs_shortest_path('A', 'F'))
    WIDTH = 64
    HEIGHT =  64
    maze_rand, start = maze_generator(HEIGHT, WIDTH)
    print('solving...')
    
    result = maze_solver_BFS(maze_rand, start, HEIGHT, WIDTH)
    if(result):
        print('done!')
        print(result)
    else:
        print('unsolvable!')
    
        
    print_maze(maze_rand)
    #print(MAZE)
main()
