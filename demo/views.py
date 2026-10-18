import re
import subprocess
from datetime import date
from importlib.metadata import metadata

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.template import engines
from django.utils.safestring import mark_safe
from PIL import Image

import sorl
from demo.examples import ENGINES, EXAMPLES, HOME_HERO, SECTIONS, SOURCES

# How the options in ENGINES[...]['unsupported'] read in the engines table
GAPS = {'smart': 'smart crop', 'rounded': 'rounded corners', 'remove_border': 'border removal',
        'avif': 'AVIF output'}


def home(request):
    return render(request, 'index.html', home_context())


def gallery(request, engine):
    if engine not in ENGINES:
        raise Http404
    # Only the engine in these settings can render; others show their templates
    built = engine == settings.DEMO_ENGINE
    return render(request, 'gallery.html', gallery_context(engine, built))


def run(command):
    """First line a command prints, or '' if it fails."""
    try:
        out = subprocess.run(command, capture_output=True, text=True)
    except OSError:
        return ''
    return out.stdout.strip().splitlines()[0] if out.returncode == 0 and out.stdout else ''


def describe(url):
    """Format, size, frames and bytes of an image in MEDIA_ROOT, read back from the file."""
    path = settings.MEDIA_ROOT / url.removeprefix('media/')
    with Image.open(path) as im:
        text = '%s · %d×%d' % (im.format, im.width, im.height)
        frames = getattr(im, 'n_frames', 1)
    if frames > 1:
        text += ' · %d frames' % frames
    return text + ' · %.1f KB' % (path.stat().st_size / 1024)


def render_example(name, engine, run_it):
    """An example's template source, and its output when run_it and the engine supports it."""
    section, title, needs = next((s, t, n) for s, i, t, n in EXAMPLES if i == name)
    source = (settings.BASE_DIR / 'examples' / ('%s.html' % name)).read_text()
    # Each line with its indent, so wrapped rows can hang under it
    lines = [(len(line) - len(line.lstrip()), line) for line in source.splitlines()]
    example = {'id': name, 'section': section, 'title': title, 'lines': lines}
    if needs in ENGINES[engine]['unsupported']:
        example['skipped'] = 'Not run: %s.' % ENGINES[engine]['unsupported'][needs]
    elif run_it:
        try:
            html = engines['django'].from_string(source).render({})
        except Exception as e:
            e.add_note('while rendering demo/examples/%s.html' % name)
            raise
        example['html'] = mark_safe(html)
        example['details'] = [describe(url) for url in re.findall(r'src="(media/[^"]+)"', html)]
    return example


def site_context():
    root = settings.BASE_DIR.parent
    release = run(['git', '-C', root, 'describe', '--tags', '--abbrev=0'])
    sources = []
    for name, title, author, license, url in SOURCES:
        with Image.open(settings.MEDIA_ROOT / 'images' / name) as im:
            size = im.size
        src = 'media/images/' + name
        sources.append({'file': src, 'title': title, 'author': author, 'license': license,
                        'url': url, 'size': size, 'details': describe(src)})
    # Supported versions from the package's own classifiers in pyproject.toml
    classifiers = metadata('sorl-thumbnail').get_all('Classifier')
    django = [c[len('Framework :: Django :: '):] for c in classifiers
              if c.startswith('Framework :: Django :: ')]
    python = [c[len('Programming Language :: Python :: '):] for c in classifiers
              if c.startswith('Programming Language :: Python :: 3.')]
    return {
        'engines': [(key, engine['label']) for key, engine in ENGINES.items()],
        'django_versions': django,
        'python_versions': python,
        'sources': sources,
        'version': sorl.__version__,
        'commit': run(['git', '-C', root, 'rev-parse', '--short', 'HEAD']),
        'release': release,
        'release_date': release and run(['git', '-C', root, 'log', '-1', '--format=%as', release]),
        'built': date.today().isoformat(),
    }


def gallery_context(engine, built=True, reason=''):
    """The gallery for an engine. Not built shows the templates only, and the reason if any."""
    examples = [render_example(name, engine, built) for _, name, _, _ in EXAMPLES]
    sections = [{'id': key, 'title': title, 'intro': mark_safe(intro),
                 'examples': [e for e in examples if e['section'] == key]}
                for key, title, intro in SECTIONS]
    info = dict(ENGINES[engine], key=engine)
    version = run(info['version']) if built else ''
    return site_context() | {'page': 'gallery', 'engine': info, 'reason': reason,
                             'engine_version': version, 'sections': sections}


def home_context():
    engine = settings.DEMO_ENGINE
    return site_context() | {
        'engine': dict(ENGINES[engine], key=engine),
        'hero': render_example(HOME_HERO, engine, True),
        'engine_table': [dict(e, key=key, gaps=[GAPS.get(name, name) for name in e['unsupported']])
                         for key, e in ENGINES.items()],
    }
