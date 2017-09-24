from textwrap import fill
from typing import List, Optional, Union

from mapi.exceptions import MapiNotFoundException

from mnamer.config import Config
from mnamer.parameters import Parameters
from mnamer.query import Query
from mnamer.target import crawl

TEXT_WIDTH = 80


# noinspection PyTypeChecker
def cformat(
    text,
    fg_colour: Optional[Union[str, List[str]]] = None,
    bg_colour: Optional[Union[str, List[str]]] = None,
    attribute: Optional[Union[str, List[str]]] = None
):
    opt_c = [
        'grey',
        'red',
        'green',
        'yellow',
        'blue',
        'magenta',
        'cyan',
        'white'
    ]
    opt_attr = [
        'bold',
        'dark',
        '',
        'underline',
        'blink',
        '',
        'reverse',
        'concealed'
    ]
    fg_colour_ids = dict(list(zip(opt_c, list(range(30, 38)))))
    bg_colour_ids = dict(list(zip(opt_c, list(range(40, 48)))))
    attr_ids = dict(list(zip(opt_attr, list(range(1, 9)))))
    styles = []
    if isinstance(fg_colour, str):
        fg_colour = [fg_colour]
    elif not fg_colour:
        fg_colour = []
    for x in fg_colour: styles.append(fg_colour_ids.get(x.lower() if x else ''))
    if isinstance(bg_colour, str):
        bg_colour = [bg_colour]
    elif not bg_colour:
        bg_colour = []
    for x in bg_colour: styles.append(bg_colour_ids.get(x.lower() if x else ''))
    if isinstance(attribute, str):
        attribute = [attribute]
    elif not attribute:
        attribute = []
    for x in attribute: styles.append(attr_ids.get(x.lower() if x else ''))
    for style in styles:
        if style: text = '\033[%dm%s' % (style, text)
    if any(styles): text += '\033[0m'
    return text


def cprint(
    text,
    fg_colour: Optional[Union[str, List[str]]] = None,
    bg_colour: Optional[Union[str, List[str]]] = None,
    attribute: Optional[Union[str, List[str]]] = None
):
    print(cformat(text, fg_colour, bg_colour, attribute))


def wprint(s: object) -> None:
    print(fill(
        str(s),
        width=TEXT_WIDTH,
        break_long_words=True,
        subsequent_indent='    ',
    ))


def main():
    cprint('\nStarting mnamer', attribute='bold')

    parameters = Parameters()
    config = Config(**parameters.arguments)
    targets = crawl(parameters.targets, **config)

    # Display config information
    for key, value in config.items():
        wprint(f"  - {key}: '{value}'")

    # Exit early if there are no files found
    if not targets:
        print('No suitable media files detected. Exiting.')

    # Begin processing files
    query = Query(**config)
    renamed_count = moved_count = 0

    for target in targets:
        print('\n', '- ' * (TEXT_WIDTH // 2), '\n')
        cprint(f'Detected File', attribute='bold')
        wprint(target.path.name)

        # Print metadata fields
        for field, value in target.meta.items():
            print(f'  - {field}: {value}')

        # Print search results
        cprint('\nQuery Results', attribute='bold')
        results = query.search(target.meta)
        i = 1
        entries = []
        max_hits = int(config.get('max_hits', 100))
        while i < max_hits:
            try:
                entry = next(results)
                print(f"  [{i}] {entry}")
                entries.append(entry)
                i += 1
            except (StopIteration, MapiNotFoundException):
                break

        # Skip entry if no hits
        if not entries:
            cprint('  - None found! Skipping...\n', fg_colour='yellow')
            continue

        # Prompt user for input
        print('  [RETURN] for default, [s]kip, [q]uit')
        meta = abort = skip = None
        while not any({meta, abort, skip}):
            selection = input('  > Your Choice? ')

            # Catch default selection
            if not selection:
                meta = entries[0]
                break

            # Catch skip entry (just break w/o changes)
            elif selection in ['s', 'S', 'skip', 'SKIP']:
                skip = True
                break

            # Quit (abort and exit)
            elif selection in ['q', 'Q', 'quit', 'QUIT']:
                abort = True
                break

            # Catch result choice within presented range
            elif selection.isdigit() and 0 < int(selection) < len(entries) + 1:
                meta = entries[int(selection) - 1]
                break

            # Re-prompt if user input is invalid wrt to presented options
            else:
                print('\nInvalid selection, please try again.')

        if skip is True:
            cprint(
                '  - Skipping rename, as per user request...',
                fg_colour='yellow')
            continue

        elif abort is True:
            cprint(
                '  - Exiting, as per user request...',
                fg_colour='red')
            exit(0)

        # Process file
        cprint('\nProcessing File', attribute='bold')
        destination = config[f"{target.meta['media']}_destination"]

        wprint(f"  - renaming to '{meta.format(template)}'")
        if destination:
            target.move(destination)
            wprint(f"  - moving to '{destination}'")

        cprint('  - Success!', fg_colour='green')


if __name__ == '__main__':
    main()