#!/usr/bin/env python
import re, math
with open("log.log") as f:
    data=f.read()

def parse_data(data):
    """Parses all data in the chunk, returning, you know, stuff."""
    # Unlikely we'll find 20 significant numbers before our date is complete
    shortest = 20
    
    position_map = {
        'year': True,
        'month': True,
        'day': True,
        'hour': True,
        'minute': True,
        'second': True
    }

    sums = []

    positions = []

    for i in xrange(shortest):
        positions.append(position_map.copy())
        sums.append(0)

    month_map = {
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12
    }

    value_regex = re.compile("|".join(["\d+"] + month_map.keys())) 

    lines = []

    # We remove the first line because it may not be complete.
    for line in data.splitlines()[1:]:
        values = value_regex.findall(line)

        if len(values) < shortest:
            shortest = len(values)
            positions = positions[:shortest]
            sums = sums[:shortest]

        for position in xrange(len(positions)):
            # Convert month names to values
            if re.match('[a-zA-Z]+', values[position]):
                values[position] = month_map[values[position]]
            value = int(values[position])
            values[position] = value

            # Cascade down our exclusion list.  Add exclusions to the next match
            if value > 3000:
                for unit in positions[position]:
                    positions[position][unit] = False
            elif value > 60:
                for unit in positions[position]:
                    if unit != 'year':
                        positions[position][unit] = False
            elif value > 31:
                for unit in positions[position]:
                    if not re.match('year|minute|second', unit):
                        positions[position][unit] = False
            elif value > 24:
                for unit in positions[position]:
                    if not re.match('year|day|minute|second', unit):
                        positions[position][unit] = False
            elif value > 12:
                for unit in positions[position]:
                    if not re.match('year|day|hour|minute|second', unit):
                        positions[position][unit] = False
            elif value == 0:
                for unit in positions[position]:
                    if not re.match('year|hour|minute|second', unit):
                        positions[position][unit] = False

            sums[position] += value

        lines.append(values)

    averages = [ i / float(len(lines)) for i in sums ]

    meansums = []

    for i in xrange(shortest):
        meansums.append(0)

    # Calculate standard deviations
    for line in lines:
        for i in xrange(shortest):
            meansums[i] += (line[i] - averages[i]) ** 2
        
    deviations = [ math.sqrt(i / float(len(lines) - 1)) for i in meansums ]

    # Let's try to output this in a meaningful way

    template = "%10s" * shortest
    ftemplate = "%10.5f" * shortest

    for unit in [ 'year', 'month', 'day', 'hour', 'minute', 'second' ]:
        units = []
        for position in positions:
            units.append(unit if position[unit] else '')
        print template % tuple(units)

    for line in lines:
        print template % tuple(line[:shortest])

    print ftemplate % tuple(deviations)


parse_data(data)
