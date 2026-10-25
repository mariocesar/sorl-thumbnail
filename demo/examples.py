"""The examples on the site, and what each engine can show. Plain data, read by views.py."""

import shutil
import sys
from importlib.util import find_spec

# Options an engine leaves out, as option: reason. Examples that need one are shown, not run.
EFFECTS = {
    'smart': 'smart cropping is only implemented by Pillow and libvips',
    'rounded': 'rounded corners are only implemented by Pillow and libvips',
    'blur': 'blur is only implemented by Pillow and libvips',
    'remove_border': 'border removal is only implemented by Pillow and libvips',
}
NO_PADDING = {'padding': 'this engine does not implement padding'}
BAD_PADDING = {'padding': 'with padding this engine reports the unpadded size, see '
                          'https://github.com/mariocesar/sorl-thumbnail/issues/835'}

# ImageMagick 7 has magick, 6 has convert and identify
MAGICK = 'magick' if shutil.which('magick') else 'convert'

# Settings live in demo/settings/<key>.py. install is for people, modules and tools for missing().
ENGINES = {
    'pil': {
        'install': 'pip install pillow',
        'label': 'Pillow',
        'modules': ['PIL'],
        'tools': [],
        'version': [sys.executable, '-c', 'import PIL; print("Pillow", PIL.__version__)'],
        'unsupported': {},
    },
    'vips': {
        'install': 'pip install sorl-thumbnail[vips]',
        'label': 'libvips',
        'modules': ['pyvips'],
        'tools': [],
        'version': [sys.executable, '-c', 'import pyvips; '
                    'print("libvips %d.%d.%d" % tuple(map(pyvips.version, range(3))))'],
        'unsupported': {},
    },
    'imagemagick': {
        'install': 'the ImageMagick commands',
        'label': 'ImageMagick',
        'modules': [],
        'tools': [MAGICK],
        'version': [MAGICK, '-version'],
        'unsupported': EFFECTS | BAD_PADDING,
    },
    'graphicsmagick': {
        'install': 'the gm command from GraphicsMagick',
        'label': 'GraphicsMagick',
        'modules': [],
        'tools': ['gm'],
        'version': ['gm', 'version'],
        'unsupported': EFFECTS | BAD_PADDING | {'avif': 'GraphicsMagick has no AVIF encoder'},
    },
    'wand': {
        'install': 'pip install wand, and ImageMagick',
        'label': 'Wand',
        'modules': ['wand'],
        'tools': [],
        'version': [sys.executable, '-c', 'import wand.version as v; print(v.MAGICK_VERSION)'],
        'unsupported': EFFECTS | NO_PADDING,
    },
    'pgmagick': {
        'install': 'pip install pgmagick',
        'label': 'pgmagick',
        'modules': ['pgmagick'],
        'tools': [],
        'version': [sys.executable, '-c', 'import pgmagick; print(pgmagick.gminfo().version)'],
        'unsupported': EFFECTS | NO_PADDING,
    },
}

SECTIONS = [
    ('geometry', 'Geometry', 'The geometry string sets the box the thumbnail must fit in: '
     'both sides, only the width, or only the height. The aspect ratio is kept.'),
    ('crop', 'Crop', 'With <code>crop</code> the thumbnail fills the whole box and the '
     'overflow is cut. Position it with CSS-like keywords, percentages or pixels.'),
    ('upscale', 'Upscale', 'Small sources are enlarged to the requested size unless '
     '<code>upscale=False</code>.'),
    ('formats', 'Formats', 'The output format is JPEG unless you ask for another one. '
     'Which formats work depends on the codecs the engine was built with.'),
    ('quality', 'Quality', 'JPEG quality trades file size for detail. Progressive JPEGs '
     'load in passes; the final image is the same.'),
    ('colorspace', 'Colorspace', 'Thumbnails are RGB by default. <code>GRAY</code> converts '
     'to grayscale.'),
    ('padding', 'Padding', 'With <code>padding</code> the thumbnail is centered on a '
     'canvas of the exact requested size.'),
    ('effects', 'Effects', 'Rounded corners, blur and border removal.'),
    ('animation', 'Animation', 'With GIF output, Wand and libvips keep every frame, and so '
     'does Pillow after 13.2.0 '
     '(<a href="https://github.com/mariocesar/sorl-thumbnail/issues/687">#687</a>). '
     'ImageMagick, GraphicsMagick and every other format take the first frame.'),
    ('orientation', 'Orientation', 'Photos are rotated following their EXIF orientation '
     'unless <code>orientation=False</code>. This test image is stored sideways.'),
    ('filters', 'Filters', '<code>is_portrait</code> tells you if an image is taller than wide, '
     'before making a thumbnail. <code>margin</code> centers a thumbnail in a fixed box.'),
]

# section, template in demo/examples/<id>.html, title, option it needs
EXAMPLES = [
    ('geometry', 'geometry-box', 'Fit in a box', None),
    ('geometry', 'geometry-width', 'Fixed width', None),
    ('geometry', 'geometry-height', 'Fixed height', None),
    ('crop', 'crop-center', 'Center crop', 'crop'),
    ('crop', 'crop-top', 'Top crop', 'crop'),
    ('crop', 'crop-bottom', 'Bottom crop', 'crop'),
    ('crop', 'crop-left', 'Left crop', 'crop'),
    ('crop', 'crop-right', 'Right crop', 'crop'),
    ('crop', 'crop-percent', 'Percentage offset', 'crop'),
    ('crop', 'crop-pixels', 'Pixel offset', 'crop'),
    ('crop', 'crop-noop', 'No-op crop', None),
    ('crop', 'crop-smart', 'Smart crop', 'smart'),
    ('crop', 'cropbox', 'Crop box', 'crop'),
    ('upscale', 'upscale-on', 'Upscaled (default)', None),
    ('upscale', 'upscale-off', 'Not upscaled', None),
    ('formats', 'format-jpeg', 'JPEG', None),
    ('formats', 'format-png', 'PNG', None),
    ('formats', 'format-webp', 'WEBP', None),
    ('formats', 'format-gif', 'GIF', None),
    ('formats', 'format-avif', 'AVIF', 'avif'),
    ('quality', 'quality-10', 'Quality 10', None),
    ('quality', 'quality-50', 'Quality 50', None),
    ('quality', 'quality-default', 'Quality 95 (default)', None),
    ('quality', 'progressive-off', 'Not progressive', None),
    ('colorspace', 'colorspace-rgb', 'RGB (default)', None),
    ('colorspace', 'colorspace-gray', 'Grayscale', 'colorspace'),
    ('padding', 'padding-default', 'White padding (default color)', 'padding'),
    ('padding', 'padding-color', 'Colored padding', 'padding'),
    ('effects', 'effects-rounded', 'Rounded corners', 'rounded'),
    ('effects', 'effects-blur', 'Blur', 'blur'),
    ('effects', 'effects-remove-border', 'Remove border', 'remove_border'),
    ('animation', 'animation-gif', 'GIF output', None),
    ('animation', 'animation-png', 'PNG output', None),
    ('orientation', 'orientation-on', 'Follow EXIF (default)', None),
    ('orientation', 'orientation-off', 'Ignore EXIF', None),
    ('filters', 'filter-is-portrait', 'is_portrait', None),
    ('filters', 'filter-margin', 'margin', None),
]

# Files in demo/media/images/
SOURCES = [
    ('mona-lisa.jpg', 'Mona Lisa', 'Leonardo da Vinci', 'Public domain',
     'https://commons.wikimedia.org/wiki/File:Leonardo_da_Vinci_-_Mona_Lisa.jpg'),
    ('earth-apollo-11.png', 'Earth from Apollo 11', 'NASA', 'Public domain',
     'https://commons.wikimedia.org/wiki/File:Earth_-_Apollo_11_-_1969-07-24_(48301755056).png'),
    ('caritas-romana.webp', 'Caritas Romana', 'Artemisia Gentileschi', 'Public domain',
     "https://commons.wikimedia.org/wiki/File:Artemisia_Gentileschi_'Caritas_Romana'.webp"),
    ('bouncing-ball.gif', 'Bouncing ball', 'Branko at English Wikipedia', 'Public domain',
     'https://commons.wikimedia.org/wiki/File:Animexample.gif'),
    ('kimono.avif', 'Kimono', 'Momiji Jinzamomi and Kaede Fujisaki', 'CC BY-SA 4.0',
     'https://github.com/link-u/avif-sample-images#kimono---transformation-tests'),
    ('fixtures/white_border.jpg', 'White border test image', 'sorl-thumbnail tests',
     'BSD-3-Clause', 'https://github.com/mariocesar/sorl-thumbnail/tree/main/tests/data'),
    ('fixtures/aspect_test.jpg', 'EXIF orientation test image', 'sorl-thumbnail tests',
     'BSD-3-Clause', 'https://github.com/mariocesar/sorl-thumbnail/tree/main/tests/data'),
]

HOME_HERO = 'crop-center'



def missing(key):
    """Python modules and commands this engine needs but can't find."""
    engine = ENGINES[key]
    names = [m for m in engine['modules'] if find_spec(m) is None]
    return names + [t for t in engine['tools'] if shutil.which(t) is None]
