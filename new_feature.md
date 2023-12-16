# Ant Colony Optimisation
As there are a large number of LC agents on the beach at a given time, it is possible for them to benefit from swarm intelligence. One possible way of this is using a form of the ant colony optimisation algorithm (ACO).

For this activity the method of distributing debris around the beach was changed. The debris is no longer randomly distributed to each cell but scattered in n clusters randomly placed on the beach. This makes it harder for the LC agents to find debris on their own. When the LC agent fills its own payload, it has no memory of where the cluster it was cleaning was and will start to explore the beach with no prior knowledge, AGO offers a more efficient solution. In the context of ACO, the LC agents represent the ants and the debris clusters represent sources of food scattered in the environment.

Using ACO, we can program the LC agents to place pheromones as they return to the wastebin to deposit their payload. The Agent who comes across this trail will follow the trail to the source, where they will likely find a cluster of debris. If there are more than one trail, they will follow a probabilistic equation to decide which trail to follow if.

## Algorithm
The LC agents start as usual by exploring the environment until they discover debris to collect. Once their payload is full, they change state to EMPTYING and return to the wastebin creating pheromones as they move.
Any exploring/idle LC agent that comes across these pheromones will follow the trail to its source and start collecting the debris and then returning to the wastebin while leaving their own trail of pheromones. 
This creates a situation where the more LC agents collecting from a certain cluster, the more agents are likely to discover and follow the trail. This allows large clusters to be cleared more quickly compared to when the LC agents randomly searched the environment.

## Implementation
To implement this, a new agent was created call "Pheromone" which is created each time step as LC agents return to the wastebin. The pheromone contains the location of the next pheromone in the trail allowing the LC agent to follow the trail. The pheromone's strength reduces each time step until it reaches 0 and disappears. 

A new state was added to the LC design called FOLLOWING_TRAIL. A new state was necessary as its behaviour needs to be considerably different to any other state. An updated LC State-flow diagram has been made called "LC_Novel_Stateflow.jpg".

