# Release Notes

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

__Maintenance:__

* Adjust info/debugging log output in walker.

## 1.1.0
DOC:
* Add documentation on installing dependencies programatically
* Add documentation on configuration options for breadth/depth first walking
* Add example curator script to update file metadata based on subject metadata.
BUG:
* Clear up doc and CLI script to make sure we're passing in context to curator class, and not raw `flywheel.Client`
