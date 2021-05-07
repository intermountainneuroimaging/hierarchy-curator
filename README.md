
# Custom Hierarchy Curation Gear
There are a lot of cases where specific logic must be used to curate a given project. 
This hierarchy curation gear is able to take an implementation of the HierarchyCurator Class 
(provided as an input file (e.g., curator.py)), instantiate it and 
execute it on a project, walking down the hierarchy through project, subject, session, 
acquisition, analysis and file containers.

## Description

The Hierarchy curator walks _down_ the hierarchy breadth-first by default.  The gear can be launched from any level in the Flywheel Hierarchy and has access to every container below and including the run container.

For example if the hierarchy curator is run from Subject level, the first container encountered when walking the hierarchy would be the Subject in which it was run, then it would walk to each session, then it would walk to each acquisition under those sessions, and finally each file under those acquisitions.

For each container encountered when walking the hierarchy, the curator will call `validate_<container>` to decide whether it should curate that container.  The `validate_<container>` by default returns True, but can be overriden with custom logic.

If `validate_<container>` returns True, then `curate_<container>` is called.  In `curate_<container>`, you have access to the SDK model of that container and the class instance.  

You can save information from any level into the class insance itself, and then access that lower down.  For example if you wanted to set file level information based on subject metadata, you could write a curator like the following:

```python
from flywheel_gear_toolkit.utils.curator import HierarchyCurator

class Curator(HierarchyCurator):

	def curate_subject(self, sub):
		self.sub_label = sub.label

	...
	def curate_file(self, file_):
		if file_.type is 'dicom':
			file_.update_info({'PatientID':self.sub_label})
```

## Gear Inputs

### Required
* **curator**: Python script (e.g. curator.py) that implemented the `HierarchyCurator` class. 
More details at the [Flywheel Gear Toolkit docs](https://gear-toolkit.readthedocs.io/en/latest/utils.html#curator).
### Optional
* **additional_input_one**: Additional file to be used by the curator. 
* **additional_input_two**: Additional file to be used by the curator.
* **additional_input_three**: Additional file to be used by the curator.

## HierarchyCurator
The curator class must be defined in a python script which is provided to the gear
as an input. This class must be named `Curator` and must inherit from `flywheel_gear_toolkit.utils.curators.HierarchyCurator`
class:
```python
from flywheel_gear_toolkit.utils.curator import HierarchyCurator

class Curator(HierarchyCurator):
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
from flywheel_gear_toolkit.utils.curator import HierarchyCurator

class Curator(HierarchyCurator):
	...
	def curate_file(self, file_):
		"""Curates a file by setting the field 'file.info.curated' to True"""
		file_.update_info({'curated': True})
	...
	def validate_file(self, file_):
		"""Returns True if file needs curation, False otherwise"""
		return not file_.info.get('curated', False)
```

As shown in the `validate_file` method, the method should return `True` if the 
container does need to be curated and `False` if it does not.

### Input files
There are many cases where custom curation may require the use of input files. 
This gear provides mechanisms to utilize _optional_ input files.

NOTES:
1. These input files are optional, thus it is necessary to gracefully handle cases 
where the input files do not exist.
2. The gear  allows for the use of up to three input files.

The input files can be accessed within the curator class. The path to the input files 
are stored within the attribute named `additional_input_one`, `input_file_two` and 
`additional_input_three`.

Below is an example of a Project curation method using the first input file:
```python
def curate_project(self, project):
    if self.input_file_one:
        with open(self.additional_input_one, 'r') as input_file:
            for line in input_file:
                project.add_note(line)
```

### Adding extra dependencies
The file-curator gear comes with the following python packages installed:
* lxml
* pandas
* nibabel
* Pillow
* piexif
* pydicom
* pypng
* flywheel-gear-toolkit
* fw-file

__Note__: See package versions in [./pyproject.toml](pyproject.toml)

If you need other dependencies that aren't installed by default, the gear-toolkit provides 
an interface to programmatically install dependencies.  You can specify extra packages in the `__init__` method.
```python
from flywheel_gear_toolkit.utils import install_requirements
...
class Curator(HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, extra_packages=["tqdm==x.y.z"])
```

### Breadth-first vs. depth-first traversal.

By default the walker used in HierarchyCuratror uses depth-first traversal, this can be adjusted by setting the `depth_first` attribute to either `True` or `False` in your `Curator` class.  

For example if you run the gear from subject `sub-01` and there are two sessions underneath each with two acquisitions, you might have a tree that looks like:

```bash
sub-01
├── ses-screening
│   ├── acq-anat1
│   │   └── T1w.dicom.zip
│   └── acq-func1
│       └── task1.dicom.zip
└── ses-visit1
   ├── acq-anat1
   │   └── T1w.dicom.zip
   └── acq-func1
       └── task1.dicom.zip
```

If you set your curator to run depth-first:
```python
from flywheel_gear_toolkit.utils import install_requirements
...
class Curator(HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.depth_first = True
```

Then your traversal order would be as follows:

```bash
sub-01                       1.
├── ses-screening            2. 
│   ├── acq-anat1            3.
│   │   └── T1w.dicom.zip    4. 
│   └── acq-func1            5.
│       └── task1.dicom.zip  6.
└── ses-visit1               7.
   ├── acq-anat1             8.
   │   └── T1w.dicom.zip     9.
   └── acq-func1             10.
       └── task1.dicom.zip   11.
```

Whereas if you want breadth first:

```python
from flywheel_gear_toolkit.utils import install_requirements
...
class Curator(HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.depth_first = False
```

your traversal order would be:

```bash
sub-01                       1.
├── ses-screening            2. 
│   ├── acq-anat1            4.
│   │   └── T1w.dicom.zip    8. 
│   └── acq-func1            5.
│       └── task1.dicom.zip  9.
└── ses-visit1               3.
   ├── acq-anat1             6.
   │   └── T1w.dicom.zip     10.
   └── acq-func1             7.
       └── task1.dicom.zip   11.
```




