"""We want to replace all instances of:
alpha, beta, gamma, delta, epsilon, kappa, theta
and their capitalized versions with the corresponding unicode
character, and add en entry to the grounding map for each of these
if they aren't already in there"""

import csv
import os

from indra.resources.greek_alphabet import greek_alphabet

# These are the characters that are spelled out and we want to map
chars_to_map = ['alpha', 'beta', 'gamma', 'delta', 'epsilon', 'kappa', 'theta']
greek_reverse = {v: k for k, v in greek_alphabet.items()}


def main():
    path_this = os.path.dirname(os.path.abspath(__file__))
    gm_file = os.path.join(path_this, os.pardir, 'grounding_map.csv')
    new_rows = []
    existing_strings = []
    with open(gm_file, 'r') as f:
        csvreader = csv.reader(f, delimiter=str(u','), lineterminator='\r\n',
                               quoting=csv.QUOTE_MINIMAL,
                               quotechar=str(u'"'))
        for row in csvreader:
            text_string = row[0]
            existing_strings.append(text_string)
            any_renamed = False
            # If we find greek letters spelled out in an entity text string,
            # we replace them with unicode characters
            for greek_letter_name in chars_to_map:
                if greek_letter_name in text_string:
                    text_string = \
                        text_string.replace(greek_letter_name,
                                            greek_reverse[greek_letter_name])
                    any_renamed = True
                if greek_letter_name.capitalize() in text_string:
                    text_string = \
                        text_string.replace(greek_letter_name.capitalize(),
                                            greek_reverse[greek_letter_name])
                    any_renamed = True
            # These will be the potentially new rows
            if any_renamed:
                new_row = [text_string] + row[1:]
                new_rows.append(new_row)
    # We only add a new row if that wasn't already in the grounding map
    rows_to_add = [r for r in new_rows if r[0] not in existing_strings]
    # Finally, we append the new rows to the file
    with open(gm_file, 'a') as f:
        csvwriter = csv.writer(f, delimiter=str(u','), lineterminator='\r\n',
                               quoting=csv.QUOTE_MINIMAL,
                               quotechar=str(u'"'))
        for row in rows_to_add:
            csvwriter.writerow(row)


if __name__ == '__main__':
    main()
