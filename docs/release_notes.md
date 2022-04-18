# Release Notes

## 2.1.4

__Bug__:

* Fix bug in SDK not reloading `_parent` attribute `parent` property on files.
    * Revert fix for using `parent_ref` as that was treating a (not all) symptom of the
      above issue. Now we're fixing the cause.


## 2.1.3

__Maintenance__:

* Update readme
* Update to QA-CI

__Bug__:

* Use `parent_ref` to get parent container.

## 2.1.2

__Bug__:

* Enforce default curator `reload()` for legacy scripts
* `reload()` is also performed on `files` as well as containers by default

## 2.1.1

__Maintenance__:

* Restore default curator performing `reload()` on each container

## v2.0.0

__Enhancements:__

* Improve but change configuration for curator class
  * Configuration is now set via the `self.config` object, see README.md for more info.
  * Adds ability to stop walking at certain level of the hierarchy.
  * Adds ability to prevent queueing children via a custom callback.
* Expand on README
  * Configuration options
  * callback usage
  * validate_<container> methods.
* Add ability to run gear in a multi-threaded manner.

__Maintenance:__

* Adjust info/debugging log output in walker.
* Remove `__del__()` call in exception cleanup.

## 1.1.0

__Documenation__:

* Add documentation on installing dependencies programatically
* Add documentation on configuration options for breadth/depth first walking
* Add example curator script to update file metadata based on subject metadata.

__Enhancements__:

* Clear up doc and CLI script to make sure we're passing in context to curator class, and not raw `flywheel.Client`
