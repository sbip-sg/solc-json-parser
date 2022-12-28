from functools import reduce
from pprint import pprint
srcmap = "387:340:0:-:0;;;;8:9:-1;5:2;;;30:1;27;20:12;5:2;387:340:0;;;;;;;"


def parse(srcmap):
    def _reduce_fn(accumulator, current_value):
        last, *tlist = accumulator
        return [
            {
                's': int(current_value['s'] or last['s']),
                'l': int(current_value['l'] or last['l']),
                'f': int(current_value['f'] or last['f']),
            },
            last,
            *tlist
        ]

    parsed = srcmap.split(";")
    parsed = [l.split(':') for l in parsed]
    t = []
    for l in parsed:
        if len(l) >= 3:
            t.append(l[:3])
        else:
            t.append(l + [None] * (3 - len(l)))
    parsed = [{'s': s if s != "" else None, 'l': l, 'f': f} for s, l, f in t]
    parsed = reduce(_reduce_fn, parsed, [{}])
    parsed = list(reversed(parsed[:-1]))
    print(len(parsed))
    return parsed

pprint(parse(srcmap))
pprint(srcmap.count(';')+1)

