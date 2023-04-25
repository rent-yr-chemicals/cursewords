# Abandon hope, all ye who enter here.

I'm so, so sorry.

### Installing

To install, simply run the following:
```
git clone https://github.com/rent-yr-chemicals/cursewords.git
cd cursewords
pip install .
```
(It has been brought to my attention that another ncurses-powered crossword app with the name "cursewords" exists; running `pip install cursewords` will install _that other app_ instead, which will probably run better for you, but I will be sad)

### Launching

To launch the app, simply run `cursewords` from the command line.

To import a .puz file, use
```
cursewords [--source SOURCE] [file]
```
The optional `SOURCE` parameter sets the name that will appear in the "Source" field when browsing your puzzle collection.

### Configuring

Pretty much all the config is hard-coded. It'll look ugly unless your terminal uses custom colors. Might have broken glyphs unless you're using a [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) patched font. Looks best using a special version of `kitty` compiled to support extra box-drawing glyphs, which is not available anywhere on any platforms.

### Troubleshooting

Shut off your computer. Take a walk outside. Look at the clouds. Give your loved ones a call. Find peace.
