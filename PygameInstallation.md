# For Image Manipulation Only #

For now I only want to use the image ops in Pygame with PNGs (this is for [gheat](http://code.google.com/p/gheat/))

  * libX11 (e.g., from [ports](ftp://ftp.freebsd.org/pub/FreeBSD/ports/i386/packages-6-stable/x11/))
  * [libpng](http://www.libpng.org/pub/png/libpng.html) (source is straightforward dance; well, libtool 2.2 died for me on production box so I had to install [libtool 2.2.2](http://www.gnu.org/software/libtool/) and then link it in the libpng src dir after running ./configure)
  * [SDL](http://www.libsdl.org/) (straightforward)
  * [SDL\_image](http://www.libsdl.org/projects/SDL_image/) (almost straightforward; need to first `export CPPFLAGS=-I/usr/local/include` to pick up png.h)

Install those four deps, then download and unpack [pygame](http://pygame.org/) and run:

```
python setup.py build
```

You should get a warning that you don't have all dependencies, with a confirmation to proceed:

```
[gheat] silouan$ python setup.py build


WARNING, No "Setup" File Exists, Running "config.py"
Using UNIX configuration...


Hunting dependencies...
smpeg-config: not found
WARNING: "smpeg-config" failed!
SDL     : found 1.2.13
FONT    : not found
IMAGE   : found
MIXER   : not found
SMPEG   : not found
PNG     : found
JPEG    : found
SCRAP   : found


Warning, some of the pygame dependencies were not found. Pygame can still
compile and install, but games that depend on those missing dependencies
will not run. Would you like to continue the configuration? [Y/n]:
```

Go ahead and proceed. It will then probably die for one reason or another (first pass for me was because no X11; second pass once /usr/local/include was on header search path was because PNG/JPEG/SCRAP were found when we didn't want them--we don't want them because we are using SDL's built-in PNG/JPEG support and we don't know what SCRAP is and it was breaking). So then edit Setup and comment out the PNG, JPEG, SCRAP, scrap, display, and event lines. Then rerun setup.py build and then install.

You need to tweak the environment (per [this example](http://www.pygame.org/wiki/HeadlessNoWindowsNeeded)):

```
os.environ['SDL_VIDEODRIVER'] = 'dummy'
```

And then you can use (parts of) pygame!

Also need [NumPy](http://numpy.scipy.org/) for pixel access. This can be installed at any time, although for version 1.0.4 you'll need to apply [this patch](http://scipy.org/scipy/numpy/ticket/618) before installing on FreeBSD. ([re: PixelArray vs. surfarray](http://archives.seul.org/pygame/users/Aug-2007/msg00334.html))

Ugh. 1.8 has buggy PNG saving; need the changes in [this rev](http://www.seul.org/viewcvs/viewcvs.cgi?rev=1205&root=PyGame&view=rev). I just used trunk. This is fixed in 1.8.1

Ugly X dependency problems on production box. Worked: installed [sdl](http://www.freebsd.org/cgi/cvsweb.cgi/ports/devel/sdl12/) as a [package](ftp://ftp.freebsd.org/pub/FreeBSD/ports/i386/packages-6-stable/devel/) ... but not until after I [cleaned up ports/pkgs](http://www.onlamp.com/pub/a/bsd/2001/11/29/Big_Scary_Daemons.html).

# Standalone Install #

I wanted to install SDL/Pygame in a sandbox, not globally. The system I was on already had X11 and libpng, so I was starting with SDL/SDL\_image. I installed these using `./configure --prefix=`. Here's a helpful message from SDL\_image:

```
Libraries have been installed in:
   /home/chad.whitacre/foo/lib

If you ever happen to want to link against installed libraries
in a given directory, LIBDIR, you must either use libtool, and
specify the full pathname of the library, or use the `-LLIBDIR'
flag during linking and do at least one of the following:
   - add LIBDIR to the `LD_LIBRARY_PATH' environment variable
     during execution
   - add LIBDIR to the `LD_RUN_PATH' environment variable
     during linking
   - use the `-Wl,--rpath -Wl,LIBDIR' linker flag
   - have your system administrator add LIBDIR to `/etc/ld.so.conf'

See any operating system documentation about shared libraries for
more information, such as the ld(1) and ld.so(8) manual pages.
```

Pygame's setup.py calls config.py to build a Setup file before running itself. You can tell config.py where to find SDL using environment variables as follows:

```
$ SDL_CONFIG=/home/chad.whitacre/foo/bin/sdl-config LOCALBASE=/home/chad.whitacre/foo python setup.py install --home=/home/chad.whitacre/foo
```

(--home puts stuff in lib/python; --prefix uses lib/pythonx.y)