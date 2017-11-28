"""
A quick and dirty parser for ArXiv
===================================

"""
from app import (ExportPDFLatexTemplate)


class MPIATemplate(ExportPDFLatexTemplate):

    template = open('./mpia.tpl', 'r').read()

    compiler = r"TEXINPUTS='../deprecated_tex:' pdflatex"
    compiler_options = r"-enable-write18 -shell-escape -interaction=nonstopmode"

    def short_authors(self, document):
        return document.short_authors

    def figure_to_latex(self, figure):
        fig = ""
        for fname in figure.files:
            fig += r"    \includegraphics[width=\maxwidth, height=\maxheight,keepaspectratio]{"
            fig += fname + r"}\\" + "\n"
        if len(figure.files) > 1:
            fig = fig.replace(r'\maxwidth', '{0:0.1f}'.format(0.9 * 1. / len(figure.files)) + r'\maxwidth')
        caption = r"""    \caption{Fig. """ + str(figure._number) + """: """ + figure.caption + r"""}"""
        return fig, caption

    def apply_to_document(self, document):

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
    from app import (get_mitarbeiter, filter_papers, ArXivPaper,
            highlight_papers, running_options, get_new_papers, shutil)
    options = running_options()
    identifier = options.get('identifier', None)
    paper_request_test = (identifier not in (None, 'None', '', 'none'))

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
            paper.get_abstract()
            s = paper.retrieve_document_source('./tmp')
            institute_test = (('Heidelberg' in s._code) or ('heidelberg' in s._code))
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
            print(error, '\n')
        print("Generating postage")

if __name__ == "__main__":
    main(template=MPIATemplate())
