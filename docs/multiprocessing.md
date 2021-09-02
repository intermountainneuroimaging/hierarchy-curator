# Multiprocessing

[[_TOC_]]

## Implementation

Even though approach two is harder to implement, it was the only one I could
think of to guarantee execution order AND allow for information from higher up
on the hierarchy to be persisted on the class.

### Description

The main function of HierarchyCurator now does the following:

1. Instantiates a reporter for the class under `self.reporter` if one was
requested by `self.config.report = True` and starts its worker process
(See [Reporter](#Reporter) for description of reporter).
2. Distributes the children of the top level container evenly amongst workers.
3. Starts the workers
4. Listens for the `fail` event and kills remaining worker processes if one
fails. (See [Error Handling](#Errors) for more details)
5. Send termination signal to the reporter if there is a reporter.

### Child curator/SDK handling

The `HierarchyCurator` class now implements a custom `__deepcopy__` hook that
actually shallow copies all attributes except the special `data` attribute
(which is deepcopied). Therefore all child curators will refer to the same
context/client and will have their own unique `data` attribute.  Additionally,
we get around pickling of the client by instantiating a new client from cached
credentials with the gear toolkit `get_client()` method.

### Traversal order

__depth first__: Traversal order for depth-first should be reached if each
container received by each worker instantiates another depth-first walker
from that level.
__breadth first__: Traversal order for bread-first should be reached if all
containers received by each worker are added to a single breadth-first walker
from that level.

### Reporter

The reporter for multiprocessing works by storing a `Queue` managed by a
`multiprocessing.Manager` allowing it to be shared between processes.

When a curator in one of the worker functions calls `self.reporter.append_log`
behind the scenes, this actually pushes the log message to the `Queue`.
The reporter worker function then consumes values from this `Queue` and writes
them to the output (thread-safe).

> Note, a `Queue` managed by a `multiprocessing.Manager` is actually an instance
> of a `multiprocessing.managers.QueueProxy`

### Errors

Each worker function is passed an `Event` managed by a `Manager`.  The `main`
of the worker function is surrounded by a broad try-except.  When an uncaught
exception is raised, the worker will log the exception, and set this flag.
In the main process, this flag is monitored, and if set, triggers the
termination of all worker processes.

> Note, an `Event` managed by a `multiprocessing.Manager` is actually an instance
> of a `multiprocessing.managers.EventProxy`

### Additional inputs (I/O)

The HierarchyCurator allows for passing in of multiple input files.  However,
if multiple worker processes are trying to read one at the same time, it could
cause issues.  Therefore a special `open_input()` context manager should be
used to read from an input.  This context manager requests a lock on
`__enter__` and releases it on `__exit__` allowing only one worker process
to read from the input at any given time.

## Possible approaches

The most straightforward approach would have been using one process to add
containers to a `multiprocessing.Queue` and having a variable number of worker
processes consume this queue and curate the containers in order.
Unfortunately, Flywheel containers aren't pickleable due to the SDK client
being stored under each container so there is access to finders over child
containers, etc.

Because this straightforward approach doesn't work with the SDK implementation
there were two main approaches visited for implementing multiprocessing, and
both had their own sets of drawbacks.

### Approach 1

In this approach we add the id and type (but not the entirety) of each
container to a `multiprocessing.Queue` and pass this queue into each of the
workers.  These workers continuously pop off the next container, pull it using
the SDK, and then call the corresponding curate method on it.

__pros:__

* Easy to implement
  * No need to maintain order in worker threads, queue takes care of that
  * No need to create child curators/walkers

__cons:__

* Relatively API intensive:
  * Containers are queued using `iter_find()`, but then only their Id's are
    added to the queue.  Once they've been added to the queue they are found
    again using `get_<container_type>()`.  Effectively each container needs
    two calls to the API
* Execution order is guarenteed with the queue, but saving data on the
  hierarchy to the class won't work.

#### Worker function

The worker function would simply pop off the next element on the queue, pull it
from the SDK and call the curator method on this container.  Since the queue
will maintain the ordering, we don't need any special handling for depth-first
or breadth-first.

### Approach 2

Don't use a `multiprocessing.Queue` at all, instead divvy up subsections of the
tree to each worker.  In this approach subsections of the tree would be given
to each worker, and then each worker would instantiate its own walker and
curator and traverse/curate its section of the tree.

__pros:__

* Most efficient in terms of API calls since each container is only pulled once.

__cons:__

* Much more difficult to implement
  * instantiating a "child" curator from a "parent" one and having some shared
    attributes is not trivial
  * Hard to instantiate a separate SDK client on each container.
  * Need to maintain traversal order across sections of the tree

#### Worker function

If depth first, the worker function would loop through the containers it was
given and instantiate a local curator and a depth first walker with that
container as root.  It would then walk through and curate that branch.

If breadth first, the worker function would instantiate one local curator and
walker, add all of the containers it was given to that walker and walk through
breadth first.
