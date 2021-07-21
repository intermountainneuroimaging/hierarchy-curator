## Debugging multiprocessing
Unfortunately debugging multiprocessing is not the easiest thing to do.  The best way to debug is to manually add in the builtin `breakpoint()` wherever you want to set the trace (beginning `multiprocessing.Process` target usually), and then set your `PYTHONBREAKPOINT` env var to `remote_pdb.set_trace`:

```python
nrichman:hierarchy-curator/ (GEAR-1134-multi-thread✗) $ PYTHONBREAKPOINT=remote_pdb.set_trace poetry run pytest -k test_curate_main_depth_first -s
...
platform linux -- Python 3.9.2, pytest-6.2.4, py-1.10.0, pluggy-0.13.1
...
collected 6 items / 4 deselected / 2 selected
...
DEBUG:fw_gear_hierarchy_curator.curate - Populator:Found file, ID: 6497409e-82f0-f654-aee1-27d86deac32e
CRITICAL:remote_pdb:RemotePdb session open at 127.0.0.1:34975, waiting for connection ...
RemotePdb session open at 127.0.0.1:34975, waiting for connection ...
CRITICAL:remote_pdb:RemotePdb session open at 127.0.0.1:37947, waiting for connection ...
RemotePdb session open at 127.0.0.1:37947, waiting for connection ...
```
You can then connect to the remote session via `telnet` such as:

```bash
nrichman:~/ (master✗) $ telnet 127.0.0.1 34975                                                                           [18:44:27]
Trying 127.0.0.1...
Connected to 127.0.0.1.
Escape character is '^]'.
> /work/flywheel/flywheel-apps/hierarchy-curator/fw_gear_hierarchy_curator/curate.py(42)worker()
-> local_curator = copy.deepcopy(curator)
(Pdb)
```

