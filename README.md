# arxiv_on_deck
[![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/mfouesneau/arxiv_on_deck/master)

This repository is a quick and dirty version of the Arxiver.

The code goes through the new specific author lists and compiles a 1 page summary with figures
A sort of Arxiver for institutes or groups

And example is given in the example directory

## Quick Start

```
Usage: main.py [options]

Options:
  -h, --help            show this help message and exit
  -m HL_AUTHORS, --mitarbeiter=HL_AUTHORS
                        List of authors to highlight (co-workers)
  -i IDENTIFIER, --id=IDENTIFIER
                        Make postage of a single paper given by its arxiv id
  -a HL_AUTHORS, --authors=HL_AUTHORS
                        Highlight specific authors
```

## What is different from the Arxiver?

If you don't know the ArXiver, check it there: http://arxiver.moonhats.com/

The main difference comes from the additional content and output format.

First, this code does not make html pages but pdfs, born during a science coffee
at MPIA.

Here is an overview of the steps the code does:
1. Get the list of new articles on Arxiv.
2. Retrieve the information on each article including title, abstract, subjects.
3. Filter out all but selected authors (e.g., institute or group members)
4. Download the source, hunt for information in the paper source: figures, caption and labels
5. Generates a tex file with internal template with abstract, authors figures
   and captions. (takes care of compiling references from the original document)
6. Compile the document into pdf (figures are converted on the fly if necessary)


The figure selection remains simple in this version. It parses for the Arxiver
tag:
`%@arxiver{fig1.pdf,fig4.png,fig15.eps}`
or selects the most references figures throughout the text.


## Contributors

* Morgan Fouesneau (@mfouesneau)
* Iskren Y. Georviev (@iskren-y-g)
