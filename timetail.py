#!/usr/bin/env python
import re, math
from optparse import OptionParser

def _parse_args():
    """Parses arguments and displays usage"""
    usage = """%prog [options] file1 [... fileN]"""
    parser = OptionParser(usage = usage)
    options, args = parser.parse_args()
    return options, args

def cross_logic_pass(positions, unit_names, position_map):
    """Determines (very inefficiently) whether any unit from [unit_names] fills
    exactly one position in [positions].  If so, put the "index" of that unit's
    location into [position_map].  All other units in that position must be
    False.

    Returns a dict with the counts for each unit type.
    """
    unit_counts = { name: 0 for name in unit_names }

    for position in positions:
        for unit in position:
            if position[unit]:
                unit_counts[unit] += 1

    for position in xrange(len(positions)):
        for unit in positions[position]:
            if positions[position][unit] and unit_counts[unit] == 1:
                position_map[unit] = position
                # We should make all other units in this position false
                for unitchanger in positions[position]:
                    if unitchanger != unit:
                        positions[position][unitchanger] = False
    print_units(unit_names, positions)
    return unit_counts

def get_minimum_possible_deviation_index(unit,
                                         position_map,
                                         deviations,
                                         positions):
    """Returns the index of [positions] where [deviations], in a possible
    location of [unit], has the lowest value, weighted for position (farther
    left is more likely to be a more significant figure).
    """
    if position_map[unit] < 0:
        min_dev = max(deviations) * len(positions)
        min_index = -1
        for position in xrange(len(positions)):
            # The "deviations[position] * (position + 1)" test here gives a
            # strong preference for the year to be earlier in the list, as that
            # is the most typical case.
            if (positions[position][unit] and
                deviations[position] * (position + 1) < min_dev):
                min_dev = deviations[position] * (position + 1)
                min_index = position
            print deviations[position], min_index, min_dev
        return min_index
    return position_map[unit]

def cross_confirm_unit(unit, index, positions):
    """ensures that all other columns mark possible"""
    pass

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

def parse_data(data):
    """Parses all data in the chunk, returning, you know, stuff."""
    # Unlikely we'll find 20 significant numbers before our date is complete
    shortest = 20
    
    position_set = {
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
        positions.append(position_set.copy())
        sums.append(0)

    unit_names = [ 'year', 'month', 'day', 'hour', 'minute', 'second' ]

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

    # Deviation based exclusions
    for deviation in xrange(len(deviations)):
        if deviations[deviation] > 30:
            for unit in positions[deviation]:
                positions[deviation][unit] = False

    position_map = { name: -1 for name in unit_names }

    # Cross logic passes
    for i in xrange(len(unit_names)):
        unit_counts = cross_logic_pass(positions, unit_names, position_map)
    import json
    for unit in unit_names:
        new_index = get_minimum_possible_deviation_index(unit,
                                                         position_map,
                                                         deviations,
                                                         positions)
        print unit, new_index, position_map[unit]
        if position_map[unit] != new_index:
            position_map[unit] = new_index
            for position in xrange(len(positions)):
                if position != new_index:
                    positions[position][unit] = False
        unit_counts = cross_logic_pass(positions, unit_names, position_map)

        # Special case minutes/seconds
        if unit == 'hour':
            unit_counts = cross_logic_pass(positions, unit_names, position_map)
            for position in xrange(1, len(positions) - 1):
                if positions[position]['second'] and not (
                    positions[position + 1]['minute'] or
                    positions[position - 1]['minute']):
                    positions[position]['second'] = False
                if positions[position]['minute'] and not (
                    positions[position + 1]['second'] or
                    positions[position - 1]['second']):
                    positions[position]['minute'] = False
            unit_counts = cross_logic_pass(positions, unit_names, position_map)

        # If minutes and seconds are unknown and there are two of each.
        if (position_map['minute'] < 0 and
            position_map['second'] < 0 and
            unit_counts['minute'] == 2 and
            unit_counts['second'] == 2):
            # Subtract 1 here so we can always peek ahead at the next index
            for position in xrange(len(positions) - 1):
                # Check that they're in sequence
                if (positions[position]['minute'] and 
                    positions[position + 1]['second']):
                    positions[position]['second'] = False
                    positions[position + 1]['minute'] = False
                    unit_counts = cross_logic_pass(positions,
                                                   unit_names,
                                                   position_map)
                    break
        print_units(unit_names, positions)
    

    #unit_counts = cross_logic_pass(positions, unit_names, position_map)  
    print position_map

    # Let's try to output this in a meaningful way
    ftemplate = "%10.5f" * shortest

    print ftemplate % tuple(deviations)
    print_units(unit_names, positions)
    return position_map

def print_units(unit_names, positions):
    template = "%10s" * len(positions)
    for unit in unit_names:
        units = []
        for position in positions:
            units.append(unit if position[unit] else '')
        print template % tuple(units)

if __name__ == "__main__":
    options, args = _parse_args()
    for arg in args:
        #try
            with open(arg) as f:
                # Seek to EOF
                f.seek(0, 2)
                if f.tell() >= 4096:
                    f.seek(-4096, 2)
                else:
                    f.seek(0, 0)
                data = f.read(4096)
                
                position_map = parse_data(data)
                regex_len = position_map[max(position_map,
                                             key=position_map.get)] + 1
                regex_parts = [ False for i in xrange(regex_len) ]
                regex_parts[position_map['month']] = (
                    "(?P<month>%s)" % "|".join(["\d+"] + month_map.keys())
                )
                for unit in ['year', 'day', 'hour', 'minute', 'second']:
                    regex_parts[position_map[unit]] = "(?P<%s>\d+)" % unit
                final_regex = ""
                first = True
                for item in regex_parts:
                    if not item:
                        item = "\d+"
                    if 'month' in item:
                        final_regex = "%s%s%s" % (
                            final_regex,
                            ".+?%s" % item.replace('P<month>', '='),
                            item)
                    elif first:
                        first = False
                        final_regex = "%s%s" % (
                                                        final_regex,
                                                        item)
                    else:
                        final_regex = "%s%s%s" % (
                            final_regex,
                            "[^\d]+",
                            item)
                print final_regex
                searcher = re.compile(final_regex)
                for line in data.splitlines()[1:]:
                    print line
                    entries = searcher.search(line)
                    if entries:
                        print entries.groupdict()
        #except Exception, e:
        #    raise e
