# Future deployment contract, not deployment approval

This exact profile was tested on CPython 3.10.12, Linux x86_64. Bootstrap: pip 26.2.1 and setuptools 84.0.0 from hash-locked wheels. Application: 25 packages in requirements-future-deploy.lock. Use only verified wheel bytes with --no-index --only-binary=:all: --require-hashes, then pip check and compare installed metadata and physical package hashes. No sdist builds, automatic resolver upgrade or untested optional extras.

A future deployment must recover all 25 wheel artifacts from the verified artifact records, including locally built sgmllib3k 1.0.0. That wheel is not published by this change. Do not call this a ready one-command public-index install. Existing Geo >= constraints alone are not this tested profile. GNews and trafilatura extras remain outside this lock and must stay off until separately tested.

This change does not create a Render service, select a build command there, update an OS/base image, stop a collector, create indexes, write to a database or send messages. No deployed dependency or provider closure claim. The 130 historical candidate alerts remain open and visible at their unchanged paths. Package-level remediation for 18 operational-source alert occurrences is separate from provider reindexing and deployment.

Retained limits: Windows safe_join tested only Linux string branch, not Windows filesystem; BSON >2GiB overflow not executed; no live Mongo tests. Old-bootstrap1150 author logs not independently rerun. Freshselected1150 ID set independently verified, not an independent entire-suite execution. Bootstrap26.2.1/setuptools84 tested; sgmllib existing local wheel reused, not rebuilt with new bootstrap. No build command/service selected.
