Imagefapper: A Command Line API For Downloading imagefap.com galleries
======================================================================

*Note*: This requires Python (2.7 or 3.4 should suffice).

Installation
------------

Get the code in repository, either via `git`:

::

    git clone https://github.com/kinkstruction-admin/imagefapper.git


Or by clicking on the "Download Zip" button on the GitHub page that you're (ostensibly) looking at right now, and unzip the zip file.

Once you've done that, go into the folder into which you cloned/unzipped the code, and do the following:

::

    python setup.py install


Usage
-----

Once you install this package, you'll have a command line program called `imagefapper`. Go into the directory in which you want to download your porn, and do:

::

    imagefapper <url of the gallery that you want to download>


And all of the images will be downloaded! Voila!

The name of the subfolder in which the images lie will, by default, be based on the gallery name. This is, however, something you can specify.

::

    $ imagefapper --help
    Usage: imagefapper [OPTIONS] URL

      Download the imagefap.com gallery from URL.

    Options:
      --directory TEXT       Specify a directory (in .) to store images (if not
                             specified, the directory name is based off of the
                             gallery name)
      --num_threads INTEGER  The number of threads to use [default: 10]
      --version              Show the version and exit.
      --help                 Show this message and exit.
