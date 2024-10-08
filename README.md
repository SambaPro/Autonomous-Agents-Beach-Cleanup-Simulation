# Beach Cleaning Simulation using Autonomous Agents
## Overview
This project is a beach cleanup simulation is written in Python using the Mesa framework. It was developed for a third year assignment for an Autonomous Agents module.

The simulation contains a 2x2 grid representing a beach with pieces of small and large debris. The agents consist of LCs (Lightweight Cleaning) robots that collect small debris and CTs (Cleaning Tanks) that collect large debris. Each agent can act individually and searches the beach for debris. Once full they return to the waste bin and deposit their payload. The simulation ends when all the debris is deposited in the waste bin.

The purpose of this simulation is to show how agents with simple behaviour can be used to complete complex tasks.

![Interface Image](https://github.com/SambaPro/Autonomous-Agents-Beach-Cleanup-Simulation/blob/main/images/Simulation.PNG "Browser based interface")

## How to Run
Run run.py file in src/beach/run.py
The interface will open in your default browser.
Requirements are listed in requirements.txt.

```sh
pip install -r requirements.txt
```

```python
python src/run.py
```

## Interface
The interface contains sliders and checkboxes that change the details of the simulation.
These can be active simultaneously.
 
### Extended Features
This toggle adds more complexity to the simulation.
- CTs now have batteries that slowly drain as they move. They must recharge at a recharge point before the charge reaches 0.
- There is a chance that new debris is added to the beach as the simulation progresses.
- LC robots create jobs which are bidded on by CT robots for the right to allocated to it. Bidding is based on distance to debris, current charge and current payload size. The winner is decided by plurality.

### Novel Features
This feature attempts to simulate behaviour shown by ants discovering and collecting food in the wild.
As LCs discover small debris they leave a pheremone trail as they return to the waste bin. Once LCs empty their payload they follow a trail back to a cluster of debris, thus reducing the amount of searching needed. This feature is further elaborated on in new_feature.md
