from pydoc import doc
import mesa
import random
import numpy as np
from random import randint
from warehouse.agents import PickerRobot
from warehouse.agents import Box
from .agents import UNDONE


class Warehouse(mesa.Model):
    """ Model representing an automated warehouse"""
    def __init__(self, n_robots, n_boxes, width=50, height=50):
        """
            * Set schedule defining model activation
            * Sets the number of robots as per user input
            * Sets the grid space of the model
            * Create n Robots as required and place them randomly on the edge of the left side of the 2D space.
            * Create m Boxes as required and place them randomly within the model (Hint: To simplify you can place them in the same horizontal position as the Robots). Make sure robots or boxes do not overlap with each other.
        """
        # TODO implement
        self.n_robots = n_robots
        self.n_boxes = n_boxes
        self.grid = mesa.space.MultiGrid(width, height, True)
        y_s = []
        self.schedule = mesa.time.RandomActivation(self)

        # Create Agents
        for n in range(self.n_robots):
            heading = (1,0)
            #append element in vector
            x = 1
            y = 1
            while True:
                y = randint(1, height-1)
                if self.grid.is_cell_empty((x,y)):
                    break
            
            y_s.append(y)
            pr = PickerRobot(n,(x,y),self)
            self.schedule.add(pr)
            self.grid.place_agent(pr,(x,y))


        # Create Boxes
        for n in range(self.n_boxes):
            while True:
                x = randint(4,width-1)
                y = random.choice(y_s)
                if self.grid.is_cell_empty((x,y)):
                    break

            b = Box(n+self.n_robots,(x,y),self)
            self.schedule.add(b)
            self.grid.place_agent(b,(x,y))
            
        self.running = True


    def step(self):
        """
        * Run while there are Undone boxes, otherwise stop running model.
        """
        # TODO implement
        if len([a for a in self.schedule.agents if isinstance(a,Box) and a.state == UNDONE]) > 0:
            self.schedule.step()
        else:
            self.running = False

    def run_model(self) -> None:
        while len([a for a in self.schedule.agents if isinstance(a,Box) and a.state == UNDONE]) > 0:
            self.step()
        