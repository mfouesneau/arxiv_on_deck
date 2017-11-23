"""
A quick and dirty parser for ArXiv
===================================

"""
from app import (ExportPDFLatexTemplate, main)


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


if __name__ == "__main__":
    main(template=MPIATemplate())
