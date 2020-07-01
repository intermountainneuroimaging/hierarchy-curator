# Custom Curation Gear
There are a lot of cases where specific logic must be used to curate a given project. 
This custom curation gear is able to take an implementation of the Curator Class 
(provided as an input file (e.g., curator.py)), instantiate it and 
execute it on a project, walking down the hierarchy through project, subject, session, 
acquisition, analysis and file containers.

## Gear Inputs

### Required
* **curator**: Python script (e.g. curator.py) that implemented the `Curator` class. 
More details [below](#curator-class).
### Optional
* **input_file_one**: Additional file to be used by the curator. 
* **input_file_two**: Additional file to be used by the curator.
* **input_file_three**: Additional file to be used by the curator.

## <a name="curator-class"></a>The Curator Class
The curator class must be defined in a python script which is provided to the gear
as an input. This class must be named `Curator` and must inherit from `curator.Curator`
class:
```python
import curator

class MyCurator(curator.Curator):
    ...
```

Examples of such scripts can be found in the examples [folder](./examples)

### Curate Methods
The Curator Class must define curate methods for each container type 
(excluding groups and collections). For each container, the method is 
called `curate_<container_type>`. The method takes the container as an input.

For example, for the project container the curation method is defined as:
```python
    def curate_project(self, project):
        ...
```

This pattern is consistent for all containers. For the files container the method is 
named `curate_file` and takes `file_` as input (note the underscore).

### Validate Methods
In addition to the curate methods, the implementation can inherit _validate_ methods 
specific to each container. By default these methods will always return `False`. 
However, if, for example, curating a file is a time consuming process, it may be useful 
to tag a file during the curation method and check for that tag elsewhere in the 
validate method. Below is an example of how one might accomplish that:

```python
import curator

class Curator(curator.Curator):
	...
	def curate_file(self, file_):
		"""Curates a file by setting the field 'file.info.curated' to True"""
		file_.update_info({'curated': True})
	...
	def validate_file(self, file_):
		"""Checks to see if a file has already been curated"""
		return file_.info.get('curated', False)
```

As shown in the `validate_file` method, the method should return `True` if the 
container does not need to be curated and `False` if it does.

### Input files
There are many cases where custom curation may require the use of input files. 
This gear provides mechanisms to utilize _optional_ input files.

NOTES:
1. These input files are optional, thus it is necessary to gracefully handle cases 
where the input files do not exist.
2. The gear  allows for the use of up to three input files.

The input files can be accessed within the curator class. The path to the input files 
are stored within the attribute named `input_file_one`, `input_file_two` and 
`input_file_three`.

Below is an example of a Project curation method using the first input file:
```python
def curate_project(self, project):
	if self.input_file_one:
		with open(self.input_file_one, 'r') as input_file:
			for line in input_file:
				project.add_note(line)
```
