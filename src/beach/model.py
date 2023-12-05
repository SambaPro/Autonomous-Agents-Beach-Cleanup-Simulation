from pydoc import doc
import mesa
import random
import numpy as np
from random import randint
from beach.agents import CT_Robot, LargeDebris, WasteBin, ChargingPoint, Obstacle, Debris, LC_Robot
from .agents import UNDONE, DONE, NUMBER_OF_CELLS, UNDERWAY, NEW_DEBRIS_CHANCE, EXTENDED


class Beach(mesa.Model):
    """ Model representing a beach full of trash"""
    def __init__(self, n_CT_robots, n_Ldebris, n_obstacles, n_debris, n_LC_robots, width=NUMBER_OF_CELLS, height=NUMBER_OF_CELLS):
        self.n_CT_robots = n_CT_robots
        self.n_Ldebris = n_Ldebris
        self.n_obstacles = n_obstacles
        self.n_debris = n_debris
        self.n_LC_robots = n_LC_robots
        self.grid = mesa.space.MultiGrid(width, height, True)
        y_s = []
        self.schedule = mesa.time.RandomActivation(self)
        self.x = 10000

        # Place Charger and Wastebin
        x = 49
        y = 0
        wb = WasteBin(9998, (width-1,y),self)
        self.schedule.add(wb)
        self.grid.place_agent(wb,(x,y))

        chp = ChargingPoint(9999, (0,0), self)
        self.schedule.add(chp)
        self.grid.place_agent(wb,(0,0))


        # Place Obstacles
        for n in range(self.n_obstacles):
            while True:
                x = randint(4,width-1)
                y = randint(4,width-1)
                if self.grid.is_cell_empty((x,y)):
                    break
            
            obstacle = Obstacle(n,(x,y),self)
            self.schedule.add(obstacle)
            self.grid.place_agent(obstacle,(x,y))


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
            pr = CT_Robot(n+self.n_obstacles,(x,y),self)
            self.schedule.add(pr)
            self.grid.place_agent(pr,(x,y))


        # Create Large Debris
        for n in range(self.n_Ldebris):
            while True:
                x = randint(4,width-1)
                y = randint(4,width-1)
                if self.grid.is_cell_empty((x,y)):
                    break

            b = LargeDebris(n+self.n_obstacles+self.n_CT_robots,(x,y),self)
            self.schedule.add(b)
            self.grid.place_agent(b,(x,y))

        # Create Small Debris
        for n in range(self.n_debris):
            while True:
                x = randint(4,width-1)
                y = randint(4,width-1)
                if self.grid.is_cell_empty((x,y)):
                    break

            d = Debris(n+self.n_obstacles+self.n_CT_robots+n_Ldebris,(x,y),self)
            self.schedule.add(d)
            self.grid.place_agent(d,(x,y))

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
            lc = LC_Robot(n+self.n_obstacles+self.n_CT_robots+n_Ldebris+n_debris,(x,y),self)
            self.schedule.add(lc)
            self.grid.place_agent(lc,(x,y))

            
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
        
               
        # Chance to add new Large Debris to beach
        if EXTENDED:
            num = random.random()
            if num < NEW_DEBRIS_CHANCE:
                while True:
                    x = randint(4, NUMBER_OF_CELLS-1)
                    y = randint(4, NUMBER_OF_CELLS-1)
                    if self.grid.is_cell_empty((x,y)):
                        break

                d = LargeDebris(self.x,(x,y),self)
                self.x =self.x + 1
                self.schedule.add(d)
                self.grid.place_agent(d,(x,y))




    def run_model(self) -> None:
        while len([a for a in self.schedule.agents if isinstance(a,LargeDebris) and a.state == DONE]) < self.n_Ldebris and len([a for a in self.schedule.agents if isinstance(a,Debris) and a.state == DONE]) < self.n_debris:
            self.step()
        