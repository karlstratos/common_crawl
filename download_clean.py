# Author: Karl Stratos (stratos@cs.columbia.edu)
"""
This module is used to clean English Common Crawl. You need to specify the path
to the Stanford tokenizer: "third_party/stanford-corenlp-full-2014-08-27/".

Use it like: python3 clean_en.py [wet.paths] [downloaded] > [log.txt]
"""

import argparse
import os
import subprocess

def clean1(input, output):
    """
    Preliminary cleaning before passing to the Stanford tokenizer.
    1. Removes meta-data.
    2. Removes any non-ascii character.
    """
    with open(input, "r") as infile:
        with open(output, "w") as outfile:
            for line in infile:
                line = line[:-1]  # Get rid of the newline character.
                if not line: continue  # Empty.

                # Remove meta-data lines like the following:
                # WARC/1.0
                # WARC-Type: conversion
                # WARC-Target-URI: http://news.bbc.co.uk/2/hi/africa/3414345.stm
                # WARC-Date: 2014-08-02T09:52:13Z
                # WARC-Record-ID:
                # WARC-Refers-To:
                # WARC-Block-Digest: sha1:JROHLCS5SKMBR6XY46WXREW7RXM64EJC
                # Content-Type: text/plain
                # Content-Length: 6724

                #if (len(line) >= 4 and line[:4] == "WARC") or
                #    (len(line) >= 13 and line[:13] == "Content-Type:") or
                #     (len(line) >= 13 and line[:13] == "Content-Length:"):
                #    print(line)
                #    continue

                # Go through each character of the line to remove non-ascii.
                i = 0
                while i < len(line):
                    if ord(line[i]) >= 128:  # Skip a non-ascii character.
                        i += 1
                        continue
                    outfile.write(line[i])
                    i += 1
                outfile.write("\n")

def main(args):
    urls = [line.split()[0] for line in open(args.urls, "r")]
    for url in urls:
        gzname = url.rsplit("/", 1)[1]
        name = gzname.rsplit(".", 1)[0]
        prpath = os.path.join(args.outdir, name + ".processed")
        if os.path.exists(prpath):
            print("Skipping: ", prpath)
            continue
        subprocess.call(["touch", prpath])  # First create this file to avoid a race.
        subprocess.call(["wget", url])
        subprocess.call(["gunzip", name])

        # Only collect ascii lines of length at least 3.
        name1 = name + ".1"
        clean1(name, name1)
        exit(0)

        # Run Stanford document tokenizer.
        name2 = name + ".2"
        command2 = "java -cp 'stanford-corenlp-full-2014-08-27/*' edu.stanford.nlp.process.DocumentPreprocessor {0} > {1}".format(name1, name2)
        subprocess.call(command2, shell=True)

        # Now that sentences are separated, discard unreasonably long sentences.
        name3 = name + ".3"
        command3 = "cat {0} | awk 'NF < 150' > {1}".format(name2, name3)
        subprocess.call(command3, shell=True)

        # Sort and delete duplicate sentences.
        name4 = name + ".4"
        command4 = "cat {0} | sort | uniq > {1}".format(name3, name4)
        subprocess.call(command4, shell=True)

        # Remove sentences that are mostly symbols.
        with open(prpath, "w") as outfile:
            with open(name4, "r") as infile:
                for line in infile:
                    num_symbols = 0
                    for char in line:
                        if not char.isalnum(): num_symbols += 1
                    if float(num_symbols) / len(line) < 0.4:
                        outfile.write(line)

        subprocess.call(["rm", "-rf", name])
        subprocess.call(["rm", "-rf", name1])
        subprocess.call(["rm", "-rf", name2])
        subprocess.call(["rm", "-rf", name3])
        subprocess.call(["rm", "-rf", name4])

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("urls", type=str, help="file of URLs")
    argparser.add_argument("outdir", type=str, help="output directory")
    parsed_args = argparser.parse_args()
    main(parsed_args)
