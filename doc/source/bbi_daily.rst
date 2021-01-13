==============================
Automated tests with bbi_daily
==============================

BBI stands for *BrainVISA Build Infrastructure*. The ``casa_distro_admin
bbi_daily`` command orchestrates this process in a given BBE (BrainVISA Build
Environment, a directory that serves as a *base directory* for casa-distro).
The ``bbi_daily`` command will run the following main steps, while (optionally)
logging detailed output to a Jenkins server:

1. Self-update casa_distro with ``git pull``;

2. Update the ``casa-run`` and ``casa-dev`` images from the BrainVISA website;

3. Run a compilation in a dev environment (``bv_maker sources``, ``bv_maker
   configure``, ``bv_maker build``, ``bv_maker doc``);

4. Run all tests that would be run by ``bv_maker test`` in the dev environment;

5. Install the compiled software in a new *user image* based on the
   ``casa-run`` image (the software is installed under ``/casa/install``);

6. Run the tests in the user image.


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

2. Create a directory dedicated to the nightly builds and change to it::

     export CASA_BASE_DIRECTORY=/volatile/a-sac-ns-brainvisa/bbi_nightly
     mkdir "$CASA_BASE_DIRECTORY"
     cd "$CASA_BASE_DIRECTORY"

   This directory will be the *base directory* for your *BrainVISA Build
   Environment* (*BBE*).

3. Create the ``jenkins_auth`` file in the *BBE base directory*. This text file
   must consist of two lines: the first line contains the username on the
   Jenkins server, the second line contains the *token* that can be generated
   in the Jenkins web interface (click on the user on top right corner, select
   *Configure* and create a new API token). This token will be used instead of
   the account password to upload build results. One advantage of using a token
   is the possibility to revoke it at any time. It is recommended to use one
   token per BrainVISA Build Environment and name the token accordingly.

4. Download the ``casa-dev`` image::

     wget http://brainvisa.info/download/casa-dev-ubuntu-18.04.sif

   :note: Until the BrainVISA 5.0 release, you need to replace
          ``brainvisa.info`` by ``new.brainvisa.info``. Also, you need to
          export this environment variable for casa-distro to find the images
          in later steps: ``export
          BRAINVISA_PUBLISH_SERVER=new.brainvisa.info``.

5. Create a directory for your development environment and set it up::

     cd "$CASA_BASE_DIRECTORY"
     mkdir brainvisa-master-ubuntu-18.04
     singularity run --bind "$(pwd)"/brainvisa-master-ubuntu-18.04:/casa/setup \
         casa-dev-ubuntu-18.04.sif distro=brainvisa branch=master

6. Edit the ``conf/svn.secret`` file with your BioProj login and password.

7. Check out and compile an initial build::

     "$CASA_BASE_DIRECTORY"/brainvisa-master-ubuntu-18.04/bin/bv \
         opengl=container bv_maker

9. Download the ``casa-run`` image::

     "$CASA_BASE_DIRECTORY"/brainvisa-master-ubuntu-18.04/bin/casa_distro \
         pull_image image=casa-run-ubuntu-18.04.sif

10. Create an inital user image. You may need to set the ``SINGULARITY_TMPDIR``
    environment variable to a disk with enough free space (about twice the size
    of the final user image)::

      export SINGULARITY_TMPDIR=/volatile/tmp
      "$CASA_BASE_DIRECTORY"/brainvisa-master-ubuntu-18.04/bin/casa_distro_admin \
          create_user_image \
          version=nightly \
          environment_name=brainvisa-master-ubuntu-18.04 \
          name=brainvisa-master-ubuntu-18.04-nightly

    - ``environment_name`` is the name of the development environment.
    - ``name`` is the full name of the created user image. We change it from the
    default, because we need it to be fully explicit: it will be the named
    displayed on the Jenkins page.

11. Install the *environment* for your new user image::

      cd "$CASA_BASE_DIRECTORY"
      mkdir brainvisa-master-ubuntu-18.04-nightly
      singularity run --bind "$(pwd)"/brainvisa-master-ubuntu-18.04-nightly:/casa/setup \
          brainvisa-master-ubuntu-18.04-nightly.sif

12. Edit ``brainvisa-master-ubuntu-18.04-nightly/conf/casa_distro.json`` by
    changing the ``distro`` and ``version`` keys to their correct values
    (create them if they are missing). In our example::

      "distro": "brainvisa",
      "version": "nightly"

    This should not be needed anymore when `issue #201
    <https://github.com/brainvisa/casa-distro/issues/201>`_ is fixed.

13. Check that the whole ``bbi_daily`` process is able to run successfully::

      "$CASA_BASE_DIRECTORY"/brainvisa-master-ubuntu-18.04/bin/casa_distro_admin \
          bbi_daily dev_tests=no user_tests=no

    Beware that the output of each step is displayed only when that step is
    finished, so the command may seem to hang for a long time.

14. Set the ``bbi_command`` to run on a regular basis using ``crontab -e``::

      MAILTO=your.email@host.example
      37 5 * * * PATH=/usr/local/bin:/usr/bin:/bin CASA_BASE_DIRECTORY=/volatile/a-sac-ns-brainvisa/bbi_nightly SINGULARITY_TMPDIR=/volatile/tmp /volatile/a-sac-ns-brainvisa/bbi_nightly/brainvisa-master-ubuntu-18.04/bin/casa_distro_admin bbi_daily jenkins_server='https://brainvisa.info/builds'

    :note: Remember to set all the needed environment variables, including
           ``BRAINVISA_PUBLISH_SERVER``. ``PATH`` may need to be set
           additionally, in case your Singularity installation is under
           ``/usr/local`` (by default cron limits ``PATH`` to
           ``/usr/bin:/bin``).
