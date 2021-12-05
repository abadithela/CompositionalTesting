class Agent:
    def __init__(self, name, x, y, v, goal, orientation=None):
        self.name = name
        self.x = x
        self.y = y
        self.v = v
        self.goal = goal
        if orientation is not None:
            self.orientation = orientation
        else:
            self.orientation = 0
        # if self.orientation == self.goal:
        #     self.turn = True
        # else:
        #     self.turn = False
    #
    def step_forward(self):
        self.x = self.x + 1

    def step_mergeL(self):
        self.x = self.x + 1
        self.y = self.y + 1

    def step_mergeR(self):
        self.x = self.x + 1
        self.y = self.y - 1

    def step_stay(self):
        pass

    # def setxy(self,x,y):
    #     self.x = x
    #     self.y = y
