"""
A quick and dirty parser for ArXiv
===================================

"""
import sys
import traceback
from app import (ExportPDFLatexTemplate, DocumentSource, raise_or_warn, __DEBUG__)
import os
import inspect
#directories
__ROOT__ = '/'.join(os.path.abspath(inspect.getfile(inspect.currentframe())).split('/')[:-1])


class MPIATemplate(ExportPDFLatexTemplate):
    """ Template used at MPIA 
    which shows 3 figures and adapt the layout depending of figure aspect ratios
    """

    template = open('./mpia.tpl', 'r').read()

    # Include often missing libraries
    compiler = r"TEXINPUTS='{0:s}/deprecated_tex:' pdflatex".format(__ROOT__)
    compiler_options = r"-enable-write18 -shell-escape -interaction=nonstopmode"

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
            fig += r"    \includegraphics[width=\maxwidth, height=\maxheight,keepaspectratio]{"
            fig += fname + r"}\\" + "\n"
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
                     shutil, get_catchup_papers, check_required_words, check_date)
    options = running_options()
    identifier = options.get('identifier', None)
    paper_request_test = (identifier not in (None, 'None', '', 'none'))
    hl_authors = options.get('hl_authors', None)
    hl_request_test = (hl_authors not in (None, 'None', '', 'none'))
    sourcedir = options.get('sourcedir', None)
    catchup_since = options.get('since', None)

    __DEBUG__ = options.get('debug', False)

    if __DEBUG__:
        print('Debug mode on')

    if not hl_request_test:
        mitarbeiter_list = options.get('mitarbeiter', './mitarbeiter.txt')
        mitarbeiter = get_mitarbeiter(mitarbeiter_list)
    else:
        mitarbeiter = [author.strip() for author in hl_authors.split(',')]

    if sourcedir not in (None, ''):
        paper = DocumentSource(sourcedir)
        paper.identifier = sourcedir
        keep = highlight_papers([paper], mitarbeiter)
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
        keep = filter_papers(papers, mitarbeiter)
    else:
        papers = [ArXivPaper(identifier=identifier.split(':')[-1], appearedon=check_date(options.get('date')))]
        keep = highlight_papers(papers, mitarbeiter)

    institute_words = ['Heidelberg', 'Max', 'Planck', '69117']

    # make sure no duplicated papers
    keep = {k.identifier: k for k in keep}.values()
        
    for paper in keep:
        print(paper)
        try:
            paper.get_abstract()
            s = paper.retrieve_document_source('./tmp')
            institute_test = check_required_words(s, institute_words)
            print("\n**** From Heidelberg: ", institute_test, '\n')
            # Filtering out bad matches
            if (not institute_test) and (not paper_request_test):
                raise RuntimeError('Not an institute paper')
            if (paper_request_test or institute_test):
                s.compile(template=template)
                _identifier = paper.identifier.split(':')[-1]
                name = s.outputname.replace('.tex', '.pdf').split('/')[-1]
                shutil.move('./tmp/' + name, _identifier + '.pdf')
                print("PDF postage:", _identifier + '.pdf' )
            else:
                print("Not from HD... Skip.")
        except Exception as error:
            raise_or_warn(error, debug=__DEBUG__)
        print("Generating postage")

if __name__ == "__main__":
    main(template=MPIATemplate())
