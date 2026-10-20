# Examples site

The project homepage and one example gallery per image engine. It is a small Django
project, exported to static files and published to https://mariocesar.github.io/sorl-thumbnail/
by `.github/workflows/pages.yml`.

## Run it

```sh
uv run --group demo demo/manage.py runserver
```

`uv run` creates `.venv`, installs sorl and the `demo` dependency group from `pyproject.toml`
at the versions in `uv.lock`, and runs the command. Without uv, `pip install -e . --group demo`
(pip 25.1 or later) and drop the `uv run --group demo` prefix.

Edit a template in `examples/` and refresh. Each engine has its own settings module, like
`tests/settings/`:

```sh
uv run --group demo demo/manage.py runserver --settings=demo.settings.imagemagick
```

Thumbnails are cached in `media/cache/`. Delete it if you change a source image.

## Export it

```sh
uv run --group demo demo/manage.py build                  # every engine, then checksite
uv run --group demo demo/manage.py build --engines pil    # only Pillow, the rest get a page without results
uv run --group demo demo/manage.py render --settings=demo.settings.wand   # one engine's page
uv run --group demo demo/manage.py checksite              # check what is in site/
python -m http.server -d site                             # look at the export
```

CI runs `uv run --locked --group demo demo/manage.py build --require pil,imagemagick,graphicsmagick,wand`.
To update Django, Pillow or Wand, run `uv lock --upgrade` and commit `uv.lock`.

## What's where

- `examples/<id>.html`: one `{% thumbnail %}` template per example. The page shows this
  text next to what it renders.
- `examples.py`: the sections and examples in order, the source image credits, and what
  each engine can't do. An example that needs an unsupported option is shown, not run.
- `views.py`: `home` and `gallery`, and the context functions the export reuses.
- `settings/`: `base.py` plus one module per engine.
- `management/commands/`: `render` exports one engine, `build` runs `render` once per engine
  in its own process (sorl's settings are process-wide) and then `checksite`.
- `media/images/`: the committed source images, see its README for credits.

`render` fails on any sorl error, including ones sorl only logs. `checksite` reads the
exported HTML back and checks that every link, anchor and image resolves, and that each
image decodes to the format and size the page claims.

## Add an example

Write `examples/<id>.html` and add a line to `EXAMPLES` in `examples.py`. If an engine can't
run it, name the option it needs in that line and add it to the engine's `unsupported`.

## Add an engine

Add `settings/<key>.py` and an entry in `ENGINES` in `examples.py`, then decide whether CI
should `--require` it.
