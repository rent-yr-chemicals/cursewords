# Abandon hope, all ye who enter here.

I'm so, so sorry.

### Installing

1. Stick `cursewords` somewhere python can import it.
2. Create the following directories (yes, you need to do this manually):
  - `~/.local/share/cursewords/`
  - `~/.local/share/cursewords/library/`
3. Make sure `cursewords.py` is executable.

### Launching

To launch the app, simply run `cursewords.py`.

To import a .puz file, use
```
cursewords.py [--source SOURCE] [file]
```
The optional `SOURCE` parameter sets the name that will appear in the "Source" field when browsing your puzzle collection.

### Configuring

Pretty much all the config is hard-coded. It'll look ugly unless your terminal uses custom colors. Might have broken glyphs unless you're using a [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) patched font. Looks best using a special version of `kitty` compiled to support extra box-drawing glyphs; this is not available anywhere on any platforms.

### Troubleshooting

Shut off your computer. Take a walk outside. Look at the clouds. Give your loved ones a call. Find peace.
