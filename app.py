"""
A quick and dirty parser for ArXiv
===================================

"""

from __future__ import (absolute_import, division, print_function)
import sys
import operator
import re
from glob import glob
import os
import subprocess

from html.parser import HTMLParser
from urllib.request import urlopen
import tarfile
import shutil

PY3 = sys.version_info[0] > 2

if PY3:
    iteritems = operator.methodcaller('items')
    itervalues = operator.methodcaller('values')
    basestring = (str, bytes)
else:
    range = xrange
    from itertools import izip as zip
    iteritems = operator.methodcaller('iteritems')
    itervalues = operator.methodcaller('itervalues')
    basestring = (str, unicode)


def balanced_braces(args):
    """ Find tokens between {} 

    Parameters
    ----------
    args: list or str
        data to parse

    Returns
    -------
    parts: seq
        extracted parts
    """
    if isinstance(args, basestring):
        return balanced_braces([args])
    parts = []
    for arg in args:
        if '{' not in arg:
            continue
        chars = []
        rest = []
        n = 0
        for c in arg:
            if c == '{':
                if n > 0:
                    chars.append(c)
                n += 1
            elif c == '}':
                n -= 1
                if n > 0:
                    chars.append(c)
                elif n == 0:
                    parts.append(''.join(chars).lstrip().rstrip())
                    chars = []
            elif n > 0:
                chars.append(c)
            else:
                rest.append(c)
    return parts


def get_latex_body(data):
    """ Extract document body text """
    a = re.compile(r'begin{document}').search(data).span()[1]
    b = re.compile(r'end{document}').search(data).span()[0]
    return clear_comments(data[a:b])


def get_latex_header(data):
    """ Extract document header """
    a = re.compile(r'begin{document}').search(data).span()[1]
    return data[:a]


def get_latex_macros(data):
    """ Extract defined commands in the document header """
    header = get_latex_header(data)
    macros = '\n'.join(re.compile(r'command{.*}').findall(header))
    macros = macros.replace('command', '\\providecommand')
    #multiline def will be ignored
    defs = [k for k in re.compile(r'\\def.*').findall(header) if (len(balanced_braces(k)) > 0)] 
    defs = defs + [k for k in re.compile(r'\\gdef.*').findall(header) if (len(balanced_braces(k)) > 0)] 
    macros += '\n'.join(defs)
    print('*** Found macros and definitions in the header: ')

    print(macros)
    return macros


def clear_comments(data):
    lines = []
    for line in data.splitlines():
        try: 
            start = list(re.compile(r'(?<!\\)%').finditer(line))[0].span()[0]
            lines.append(line[:start])
        except IndexError:
            lines.append(line)
    return '\n'.join(lines)


def get_latex_figures(data):
    """ Extract figure declarations """
    starts = [k.span()[0] for k in re.compile(r'(?<!%).*begin{figure').finditer(data)]
    ends = [k.span()[1] for k in re.compile(r'(?<!%).*end{figure.*').finditer(data)]
    figures = [data[a: b] for a, b in zip(starts, ends)]
    return figures


def parse_command(command, code, tokens=1):
    """
    Parse code to find a command arguments

    Parameters
    ----------
    command: str
        command to find

    code: str
        code in which searching

    tokens: int
        number of arguments to find

    Returns
    -------
    next_token: sequence or str
        found arguments
    """
    safe = command.replace('\\', '')
    options = re.findall(safe + '\s*\[.*\]', code)
    if len(options) > 0:
        opt = options[0]
        code = code.replace(opt.replace(command, ''), '')
    where = list(re.compile(r'\\' + safe).finditer(code))[0].span()[1]
    next_token = balanced_braces(code[where:])[:tokens]
    if tokens == 1:
        return next_token[0]
    return next_token


def get_latex_environment(envname, data, onlycontent=True):
    """
    Parse code to find a specific environment content

    Parameters
    ----------
    envname: str
        environment to find

    data: str
        code in which searching

    onlycontent: bool, optional
        return only content otherwise incl. env. definition tags

    Returns
    -------
    content: sequence
        found content
    """
    if not onlycontent:
        starts = [k.span()[0] for k in re.compile(r'begin{' + envname).finditer(data)]
        ends = [k.span()[1] for k in re.compile(r'end{' + envname +'.*').finditer(data)]
        content = [data[a - 1: b] for a, b in zip(starts, ends)]
    else:
        starts = [k.span()[1] for k in re.compile(r'begin{' + envname).finditer(data)]
        ends = [k.span()[0] for k in re.compile(r'end{' + envname +'.*').finditer(data)]
        content = [data[a + 1: b - 1] for a, b in zip(starts, ends)]
    return content


class Figure(object):
    """ 
    class that attempts to catch figures from tex source input in many formats
    """
    def __init__(self, code, number=0):
        self._code = code
        self.info = self._parse()
        self._number = number
        self._n_references = 0

    def set_number_of_references(self, number):
        """ tell how many times the figure is cited in the text """
        self._n_references = number

    @property
    def number_of_references(self):
        """ how many times the figure is cited in the text """
        return self._n_references

    def _parse(self):
        """ Parse the code for specific commands """
        commands = 'caption', 'label', 'includegraphics', 'plotone'
        info= {}
        # makes sure multiple includegraphics on the same line do work
        try:
            # careful with subfigure...
            if 'subfigure' in self._code:
                found = []
                for match in re.compile(r'subfigure.*').finditer(self._code):
                    start, end = match.span()
                    newcode = balanced_braces(self._code[start:end])[0]
                    for command in commands:
                        try:
                            found.append(parse_command(command, newcode))
                        except IndexError:
                            pass
                info['subfigures'] = found

                for command in commands[:2]:
                    try:
                        info[command] = parse_command(command, self._code)
                    except IndexError:
                        info[command] = None
            else:
                for command in commands:
                    try:
                        info[command] = parse_command(command, self._code)
                    except IndexError:
                        info[command] = None
                command = 'plottwo'
                try:
                    info[command] = parse_command(command, self._code, 2)
                except IndexError:
                    info[command] = None
        except:
            # Catch any issue for now 
            for command in commands:
                info[command] = None

        return info

    @property
    def files(self):
        """ Associated data files """
        files = []
        for k in 'includegraphics', 'plotone':
            attr = self.info.get(k)
            if attr is not None:
                files.append(attr)
        for k in 'plottwo', 'subfigures':
            attr = self.info.get(k)
            if attr is not None:
                files.extend(attr)
        return files

    @property
    def label(self):
        return self.info['label']

    @property
    def caption(self):
        return self.info['caption']

    def __repr__(self):
        txt = """Figure {0:d} ({1:s})
        {2:s}
        File(s): {3:s}"""
        return txt.format(self._number, self.label or "",
                self.caption, ','.join(self.files))


class Document(object):
    """ Latex Document structure """

    def __init__(self, data):
        self._code = data
        self._header = get_latex_header(self._code)
        self._body = get_latex_body(self._code)
        self._macros = get_latex_macros(self._header)
        self._title = None
        self._abstract = None
        self._authors = None
        self._short_authors = None
        self._structure = None
        self._identifier = None
        self.figures = [Figure(k, e) for e, k in enumerate(get_latex_figures(self._body), 1)]
        self.highlight_authors = []
        self.comment = None
        self.date = ''

        self._update_figure_references()


    def _update_figure_references(self):
        """ parse to find cited figures in the text """
        for fig in self.figures:
            if fig.label is not None:
                number = len(re.compile(r'\\ref{' + fig.label + '}').findall(self._code))
                fig.set_number_of_references(number)

    @property
    def arxivertag(self):
        """ check for arxiver tag selecting figures """
        if r"%@arxiver" in self._code:
            start, end = list(re.compile(r'@arxiver{.*}').finditer(self._body))[0].span()
            return balanced_braces(self._code[start:end])[0]

    @property
    def title(self):
        if self._title is None:
            self._title = parse_command('title', self._code) 
        return self._title

    @property
    def authors(self):
        if self._authors is None:
            self._authors = parse_command('author', self._code) 
        return self._authors

    @property
    def short_authors(self):
        if self._short_authors is not None:
            return self._short_authors
        if len(self.authors) < 5:
            return self.authors
        else:
            if any(name in self._authors[0] for name in set(self.highlight_authors)):
                authors = r'\hl{' + self._authors[0] + r'}, et al.'
            else:
                authors = self._authors[0] + ", et al."
        if len(self.highlight_authors) > 0:
            incl_authors = []
            for name in set(self.highlight_authors):
                if name != self._authors[0]:
                    incl_authors.append(r'\hl{' + name + r'}')
            authors += '; incl. ' + ', '.join(incl_authors)
        self._short_authors = authors
        return authors

    @property
    def abstract(self):
        if self._abstract is None:
            try:
                try:
                    # AA abstract
                    self._abstract = '\n'.join(parse_command('abstract', self._body, 5))
                except Exception as error:
                    self._abstract = parse_command('abstract', self._code)
            except IndexError:
                self._abstract = ' '.join(get_latex_environment('abstract', self._code))
        # Cleaning
        self._abstract = '\n'.join([k for k in self._abstract.splitlines() if k != ''])
        return self._abstract

    def _parse_structure(self):
        if self._structure is not None:
            return self._structure

        tags = list(re.compile(r'\\([^\s]*)section').finditer(self._body))
        try:
            appendix_start = list(re.compile(r'\\([^\s]*)appendix').finditer(self._body))[0].span()[1]
        except IndexError:
            appendix_start = len(self._code)
        structure = []
        levels = {r'\section': 0, '\subsection': 1, '\subsubsection': 2}
        for tag in tags:
            starts = tag.span()[0]
            name = parse_command(tag.group(), self._code[starts:])
            level = levels[tag.group()] + int(starts >= appendix_start)
            attr = (level, name, [])

            if len(structure) == 0:
                structure.append(attr)
            else:
                if ((starts >= appendix_start) & (structure[-1][1] != 'Appendix')):
                    structure.append((0, 'Appendix', []))
                if level > structure[-1][0]:
                    last = structure[-1][-1]
                    if len(last) > 0:
                        if level > last[-1][0]:
                            last[-1][-1].append(attr)
                        else:
                            structure[-1][-1].append(attr)
                    else:
                        structure[-1][-1].append(attr)
                else:
                    structure.append(attr)
        self._structure = structure
        return self._structure

    def print_structure(self):
        for node in self._parse_structure():
            name = node[1]
            children = node[-1]
            print(name)
            for subnode in children:
                name = subnode[1]
                print('  ' * subnode[0], name)
                for subsubnode in subnode[-1]:
                    print('  ' * subsubnode[0], subsubnode[1])

    def __repr__(self):
        txt = """{s.title:s}\n\t{s.short_authors:s}"""
        if self._identifier:
            txt = """[{s._identifier:s}]: """ + txt
        return txt.format(s=self)


class ExportPDFLatexTemplate(object):

    template = r"""%
\documentclass[a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[a4paper,margin=.5cm,landscape]{geometry}
\usepackage[english]{babel}
\usepackage{natbib}
\usepackage{graphicx}
\usepackage{txfonts}
\usepackage{xcolor}
\usepackage{amsfonts}
\usepackage{mathrsfs}
\usepackage{amssymb}
\usepackage{textgreek}
\usepackage[nolist,nohyperlinks,printonlyused]{acronym}
\usepackage[breaklinks,colorlinks,citecolor=blue,unicode]{hyperref}
\usepackage{siunitx}

%convert files on the fly to pdflatex compilation
\DeclareGraphicsExtensions{.jpg, .ps, .eps, .png, .pdf}
\DeclareGraphicsRule{.ps}{pdf}{.pdf}{`convert #1 pdf:`dirname #1`/`basename #1 .ps`-ps-converted-to.pdf}
\DeclareGraphicsRule{.eps}{pdf}{.pdf}{`convert #1 pdf:`dirname #1`/`basename #1 .eps`-eps-converted-to.pdf}

%Document found macros
<MACROS>

% template macros
\renewcommand{\abstract}[1]{%
  \textbf{<IDENTIFIER> } #1
}
\newcommand\hl[1]{\colorbox{yellow}{#1}}

\renewcommand{\thanks}[1]{}
\renewcommand{\caption}[1]{{\scriptsize{#1}}}
\providecommand{\acronymused}[1]{}
\providecommand{\altaffilmark}[1]{}

\begin{document}
\thispagestyle{plain}
\begin{minipage}[t][0pt]{0.98\linewidth}

\textbf{\LARGE{<TITLE>}}

\vspace{1em}

\textbf{\large{<AUTHORS>}}

\vspace{1em}

\abstract{
<ABSTRACT>
}

\vspace{1em}

\centering
<FIGURES>

\vfill
\hl{<DATE>} -- <COMMENTS>
\end{minipage}

\end{document}
"""

    compiler = r"TEXINPUTS='../deprecated_tex:' pdflatex"
    compiler_options = r"-enable-write18 -shell-escape -interaction=nonstopmode"

    def short_authors(self, document):
        return document.short_authors

    def select_figures(self, document, N=3):
        selection = sorted(document.figures, 
                key=lambda x: x.number_of_references, 
                reverse=True)
        return selection[:N]

    def figure_to_latex(self, figure, size=r'0.32\textwidth'):
        txt = r"""\begin{minipage}{0.32\textwidth}""" + '\n'
        for fname in figure.files:
            txt += r"    \includegraphics[width=\textwidth, height=0.4\textheight,keepaspectratio]{"
            txt += fname + r"}\\" + "\n"
        txt += r"""    \caption{Fig. """ + str(figure._number) + """: """ + figure.caption + r"""}"""
        txt += '\n' + """\end{minipage}""" + '\n%\n'
        return txt
        '''
        txt = r"""\resizebox{{{0:s}}}{!}{""".format(size) + '\n'
        for fname in figure.files:
            txt += r"\includegraphics[width=\textwidth, height=0.4\textheight,keepaspectratio]{"
            txt += fname + r"}\\" + "\n"
        txt += r"""    \caption{Fig. """ + str(figure._number) + """: """ + figure.caption + r"""}"""
        txt += '\n' + """}""" + '\n%\n'
        return txt
        '''

    def apply_to_document(self, document):

        txt = self.template.replace('<MACROS>', "") # document._macros) 
        if document._identifier is not None:
            txt = txt.replace('<IDENTIFIER>',
                    r'\hl{{{0:s}}}'.format(document._identifier) or 'Abstract ')
        else:
            txt = txt.replace('<IDENTIFIER>', 'Abstract ')
        txt = txt.replace('<TITLE>', document.title)
        txt = txt.replace('<AUTHORS>', self.short_authors(document))
        txt = txt.replace('<ABSTRACT>', document.abstract.replace(r'\n', ' '))
        figures = ''.join([self.figure_to_latex(fig) for fig in
            self.select_figures(document) ])
        txt = txt.replace('<FIGURES>', figures)
        txt = txt.replace('<COMMENTS>', document.comment or '')
        txt = txt.replace('<DATE>', document.date)

        return txt


class DocumentSource(Document):

    def __init__(self, directory):
        fnames = glob(directory + '/*.tex')
        fname = self._auto_select_main_doc(fnames)

        with open(fname, 'r') as finput:
            data = self._expand_auxilary_files(finput.read(),
                    directory=directory)

        Document.__init__(self, data)
        self.fname = fname
        self.directory = directory
        self.outputname = self.fname[:-len('.tex')] + '_cleaned.tex' 

    def _expand_auxilary_files(self, data, directory=''):
        # inputs
        inputs = list(re.compile(r'\\input.*').finditer(data))
        if len(directory):
            if directory[-1] != '/':
                directory = directory + '/'
        if len(inputs) > 0:
            print('*** Found document inclusions ')
            new_data = []
            prev_start, prev_end = 0, 0
            for match in inputs:
                try:
                    fname = match.group().replace(r'\input', '').strip()
                    fname = fname.replace('{', '').replace('}', '').replace('.tex', '')   # just in case
                    print('      input command: ', fname)
                    with open(directory + fname + '.tex', 'r') as fauxilary:
                        auxilary = fauxilary.read()
                    start, end = match.span()
                    new_data.append(data[prev_end:start])
                    new_data.append('\n%input from {0:s}\n'.format(fname) + auxilary + '\n')
                    prev_start, prev_end = start, end
                except Exception as e:
                    print(e)
                    pass
            new_data.append(data[prev_end:])
            return '\n'.join(new_data)
        else:
            return data

    def _auto_select_main_doc(self, fnames):
        if (len(fnames) == 1):
            return fnames[0]

        print('multiple tex files')
        selected = None
        for e, fname in enumerate(fnames):
            with open(fname, 'r') as finput:
                if 'documentclass' in finput.read():
                    selected = e, fname
                    break
        if selected is not None:
            print("Found main document in: ", selected[1])
            print(e, fname)
        if selected is not None:
            return selected[1]
        else:
            print('Could not locate the main document automatically. Little help please!')
            for e, fname in enumerate(fnames):
                print(e, fname)
            select = input("which file is the main document? ")
            return fnames[int(select)]

    def __repr__(self):
        return '''Paper in {0:s}, \n\t{1:s}'''.format(self.fname,
                Document.__repr__(self))

    def compile(self, template=None):

        if template is None:
            template = ExportPDFLatexTemplate()

        with open(self.outputname, 'w') as out:
            out.write(template.apply_to_document(self))

        # compile source to get aux data if necessary
        compiler_command = "cd {0:s}; {1:s} {2:s} ".format(self.directory,
                template.compiler, template.compiler_options)
        if not os.path.isfile(self.fname.replace('.tex', '.aux')):
            outputname = self.fname.split('/')[-1]
            subprocess.call(compiler_command + outputname, shell=True)
        
        # get the references compiled
        input_aux = self.fname.replace('.tex', '.aux')
        output_aux = self.outputname.replace('.tex', '.aux')
        with open(output_aux, 'w+') as fout:
            with open(input_aux, 'r') as fin:
                for line in fin:
                    if (('cite' in line) or ('citation' in line) or 
                            ('label' in line) or ('toc' in line)):
                        fout.write(line)

        # compile output
        outputname = self.outputname.split('/')[-1]
        subprocess.call(compiler_command + outputname, shell=True)


class ArxivAbstractHTMLParser(HTMLParser):
    """ generates a list of Paper items by parsing the Arxiv new page """

    def __init__(self, *args, **kwargs):
        HTMLParser.__init__(self, *args, **kwargs)
        self.current_paper = None
        self._paper_item = False
        self._title_tag = False
        self._author_tag = False
        self._abstract_tag = False
        self._comment_tag = False
        self.title = None
        self.comment = None
        self.date = None
        self.authors = []

    def handle_starttag(self, tag, attrs):
        if tag == 'h1':
            self._title_tag = True
        if (tag == 'a') & (len(attrs) > 0):
            if '/find/astro-ph/1/au:' in attrs[0][1]:
                self._author_tag = True
        if tag == 'blockquote':
            self._abstract_tag = True

        try:
            if 'tablecell comments' in attrs[0][1]:
                self._comment_tag = True
        except IndexError:
            pass

    def handle_endtag(self, tag):
        if tag == 'h1':
            self._title_tag = False
        if tag == 'a':
            self._author_tag = False
        if tag == 'blockquote':
            self._abstract_tag = False

    def handle_data(self, data):
        if self._title_tag and ('Title:' not in data):
            self.title = data.replace('\n', ' ').strip()
        if self._author_tag:
            self.authors.append(data)
        if self._abstract_tag:
            self.abstract = data.strip()
        if self._comment_tag:
            self.comment = data.strip()
            self._comment_tag = False
        if 'Submitted on' in data:
            self.date = data.strip()


class ArxivListHTMLParser(HTMLParser):
    """ generates a list of Paper items by parsing the Arxiv new page """

    def __init__(self, *args, **kwargs):
        skip_replacements = kwargs.pop('skip_replacements', False)
        HTMLParser.__init__(self, *args, **kwargs)
        self.papers = []
        self.current_paper = None
        self._paper_item = False
        self._title_tag = False
        self._author_tag = False
        self.skip_replacements = skip_replacements
        self._skip = False

    def handle_starttag(self, tag, attrs):
        # paper starts with a dt tag
        if (tag in ('dt') and not self._skip):
            if self.current_paper:
                self.papers.append(self.current_paper)
            self._paper_item = True
            self.current_paper = ArXivPaper()

    def handle_endtag(self, tag):
        # paper ends with a /dd tag
        if tag in ('dd'):
            self._paper_item = False
        if tag in ('div',) and self._author_tag:
            self._author_tag = False
        if tag in ('div',) and self._title_tag:
            self._title_tag = False

    def handle_data(self, data):
        if data.strip() in (None, "", ','):
            return
        if 'replacements for' in data.lower():
            self._skip = (True & self.skip_replacements)
        if self._paper_item:
            if 'arXiv:' in data:
                self.current_paper.identifier = data
            if self._title_tag:
                self.current_paper.title = data.replace('\n', '')
                self._title_tag = False
            if self._author_tag:
                self.current_paper._authors.append(data.replace('\n', ''))
                self._title_tag = False
            if 'Title:' in data:
                self._title_tag = True
            if 'Authors:' in data:
                self._author_tag = True


class ArXivPaper(object):
    """ Class that handles the interface to Arxiv website paper abstract """

    source = "https://arxiv.org/e-print/{identifier}"
    abstract = "https://arxiv.org/abs/{identifier}"

    def __init__(self, identifier=""):
        """ Initialize the data """
        self.identifier = identifier
        self.title = ""
        self._authors = []
        self.highlight_authors = []
        self.comment = ""
        self.date = None

    @classmethod
    def from_identifier(cls, identifier):
        return cls(identifier.split(':')[-1]).get_abstract()

    @property
    def authors(self):
        authors = ", ".join(self._authors)
        if len(self.highlight_authors) > 0:
            for name in self.highlight_authors:
                if (name in authors):
                    authors = authors.replace(name, r'\hl{' + name + r'}')
        return authors

    @property
    def short_authors(self):
        if len(self.authors) < 5:
            return self.authors
        else:
            if any(name in self._authors[0] for name in self.highlight_authors):
                authors = r'\hl{' + self._authors[0] + r'}, et al.'
            else:
                authors = self._authors[0] + ", et al."
        if len(self.highlight_authors) > 0:
            incl_authors = []
            for name in self.highlight_authors:
                if name != self._authors[0]:
                    incl_authors.append(r'\hl{' + name + r'}')
            authors += '; incl. ' + ','.join(incl_authors)
        return authors

    def __repr__(self):
        txt = """[{s.identifier:s}]: {s.title:s}\n\t{s.authors:s}"""
        return txt.format(s=self)

    def retrieve_document_source(self, directory=None):
        where = ArXivPaper.source.format(identifier=self.identifier.split(':')[-1])
        tar = tarfile.open(mode='r|gz', fileobj=urlopen(where))
        if directory is None:
            return tar
        else:
            if os.path.isdir(directory):
                shutil.rmtree(directory)
            print("extracting tarball...")
            tar.extractall(directory)
            document = DocumentSource(directory)
            self.get_abstract()
            try:
                document.authors
            except Exception as error:
                print(error)
                document._authors = self.authors
            try:
                document.abstract
            except Exception as error:
                print(error)
                document._abstract = self.abstract
            document._short_authors = self.short_authors
            document._authors = self.authors
            document._identifier = self.identifier
            document.comment = self.comment
            document.date = self.date
            return document

    def get_abstract(self):
        where = ArXivPaper.abstract.format(identifier=self.identifier.split(':')[-1])
        html = urlopen(where).read().decode('utf-8')

        parser = ArxivAbstractHTMLParser()
        parser.feed(html)
        self.title = parser.title
        self._authors = parser.authors
        self.abstract = parser.abstract
        self.comment = parser.comment
        self.date = parser.date
        return self

    def make_postage(self, template=None, mitarbeiter=None):
        print("Generating postage")
        self.get_abstract()
        s = self.retrieve_document_source('./tmp')
        s.compile(template=template)
        identifier = self.identifier.split(':')[-1]
        name = s.outputname.replace('.tex', '.pdf').split('/')[-1]
        shutil.move('./tmp/' + name, identifier + '.pdf')
        print("PDF postage:", identifier + '.pdf' )


def get_new_papers(skip_replacements=False):
    """ retrieve the new list from the website 
    Parameters
    ----------
    skip_replacements: bool
        set to skip parsing the replacements

    Returns
    -------
    papers: list(ArXivPaper)
        list of ArXivPaper objects
    """
    url = "https://arxiv.org/list/astro-ph/new"
    html = urlopen(url).read().decode('utf-8')

    parser = ArxivListHTMLParser(skip_replacements=skip_replacements)
    parser.feed(html)
    papers = parser.papers
    return papers


def get_mitarbeiter(source='./mitarbeiter.txt'):
    """ returns the list of authors of interests.
    Needed to parse the input list to get initials and last name.
    This may not work all the time. The best would be to have the proper names
    directly given as e.g. "I.-M. Groot".

    Returns
    -------
    mitarbeiter: list(str)
       authors to look for 
    """
    with open(source) as fin:
        mitarbeiter = []
        for name in fin:
            if name[0] != '#':   # Comment line
                names = name.split()
                shortname = []
                for name in names[:-1]:
                    if '-' in name:
                        rest = '-'.join([w[0] + '.' for w in name.split('-')])
                    else:
                        rest = name[0] + '.'
                    shortname.append(rest)
                shortname.append(names[-1])
                mitarbeiter.append(' '.join(shortname))
    return list(sorted(set(mitarbeiter)))


def highlight_papers(papers, fname_list):
    """ Extract papers when an author match is found
    Parameters
    ----------
    papers: list(ArXivPaper)
        paper list
    fname_list: list(str)
        authors to search

    Returns
    -------
    keep: list(ArXivPaper)
        papers with matching author
    """
    keep = []
    for paper in papers:
        print(paper)
        for name in fname_list:
            for author in paper._authors:
                print(author)
                if name in author:
                    print(name, author)
                    # perfect match on family name
                    # TODO: add initials test
                    if (name == author.split()[-1]):
                        print(name, author)
                        paper.highlight_authors.append(author)
        keep.append(paper)
    return keep


def filter_papers(papers, fname_list):
    """ Extract papers when an author match is found
    Parameters
    ----------
    papers: list(ArXivPaper)
        paper list
    fname_list: list(str)
        authors to search

    Returns
    -------
    keep: list(ArXivPaper)
        papers with matching author
    """
    keep = []
    for paper in papers:
        if any(name in paper.authors for name in fname_list):
            for name in fname_list:
                for author in paper._authors:
                    if name in author:
                        # perfect match on family name
                        # TODO: add initials test
                        if (name == author.split()[-1]):
                            print(name, author)
                            paper.highlight_authors.append(author)
            keep.append(paper)
    return keep


def running_options():

    opts = (
            ('-m', '--mitarbeiter', dict(dest="hl_authors", help="List of authors to highlight (co-workers)", default='./mitarbeiter.txt', type='str')),
            ('-i', '--id', dict(dest="identifier", help="Make postage of a single paper given by its arxiv id", default='None', type='str')),
        )

    from optparse import OptionParser
    parser = OptionParser()

    for ko in opts:
        parser.add_option(*ko[:-1], **ko[-1])

    (options, args) = parser.parse_args()

    return options.__dict__


def main(template=None):
    options = running_options()
    identifier = options.get('identifier', None)

    mitarbeiter_list = options.get('mitarbeiter', './mitarbeiter.txt')
    mitarbeiter = get_mitarbeiter(mitarbeiter_list)
    if identifier in (None, '', 'None'):
        papers = get_new_papers(skip_replacements=True)
        keep = filter_papers(papers, mitarbeiter)
    else:
        papers = [ArXivPaper(identifier=identifier.split(':')[-1])]
        keep = highlight_papers(papers, mitarbeiter)
        
    for paper in keep:
        print(paper)
        try:
            paper.make_postage(template=template, mitarbeiter=mitarbeiter)
        except Exception as error:
            print(error)


if __name__ == "__main__":
    main()
