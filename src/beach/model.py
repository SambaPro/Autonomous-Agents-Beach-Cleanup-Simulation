from pydoc import doc
import mesa
import random
import numpy as np
from random import randint
from .agents import CT_Robot, LargeDebris, WasteBin, ChargingPoint, Obstacle, Debris, LC_Robot, Bidder
from .agents import NUMBER_OF_CELLS, NEW_DEBRIS_CHANCE,  UNDONE, DONE, UNDERWAY, IDLE, EXPLORING, PICKING, CHARGING, EMPTYING

def pending_LDebris(model):
    """
    Returns number of Large Debris not collected by CT agents
    """
    return len([a for a in model.schedule.agents if isinstance(a,LargeDebris) and a.state not in (UNDERWAY, DONE)])

def pending_Debris(model):
    """
    Returns number of Debris not collected by LC agents
    """
    return len([a for a in model.schedule.agents if isinstance(a,Debris) and a.state not in (UNDERWAY, DONE)])

def get_busy_CT(model):
    return len([a for a in model.schedule.agents if isinstance(a,CT_Robot) and a.state in (PICKING, CHARGING, EMPTYING)])

def get_exploring_CT(model):
    return len([a for a in model.schedule.agents if isinstance(a,CT_Robot) and a.state == EXPLORING])
"""
def get_charge_time(model):
    if len([a for a in model.schedule.agents if isinstance(a,LargeDebris)]) == 0:
        return
    CTs = [a for a in model.schedule.agents if isinstance(a,CT_Robot) and a.state==CHARGING]
    
    if CTs:
        for CT in CTs:
            model.cum_charge_time += 1
        
    return model.cum_charge_time
    """

def get_busy_LC(model):
    return len([a for a in model.schedule.agents if isinstance(a,LC_Robot) and a.state in (PICKING, EMPTYING)])

def get_exploring_LC(model):
    return len([a for a in model.schedule.agents if isinstance(a,LC_Robot) and a.state == EXPLORING])

def get_CT_efficiency(model):
    CTs = [a for a in model.schedule.agents if isinstance(a,CT_Robot)]
    CT_efficiency = []
    for CT in CTs:
        if CT.total_collected != 0:
            CT_efficiency.append((CT.unique_id, CT.charge_spent,CT.total_collected))

    return CT_efficiency




class Beach(mesa.Model):
    """ Model representing a beach full of trash"""
    def __init__(self, n_CT_robots, n_LC_robots, n_obstacles, n_debris, n_Ldebris, EXTENDED, width=NUMBER_OF_CELLS, height=NUMBER_OF_CELLS, seed=123):
        self.tick = 0
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

            self.datacollector = mesa.DataCollector(
            model_reporters={
                            "pending_LDebris": pending_LDebris,
                            "pending_Debris": pending_Debris,
                            "busy_CT": get_busy_CT,
                            "exploring_CT": get_exploring_CT,
                            "busy_LC": get_busy_LC,
                            "exploring_LC": get_exploring_LC,
                            "CT_efficiency": get_CT_efficiency
            }, 
            agent_reporters={
                            "state": "state",
                            "charge": "charge"
            })

            
        self.running = True


    def step(self):
        """
        * Run while there are Undone Debris, otherwise stop running model.
        """
        self.tick += 1
        
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

        self.datacollector.collect(self)               


    def run_model(self) -> None:
        while len([a for a in self.schedule.agents if isinstance(a,LargeDebris) and a.state == DONE]) < self.n_Ldebris and len([a for a in self.schedule.agents if isinstance(a,Debris) and a.state == DONE]) < self.n_debris:
            self.step()
        