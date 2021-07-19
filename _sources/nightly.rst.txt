==============================
Automated tests with bbi_daily
==============================

BBI stands for *BrainVISA Build Infrastructure*. The ``casa_distro_admin
bbi_daily`` command orchestrates automated builds and tests in a given *base
directory*. This page is written as a guide to setting up automated tests, see
:ref:`bbi-daily-help` for the reference documentation.


Walkthrough
-----------

Here is a detailed log of how nightly builds are set up in NeuroSpin. You can
take inspiration from it to create your own personalized set-up.

1. Install ``singularity``. Configure the *fakeroot* functionality of
   Singularity, as explained `in the Singularity Admin Guide
   <https://sylabs.io/guides/3.7/admin-guide/user_namespace.html#fakeroot-feature>`_.
   In short, you need admin rights on your machine, and you have to run::

     sudo singularity config fakeroot --add $USER

   (with ``$USER`` being ``a-sac-ns-brainvisa`` in this case).

2. Create a directory dedicated to the nightly builds and ``cd`` into it::

     export CASA_BASE_DIRECTORY=/volatile/a-sac-ns-brainvisa/bbi_nightly
     mkdir "$CASA_BASE_DIRECTORY"
     cd "$CASA_BASE_DIRECTORY"

3. Create the ``jenkins_auth`` file in the *base directory*. This text file
   must consist of two lines: the first line contains the username on the
   Jenkins server, the second line contains the *token* that can be generated
   in the Jenkins web interface (click on the user on top right corner, select
   *Configure* and create a new API token). This token will be used instead of
   the account password to upload build results. One advantage of using a token
   is the possibility to revoke it at any time. It is recommended to use one
   token per BrainVISA Build Environment and name the token accordingly.


   :warning: You should make this file non-readable by others, e.g. create it
             with::
               chmod 0600 jenkins_auth

4. Download the ``casa-dev`` image using the link found on the Downloads page
   of <https://brainvisa.info/>. Also download the associated JSON file (to be
   extra safe, check that the md5sum of the image matches that stored in the
   JSON file).::

     wget https://brainvisa.info/download/casa-dev-5.0.sif
     wget https://brainvisa.info/download/casa-dev-5.0.sif.json
     md5sum casa-dev-5.0.sif

5. Create a directory for your development environment and set it up::

     cd "$CASA_BASE_DIRECTORY"
     mkdir brainvisa-master-5.0
     singularity run --bind ./brainvisa-master-5.0:/casa/setup \
         casa-dev-5.0.sif distro=brainvisa branch=master

6. Edit the ``conf/svn.secret`` file with your BioProj login and password.

7. Check out and compile an initial build while you do the rest of the
   configuration (until you run ``bbi_daily``)::

     "$CASA_BASE_DIRECTORY"/brainvisa-master-5.0/bin/bv_maker

8. Put the reference test data in
   ``"$CASA_BASE_DIRECTORY"/brainvisa-master-5.0/tests/ref/``. Best is to copy
   it from a known-good source.

9. ``bbi_daily`` will install the compiled software in a user image, create a
   fresh user environment from that user image, and run tests in there. You can
   control this process with a few optional parameters, that you should insert
   in the ``conf/casa_distro.json`` of the dev environment, as a new dictionary
   under the ``bbi_user_config`` key. Below is the list of keys in this
   dictionary with their default values::

     "bbi_user_config": {
         "name": "<dev_name>-userimage",
         "directory": "<dev_directory>/../<user_name>",
         "image": "{base_directory}/<user_name>{extension}",
         "version": "%Y-%m-%d"
     }

   Note that the value of ``version`` will be interpreted by
   :func:`time.strftime`.

10. Check that the whole ``bbi_daily`` process is able to run successfully::

      "$CASA_BASE_DIRECTORY"/brainvisa-master-5.0/bin/casa_distro_admin \
          bbi_daily

    This will take a long time. Beware that the output of each step is
    displayed only when that step is finished, so the command may seem to hang
    for a long time.

11. Set the ``bbi_daily`` command to run on a regular basis using ``crontab -e``::

      MAILTO=your.email@host.example
      37 5 * * * PATH=/usr/local/bin:/usr/bin:/bin CASA_BASE_DIRECTORY=/volatile/a-sac-ns-brainvisa/bbi_nightly SINGULARITY_TMPDIR=/volatile/tmp /volatile/a-sac-ns-brainvisa/bbi_nightly/brainvisa-master-5.0/bin/casa_distro_admin bbi_daily jenkins_server='https://brainvisa.info/builds'

    :note: Remember to set all the needed environment variables. ``PATH`` may
           need to be set additionally, in case your Singularity installation
           is under ``/usr/local`` (by default cron limits ``PATH`` to
           ``/usr/bin:/bin``).
