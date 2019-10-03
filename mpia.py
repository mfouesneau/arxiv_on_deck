#!/Users/georgiev/Installs/miniconda3/bin/python
"""
A quick and dirty parser for ArXiv
===================================

"""
import sys,time
import traceback
from app import (ExportPDFLatexTemplate, DocumentSource, raise_or_warn,\
        color_print, __DEBUG__)
import os
import inspect
#directories
__ROOT__ = '/'.join(os.path.abspath(inspect.getfile(inspect.currentframe())).split('/')[:-1])

# Cron jobs need absolute file paths

mpia_tpl = __ROOT__ + '/mpia.tpl'

class MPIATemplate(ExportPDFLatexTemplate):
    """ Template used at MPIA 
    which shows 3 figures and adapt the layout depending of figure aspect ratios
    """

    template = open(mpia_tpl, 'r').read()

    # Include often missing libraries
    compiler = r"TEXINPUTS='{0:s}/deprecated_tex:' pdflatex ".format(__ROOT__)
    compiler_options = r" -enable-write18 -shell-escape -interaction=nonstopmode "

    def short_authors(self, document):
        """ How to return short version of author list 

        Parameters
        ----------
        document: app.Document instance
            latex document

        returns
        -------
        short_authors: string
            representation of the authors
        """
        print(document.short_authors)
        return document.short_authors

    def figure_to_latex(self, figure):
        """ How to include the figures """
        fig = ""
        for fname in figure.files:
            # as latex parses these lines first, one must prevent latex to find
            # dots in figure filenames apart from the extension 
            rootname, extension = '.'.join(fname.split('.')[:-1]), fname.split('.')[-1]
            fig += r"    \includegraphics[width=\maxwidth, height=\maxheight,keepaspectratio]{"
            fig += r"{" + rootname + r"}." + extension + r"}\\" + "\n"
        if len(figure.files) > 1:
            fig = fig.replace(r'\maxwidth', '{0:0.1f}'.format(0.9 * 1. / len(figure.files)) + r'\maxwidth')
        caption = r"""    \caption{Fig. """ + str(figure._number) + """: """ + str(figure.caption) + r"""}"""
        return fig, caption

    def apply_to_document(self, document):
        """ Fill the template 

        Parameters
        ----------
        document: app.Document instance
            latex document

        Returns
        -------
        txt: string
            latex source of the final document
        """
        txt = self.template.replace('<MACROS>', document._macros)
        if document._identifier is not None:
            txt = txt.replace('<IDENTIFIER>',
                              r'\hl{{{0:s}}}'.format(document._identifier) or 'Abstract ')
        else:
            txt = txt.replace('<IDENTIFIER>', 'Abstract ')
        txt = txt.replace('<TITLE>', document.title)
        txt = txt.replace('<AUTHORS>', self.short_authors(document))
        txt = txt.replace('<ABSTRACT>', document.abstract.replace(r'\n', ' '))

        for where, figure in zip('ONE TWO THREE'.split(),
                                 self.select_figures(document, N=3)):
            fig, caption = self.figure_to_latex(figure)
            if where == 'ONE':
                special = fig.replace(r"[width=\maxwidth, height=\maxheight,keepaspectratio]", "")
                txt = txt.replace('<FILE_FIGURE_ONE>', special)
            fig = fig.replace(r'\\', '')
            txt = txt.replace('<FIGURE_{0:s}>'.format(where), fig)
            txt = txt.replace('<CAPTION_{0:s}>'.format(where), caption)
        if '<CAPTION_TWO>' in txt:
            txt = txt.replace('<FIGURE_TWO>', '')
            txt = txt.replace('<CAPTION_TWO>', '')
        if '<CAPTION_THREE>' in txt:
            txt = txt.replace('<FIGURE_THREE>', '')
            txt = txt.replace('<CAPTION_THREE>', '')

        txt = txt.replace('<COMMENTS>', document.comment or '')
        txt = txt.replace('<DATE>', document.date)

        return txt


def main(template=None):
    """ Main function """
    from app import (get_mitarbeiter, filter_papers, ArXivPaper,
                     highlight_papers, running_options, get_new_papers,
                     shutil, get_catchup_papers, check_required_words, check_date,
                     make_qrcode)
    options = running_options()
    identifier = options.get('identifier', None)
    paper_request_test = (identifier not in (None, 'None', '', 'none'))
    hl_authors = options.get('hl_authors', None)
    hl_request_test = (hl_authors not in (None, 'None', '', 'none'))
    sourcedir = options.get('sourcedir', None)
    catchup_since = options.get('since', None)
    select_main = options.get('select_main', False)

    __DEBUG__ = options.get('debug', False)

    if __DEBUG__:
        print('Debug mode on')

    if not hl_request_test:
        mitarbeiter_list = options.get('mitarbeiter', __ROOT__ + '/mitarbeiter.txt')
        mitarbeiter = get_mitarbeiter(mitarbeiter_list)
    else:
        mitarbeiter = [author.strip() for author in hl_authors.split(',')]

    if sourcedir not in (None, ''):
        paper = DocumentSource(sourcedir, autoselect=(not select_main))
        paper.identifier = sourcedir
        keep, matched_authors = highlight_papers([paper], mitarbeiter)
        paper.compile(template=template)
        name = paper.outputname.replace('.tex', '.pdf').split('/')[-1]
        shutil.move(sourcedir + '/' + name, paper.identifier + '.pdf')
        print("PDF postage:", paper.identifier + '.pdf' )
        return 
    elif identifier in (None, '', 'None'):
        if catchup_since not in (None, '', 'None', 'today'):
            papers = get_catchup_papers(skip_replacements=True)
        else:
            papers = get_new_papers(skip_replacements=True, appearedon=check_date(options.get('date')))
        keep, matched_authors = filter_papers(papers, mitarbeiter)
    else:
        papers = [ArXivPaper(identifier=identifier.split(':')[-1], appearedon=check_date(options.get('date')))]
        keep, matched_authors = highlight_papers(papers, mitarbeiter)

    institute_words = ['Heidelberg', 'Max', 'Planck', '69117']

    # make sure no duplicated papers
    keep = {k.identifier: k for k in keep}.values()
    
    issues = []
    non_issues = []
        
    for paper in keep:
        print(paper)
        try:
            paper.get_abstract()
            s = paper.retrieve_document_source(__ROOT__ + '/tmp/')
            institute_test = check_required_words(s, institute_words)
            color_print("\n**** From Heidelberg: " + str(institute_test) + '\n', 'GREEN')
            _identifier = paper.identifier.split(':')[-1]
            # Filtering out bad matches
            if (not institute_test) and (not paper_request_test):
                raise RuntimeError('Not an institute paper -- ' +
                        check_required_words(s, institute_words, verbose=True))
            if (paper_request_test or institute_test):
                # Generate a QR Code
                make_qrcode(_identifier)
                s.compile(template=template)
                name = s.outputname.replace('.tex', '.pdf').split('/')[-1]
                destination = __ROOT__ + '/' + _identifier + '.pdf'
                time.sleep(2)
                shutil.move(__ROOT__ + '/tmp/' + name, destination)
                print("PDF postage:", _identifier + '.pdf' )
            else:
                print("Not from HD... Skip.")
            non_issues.append((paper.identifier, ', '.join(paper.highlight_authors)))
        except Exception as error:
            issues.append((paper.identifier, ', '.join(paper.highlight_authors), str(error)))
            raise_or_warn(error, debug=__DEBUG__)

    print(""" Issues =============================== """)
    for issue in issues:
        color_print("[{0:s}] {1:s} \n {2:s}".format(*issue), 'red')

    print(""" Matched Authors ====================== """)
    for name, author, pid in matched_authors:
        color_print("[{0:s}] {1:10s} {2:s}".format(pid, name, author), 'green')

    print(""" Compiled outputs ===================== """)
    for issue in non_issues:
        color_print("[{0:s}] {1:s}".format(*issue), 'cyan')


if __name__ == "__main__":
    main(template=MPIATemplate())
