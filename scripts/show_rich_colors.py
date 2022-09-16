#!/usr/bin/env python
# Prints examples of ~1000 ASCII colors so you can pick one.

from rich.console import Console
from rich.text import Text

STYLES_TO_OUTPUT = ['', 'bold', 'dim', 'reverse']
BACKGROUNDS = [1, 2, 3, 4, 5, 6, 7]
STATEMENT = 'color'
BG_STATEMENT = 'on bg'
SPACER = ' ' * 3


console = Console(color_system='256', highlight=False)

for i in range(256):
    texts = [
        Text('{0: >{width}}'.format(f"{STATEMENT} {i} {style}", width=len(STATEMENT) + 5 + len(style)), style=f"color({i}) {style}")
        for style in STYLES_TO_OUTPUT
    ]

    texts.append(Text(f'on background {i}', style=f'on color({i})'))

    for bg in BACKGROUNDS:
        txt = Text('{0}'.format(f" {BG_STATEMENT} {bg} "), style=f"color({i}) on color({bg})")
        texts.append(txt)

    text = Text()

    for t in texts:
        text.append(t)
        text.append(SPACER)

    console.print(text)


console.print("To view rich defaults:\n  python -m rich.default_styles\n  python -m rich.theme\n")
