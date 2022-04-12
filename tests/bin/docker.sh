#!/bin/bash
version=$(cat manifest.json | jq -r '.version')
echo $version
docker run -it --entrypoint=/bin/bash \
 -v $(pwd)/tests/assets/config.json:/flywheel/v0/config.json \
 -v $(pwd)/examples/test.py:/flywheel/v0/input/curator/curator.py \
 flywheel/hierarchy-curator:$version
