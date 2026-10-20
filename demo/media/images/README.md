# Example images

Source images for the examples site. They are committed so builds never download anything.

| File | Work | Author | License | Source | Changes |
|---|---|---|---|---|---|
| `mona-lisa.jpg` | Mona Lisa | Leonardo da Vinci | Public domain | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Leonardo_da_Vinci_-_Mona_Lisa.jpg) | Resized from 2403×3591 to 1071×1600, JPEG quality 88 |
| `earth-apollo-11.png` | Earth, Apollo 11, 1969-07-24 | NASA | Public domain | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Earth_-_Apollo_11_-_1969-07-24_(48301755056).png) | Resized from 7915×7123 to 1600×1440 |
| `caritas-romana.webp` | Caritas Romana | Artemisia Gentileschi | Public domain | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Artemisia_Gentileschi_%27Caritas_Romana%27.webp) | None, 1240×986 |
| `bouncing-ball.gif` | Animexample.gif | Branko at English Wikipedia | Public domain | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Animexample.gif) | None, 82×82, 6 frames |
| `kimono.avif` | Kimono | Momiji Jinzamomi and Kaede Fujisaki | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | [link-u/avif-sample-images](https://github.com/link-u/avif-sample-images#kimono---transformation-tests) | None, 722×1024 |

`fixtures/` has copies of two test images from `tests/data/`: `white_border.jpg` (100×100,
for border removal and smart crop) and `aspect_test.jpg` (200×100 stored with EXIF
orientation 6, for orientation).

Resized with Pillow `Image.thumbnail((1600, 1600), Image.LANCZOS)`. Downloaded 2026-10-17.

SHA-256:

```
42392f2f86d2ff7f3ef112b7b5fcb70246c51ff745593b2c71137515af19dd1a  bouncing-ball.gif
cb111f0159a60d0f5e938ce158d8c1f20999b16fa78c7e2e6b11432dd5d62152  caritas-romana.webp
bfe175de36ebc6a302bb0a6a51d794d2bd2b5754967ff7e2549215a5610fd2b7  earth-apollo-11.png
63412e0f67f37c8b6fcf0e8269a2afae0a017fa6a3a99d37d055c590b0be52d3  kimono.avif
0e60c763226797dc5f91c9805607d8c897c8d24d1f3eca1456dbd2fca41333ed  mona-lisa.jpg
```
