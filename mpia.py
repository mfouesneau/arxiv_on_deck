"""
A quick and dirty parser for ArXiv
===================================

"""
from app import (ExportPDFLatexTemplate, running_options,
                 get_mitarbeiter, get_new_papers, filter_papers)


class MPIATemplate(ExportPDFLatexTemplate):

    template = open('./mpia.tpl', 'r').read()

    compiler = r"TEXINPUTS='../deprecated_tex:' pdflatex"
    compiler_options = r"-enable-write18 -shell-escape -interaction=nonstopmode"

    def short_authors(self, document):
        return document.short_authors

    def figure_to_latex(self, figure):
        fig = ""
        for fname in figure.files:
            fig += r"    \includegraphics[width=\textwidth,keepaspectratio]{"
            fig += fname + r"}\\" + "\n"
        caption = r"""    \caption{Fig. """ + str(figure._number) + """: """ + figure.caption + r"""}"""
        return fig, caption

    def apply_to_document(self, document):

        txt = self.template.replace('<MACROS>', "")    # document._macros)
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
            txt.replace('FIGURE_{0:s}'.format(where), fig)
            txt.replace('CAPTION_{0:s}'.format(where), caption)

        txt = txt.replace('<COMMENTS>', document.comment or '')
        txt = txt.replace('<DATE>', document.date)

        return txt


if __name__ == "__main__":

    options = running_options()
    papers = get_new_papers(skip_replacements=True)
    mitarbeiter_list = options.get('mitarbeiter', './mitarbeiter.txt')
    mitarbeiter = get_mitarbeiter(mitarbeiter_list)
    keep = filter_papers(papers, mitarbeiter)
    for paper in keep:
        print(paper)
        try:
            paper.make_postage(template=MPIATemplate())
        except Exception as error:
            print(error)
