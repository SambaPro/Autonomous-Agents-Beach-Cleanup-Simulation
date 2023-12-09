from pydoc import doc
import mesa
import random
import numpy as np
from random import randint
from beach.agents import CT_Robot, LargeDebris, WasteBin, ChargingPoint, Obstacle, Debris, LC_Robot, Bidder
from .agents import UNDONE, DONE, NUMBER_OF_CELLS, UNDERWAY, NEW_DEBRIS_CHANCE


class Beach(mesa.Model):
    """ Model representing a beach full of trash"""
    def __init__(self, n_CT_robots, n_Ldebris, n_obstacles, n_debris, n_LC_robots, EXTENDED,width=NUMBER_OF_CELLS, height=NUMBER_OF_CELLS):
        self.n_CT_robots = n_CT_robots
        self.n_Ldebris = n_Ldebris
        self.n_obstacles = n_obstacles
        self.n_debris = n_debris
        self.n_LC_robots = n_LC_robots
        self.grid = mesa.space.MultiGrid(width, height, True)
        y_s = []
        self.schedule = mesa.time.RandomActivation(self)
        self.EXTENDED = EXTENDED
        self.n = 0 # Number of agents on Beach

        # Place Charger and Wastebin
        x = 49
        y = 0
        wb = WasteBin(self.n, (width-1,y),self)
        self.schedule.add(wb)
        self.grid.place_agent(wb,(x,y))
        self.n += 1

        chp = ChargingPoint(self.n, (0,0), self)
        self.schedule.add(chp)
        self.grid.place_agent(wb,(0,0))
        self.n += 1

        # Create Bidder Agent
        bidder  = Bidder(self.n, self)
        self.schedule.add(bidder)
        self.n += 1

        # Place Obstacles
        for n in range(self.n_obstacles):
            while True:
                x = randint(4,width-1)
                y = randint(4,width-1)
                if self.grid.is_cell_empty((x,y)):
                    break
            
            obstacle = Obstacle(self.n,(x,y),self)
            self.schedule.add(obstacle)
            self.grid.place_agent(obstacle,(x,y))
            self.n += 1


        # Create CT Agents
        for n in range(self.n_CT_robots):
            #append element in vector
            x = 1
            y = 1
            while True:
                y = randint(1, height-1)
                if self.grid.is_cell_empty((x,y)):
                    break
            
            y_s.append(y)
            pr = CT_Robot(self.n,(x,y),self)
            self.schedule.add(pr)
            self.grid.place_agent(pr,(x,y))
            self.n += 1


        # Create Large Debris
        for n in range(self.n_Ldebris):
            while True:
                x = randint(4,width-1)
                y = randint(4,width-1)
                if self.grid.is_cell_empty((x,y)):
                    break

            b = LargeDebris(self.n,(x,y),self)
            self.schedule.add(b)
            self.grid.place_agent(b,(x,y))
            self.n += 1

        # Create Small Debris
        for n in range(self.n_debris):
            while True:
                x = randint(4,width-1)
                y = randint(4,width-1)
                if self.grid.is_cell_empty((x,y)):
                    break

            d = Debris(self.n,(x,y),self)
            self.schedule.add(d)
            self.grid.place_agent(d,(x,y))
            self.n += 1

        # Create LC robots
        for n in range(self.n_LC_robots):
            #append element in vector
            x = 1
            y = 1
            while True:
                y = randint(1, height-1)
                if self.grid.is_cell_empty((x,y)):
                    break
            
            y_s.append(y)
            lc = LC_Robot(self.n,(x,y),self)
            self.schedule.add(lc)
            self.grid.place_agent(lc,(x,y))
            self.n += 1

            
        self.running = True


    def step(self):
        """
        * Run while there are Undone Debris, otherwise stop running model.
        """
        # Ends if all Debris are DONE
        if len([a for a in self.schedule.agents if isinstance(a,LargeDebris) and (a.state == UNDONE or a.state == UNDERWAY)])  != 0:
            self.schedule.step()
        elif len([a for a in self.schedule.agents if isinstance(a,Debris) and (a.state == UNDONE or a.state == UNDERWAY)]) != 0:
            self.schedule.step()
        else:
            print("Simulation Stopping")
            self.running = False
        

        if self.EXTENDED:

            # Chance to add new Large Debris to beach
            num = random.random()
            if num < NEW_DEBRIS_CHANCE:
                while True:
                    x = randint(4, NUMBER_OF_CELLS-1)
                    y = randint(4, NUMBER_OF_CELLS-1)
                    if self.grid.is_cell_empty((x,y)):
                        break

                d = LargeDebris(self.n,(x,y),self)
                self.n += 1
                self.schedule.add(d)
                self.grid.place_agent(d,(x,y))                


    def run_model(self) -> None:
        while len([a for a in self.schedule.agents if isinstance(a,LargeDebris) and a.state == DONE]) < self.n_Ldebris and len([a for a in self.schedule.agents if isinstance(a,Debris) and a.state == DONE]) < self.n_debris:
            self.step()
        