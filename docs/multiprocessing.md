## Multiprocessing approach

The most straightforward approach would have been using one process to add containers to a `multiprocessing.Queue` and having a variable number of worker processes consume this queue and curate the containers in order.  Unfortunately, Flywheel containers aren't pickleable due to the SDK client being stored under each container so there is access to finders over child containers, etc.

Because this straightforward approach doesn't work with the SDK implementation there were two main approaches visited for implementint multiprocessing, and both had their own sets of drawbacks.

### Approach 1

In this approach we add the id and type (but not the entirety) of each container to a `multiprocessing.Queue` and pass this queue into each of the workers.  These workers continuously pop off the next container, pull it using the SDK, and then call the corresponding curate method on it.

__pros:__
* Easy to implement
    * No need to maintain order in worker threads, queue takes care of that
    * No need to create child curators/walkers

__cons:__ 
* Relatively API intensive:
    * Containers are queued using `iter_find()`, but then only their Id's are added to the queue.  Once they've been added to the queue they are found again using `get_<container_type>()`.  Effectively each container needs two calls ot the API
* Execution order is guarenteed with the queue, but saving data on the hierarchy to the class won't work.

#### Worker function.

The worker function would simply pop off the next element on the queue, pull it from the SDK and call the curator method on this container.  Since the queue will maintain the ordering, we don't need any special handling for depth-first or breadth-first.

### Approach 2

Don't use a `multiprocessing.Queue` at all, instead divy up subsections of the tree to each worker.  In this approach subsections of the tree would be given to each worker, and then each worker would instantiate its own walker and curator and traverse/curate it's section of the tree.

__pros:__
* Most efficient in terms of API calls since each container is only pulled once.

__cons:__
* Much more difficult to implement
    * instantiating a "child" curator from a "parent" one and having some shared attributes is not trivial
    * Hard to instantiate a separate SDK client on each container.
    * Need to maintain traversal order across sections of the tree

#### Worker function.

If depth first, the worker function would loop through the containers it was given and instaniate a local curator and a depth first walker with that container as root.  It would then walk through and curate that branch.

If breadth first, the worker function would instantiate one local curator and walker, add all of the containers it was given to that walker and walk through breadth first.


## Implementation
Even though approach two is harder to implement, it was the only one I could think of to guarentee execution order AND allow for information from higher up on the hierarchy to be persisted on the class.


### Child curator/SDK handling

The `HierarchyCurator` class now implements a custom `__deepcopy__` hook that shallow copies all attributes except the special `data` attribute. Therefore all child curators will refer to the same context/client and will have their own unique `data` attribute.


Additionally, the GearToolkit context has an additional `get_client()` method that is used to instantiate a client on the child curator.


### Traversal order:

__depth first__: Traversal order for depth-first should be reached if each container recieved by each worker instantiates another depth-first walker from that level
__breadth first__: Traversal order for bread-first should be reached if all containers recieved by each worker are added to a single breadth-first walker from that level.



