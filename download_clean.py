# Author: Karl Stratos (stratos@cs.columbia.edu)
"""
This module is used to clean English Common Crawl. You need to specify the path
to the Stanford tokenizer: "third_party/stanford-corenlp-full-2014-08-27/".

Use it like: python3 clean_en.py [wet.paths] [downloaded] > [log.txt]
"""

import argparse
import os
import subprocess

def clean1(input, max_token_length, min_sequence_length, output):
    """
    Preliminary cleaning before passing to the Stanford tokenizer.
    1. Removes meta-data.
    2. Removes any non-ascii character.
    3. Replaces long tokens with a special symbol.
    """
    LONG = "<LONGER_THAN_"+str(max_token_length)+">"  # Symbol for long tokens.
    with open(input, "r") as infile:
        with open(output, "w") as outfile:
            for line in infile:
                line = line[:-1]  # Get rid of the newline character.
                if not line: continue  # Empty.
                token_sequence = []

                # Remove meta-data lines.
                if ((len(line) >= 4 and line[:4] == "WARC") or
                    (len(line) >= 13 and line[:13] == "Content-Type:") or
                    (len(line) >= 15 and line[:15] == "Content-Length:")):
                    continue

                # Go through each character.
                token = ""
                for char in line:
                    if ord(char) >= 128: continue  # Skip non-ascii characters.

                    if (char.isspace()):
                        if (token != ""):  # Found a token.
                            if len(token) > max_token_length:
                                # Replace long tokens with a special symbol.
                                print("Length {0}: {1}".format(len(token),
                                                               token))
                                token = LONG
                            token_sequence.append(token)
                            token = ""
                        else:  # Meaningless empty space.
                            continue
                    else:
                        token += char  # Accumulating a token.

                if (token != ""):  # Final token.
                    if len(token) > max_token_length:
                        # Replace long tokens with a special symbol.
                        print("Length {0}: {1}".format(len(token), token))
                        token = LONG
                    token_sequence.append(token)

                if len(token_sequence) >= min_sequence_length:
                    for i in range(len(token_sequence)):
                        outfile.write(token_sequence[i] + " ")
                    outfile.write("\n")
                else:
                    print("Too short: ", token_sequence)

def purify(input, purity, output):
    """
    Discards sentences where the portion of alphabetic characters among
    non-white characters falls below (<) the purity threshold.
    """
    with open(input, "r") as infile:
        with open(output, "w") as outfile:
            for line in infile:
                num_nonwhite_char = 0
                num_alpha = 0
                for char in line:
                    if char.isspace(): continue  # Ignore white characters.
                    num_nonwhite_char += 1
                    if char.isalpha():
                        num_alpha += 1
                if float(num_alpha) / num_nonwhite_char < purity:  # Unpure!
                    print(line[:-1])
                    continue
                outfile.write(line)

def main(args):
    tokenizer_path = "third_party/stanford-corenlp-full-2014-08-27"
    assert(os.path.isdir(tokenizer_path))

    # Create the output directory if it doesn't already exist.
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    # Get the URLs from the file.
    urls = [line.split()[0] for line in open(args.urls, "r")]

    # For each URL, download the file and clean.
    for url in urls:
        gzname = url.rsplit("/", 1)[1]
        name = gzname.rsplit(".", 1)[0]

        # Skip if the final version of this file already exists.
        final_path = os.path.join(args.outdir, name + ".processed")
        if os.path.exists(final_path): continue
        subprocess.call(["touch", final_path])  # To avoid a race.
        subprocess.call(["wget", url])
        subprocess.call(["gunzip", name])

        # Do initial cleaning.
        name1 = name + ".1"
        clean1(name, args.max_token_length, args.min_sequence_length, name1)

        # Run Stanford document tokenizer.
        name2 = name + ".2"
        command2 = "java -cp '{0}/*' edu.stanford.nlp.process.DocumentPreprocessor {1} > {2}".format(tokenizer_path, name1, name2)
        subprocess.call(command2, shell=True)

        # Sort and remove duplicate sentences.
        name3 = name + ".3"
        sort_delete_command = "cat {0} | sort | uniq > {1}".format(name2, name3)
        subprocess.call(sort_delete_command, shell=True)

        # Finally, only keep sentences whose non-white characters are mostly
        # alphabetic.
        purify(name3, args.purity, final_path)

        subprocess.call(["rm", "-rf", name])
        subprocess.call(["rm", "-rf", name1])
        subprocess.call(["rm", "-rf", name2])
        subprocess.call(["rm", "-rf", name3])

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("urls", type=str, help="file of URLs")
    argparser.add_argument("outdir", type=str, help="output directory")
    argparser.add_argument("--max_token_length", type=int, default=40,
                           help="replace tokens longer than this with a special"
                           "symbol (default: %(default)d)")
    argparser.add_argument("--min_sequence_length", type=int, default=1,
                           help="sequences need to be at least this long "
                           "(default: %(default)d)")
    argparser.add_argument("--purity", type=float, default=0.5, help="a line "
                           "needs to have >= this portion alphabetic (excluding"
                           " white spaces) (default: %(default)f)")
    parsed_args = argparser.parse_args()
    main(parsed_args)
