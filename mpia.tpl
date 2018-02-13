% Template class ---------------------------------------------
\documentclass[a4paper]{article}
% packages ---------------------------------------------------
% Many of these packages are only for compatibility with
% common articles and their macros
\usepackage[utf8]{inputenc}
% \usepackage[a4paper,margin=.5cm, landscape]{geometry}
\usepackage[a4paper,margin=.5cm]{geometry}
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
\usepackage{tikz}
\usepackage{xcolor}
\usepackage{calc}
\usepackage{ifthen}
\usepackage{xparse} 
\usepackage{xspace} 
% \usepackage{fontspec}
\usepackage{../deprecated_tex/astrojournals}


% Making fitbox environment ----------------------------------------------------
% scales the fontsize of text to fit into a specified box

\sloppypar

\usepackage{environ}% http://ctan.org/pkg/environ
\newdimen\fontdim
\newdimen\upperfontdim
\newdimen\lowerfontdim
\newif\ifmoreiterations
\fontdim12pt

\newbox\trialbox
\newbox\linebox
\global\newcount\maxbad
\newcount\linebad
\newcount\currenthbadness


\makeatletter
\NewEnviron{fitbox}[2]{% \begin{fitbox}{<width>}{<height>} stuff \end{fitbox}
    % Store environment body
    \def\stuff{%
        \BODY%
    }%
    % prepare badness box
    \def\badnessbox{%
        \global\maxbad=0\relax%
        \currenthbadness=\hbadness% save old \hbadness
        \hbadness=10000000\relax% make sure, TeX reports overfull boxes
        \message{Starting measureline recursion with width #1^^J}%
        \setbox\trialbox=\vbox{%
            \hsize#1\relax%
            \fontsize{\fontdim}{1.2\fontdim}%
            \selectfont%
            \stuff\par%
            \measurelines% start recursion
        }%
%       \noindent\usebox\trialbox\par
        \hbadness=\currenthbadness% restore old \hbadness
    }
    % prepare recursion to measure line badness
    \def\measurelines{%
        \message{Iteration of measurelines^^J}%
        \begingroup%
            \setbox\linebox=\lastbox% get the last line
            \setbox0=\hbox to \hsize{\unhcopy\linebox}% put the last line into box0 to provoke badness calculation
            \linebad=\the\badness\relax% \badness now reflects the last typeset box, i.e. box0
            \message{Badness: \the\badness\space\the\linebad\space with max \the\maxbad\space at Fontsize: \the\fontdim\space^^J}%
            \ifnum\linebad>\maxbad% store the maximum badness
                \global\maxbad=\linebad% Uncomment this line to ignore overfull hboxes!
            \fi%
            \ifvoid% end of recursion
                \linebox%
            \else%
                \unskip\unpenalty\measurelines% do the recursion
                \ifhmode%
                    \newline%
                \fi%
                \noindent\box\linebox% do the output
            \fi%
        \endgroup%
    }%
    % Prepare measurement box
    \def\buildbox{%
        \badnessbox% measure badness
        \setbox0\vbox{% measure height
            \hbox{%
                \fontsize{\fontdim}{1.2\fontdim}%
                \selectfont%
                \minipage{#1}%
                    \vbox{%                     
                        \stuff\par%
                    }%
                \endminipage%
            }%
        }%
        \message{Measured badness: \the\maxbad\space at Fontsize: \the\fontdim\space^^J}%
        \dimen@\ht0
        \advance\dimen@\dp0
        \message{Measured box height: \the\dimen@\space^^J}%
    }%
    \def\shrinkheight{%
        \loop
            \fontdim.5\fontdim % Reduce font size by half
            \buildbox
            \message{Shrinking, new box height: \the\dimen@\space at Fontsize: \the\fontdim\space^^J}%
        \ifdim\dimen@>#2 \repeat
        \lowerfontdim\fontdim
        \upperfontdim2\fontdim
        \fontdim1.5\fontdim
    }%
    \def\shrinkwidth{%
        \loop
            \fontdim.5\fontdim % Reduce font size by half
            \buildbox
        \ifnum\maxbad>10000 \repeat
        \lowerfontdim\fontdim
        \upperfontdim2\fontdim
        \fontdim1.5\fontdim
    }%
    \def\growheight{%
        \loop
            \fontdim2\fontdim % Double font size
            \buildbox
            \message{Growing, new box height: \the\dimen@\space at Fontsize: \the\fontdim\space^^J}%
        \ifdim\dimen@<#2 \repeat
        \upperfontdim\fontdim
        \lowerfontdim.5\fontdim
        \fontdim.75\fontdim
    }%
    \buildbox
    % Compute upper and lower bounds
    \ifdim\dimen@>#2
        \message{Need to shrink box height: \the\dimen@\space^^J}%
        \shrinkheight
    \else
        \message{Need to grow box height: \the\dimen@\space to target: #2^^J}%
        \growheight
    \fi
    \message{Max font: \the\upperfontdim\space^^J}%
    \message{Min font: \the\lowerfontdim\space^^J}%
    % Potentially further reduce bounds for overfull box
    \ifnum\maxbad>10000
        \shrinkwidth
    \fi 
    \message{Max font adjusted: \the\upperfontdim\space^^J}%
    \message{Min font adjusted: \the\lowerfontdim\space^^J}%
    % Now try to find the optimum height and width
    \loop
        \buildbox
        \message{Height: \the\dimen@\space^^J}%
        \ifdim\dimen@>#2
            \moreiterationstrue
            \upperfontdim\fontdim
            \advance\fontdim\lowerfontdim
            \fontdim.5\fontdim
        \else
            \ifnum\maxbad>10000
                \moreiterationstrue
                \upperfontdim\fontdim
                \advance\fontdim\lowerfontdim
                \fontdim.5\fontdim
            \else
                \advance\dimen@-#2
                \ifdim\dimen@<10pt
                    \lowerfontdim\fontdim
                    \advance\fontdim\upperfontdim
                    \fontdim.5\fontdim
                    \dimen@\upperfontdim
                    \advance\dimen@-\lowerfontdim
                    \ifdim\dimen@<.2pt
                        \moreiterationsfalse
                    \else
                        \moreiterationstrue
                    \fi
                \else
                    \moreiterationsfalse
                \fi
            \fi
        \fi
    \ifmoreiterations \repeat
    \message{Selected font: \the\fontdim\space^^J}%
    \vbox to #2{\box0\hbox{}}% Typeset content
}%
\makeatother

\usepackage{parskip}

\setlength\fboxsep{0pt}

% Internal macros --------------------------------------------------------------

% convert files on the fly to pdflatex compilation
% requires `-enable-write18 -shell-escape`' compilation options
\DeclareGraphicsExtensions{.jpg, .ps, .eps, .png, .pdf}
% \DeclareGraphicsRule{.ps}{pdf}{.pdf}{`convert -trim +repage #1 pdf:`dirname #1`/`basename #1 .ps`-ps-converted-to.pdf}
% \DeclareGraphicsRule{.eps}{pdf}{.pdf}{`convert -trim +repage #1 pdf:`dirname #1`/`basename #1 .eps`-eps-converted-to.pdf}
% \DeclareGraphicsRule{.pdf}{pdf}{.pdf}{`convert -trim +repage #1 pdf:`dirname #1`/`basename #1 .pdf`-pdf-converted-to.pdf}
% \DeclareGraphicsRule{.png}{pdf}{.pdf}{`convert -trim +repage #1 pdf:`dirname #1`/`basename #1 .png`-png-converted-to.pdf}
% slightly better quality than above
\DeclareGraphicsRule{.ps}{pdf}{.pdf}{`epstopdf #1 -o `dirname #1`/`basename #1 .ps`-ps-converted-to.pdf}
\DeclareGraphicsRule{.eps}{pdf}{.pdf}{`epstopdf #1 -o `dirname #1`/`basename #1 .eps`-eps-converted-to.pdf}

% highlight in yellow some text (e.g., authors)
\newcommand\hl[1]{\colorbox{yellow}{#1}}

% makes abstract macro
\renewcommand{\abstract}[1]{%
  \textbf{\hl{<IDENTIFIER>} } #1
}

% Inhibit most of article macros
\renewcommand{\thanks}[1]{}
\renewcommand{\footnote}[1]{}
\renewcommand{\caption}[1]{{\raggedright\scriptsize{#1}}}
\providecommand{\acronymused}[1]{}
\providecommand{\altaffilmark}[1]{}
\providecommand{\keywords}{}

% Layout definition --------------------------------------------------------
% sets some dimensions
\newlength\Widthtempl% width for 1,2,3,4
\newlength\Highttempl% height for 1
\newlength\gap% separation between boxes
\setlength\gap{4pt}
\setlength\Widthtempl{\dimexpr0.5\textwidth-0.75\gap\relax}
\setlength\Highttempl{.67\textheight}
\def\maxheight{0.25\paperheight}
\def\maxwidth{\textwidth}
\parindent0pt
\fboxsep0pt
\fboxrule0pt

% Will be used to store the first figure properties
\newsavebox\boxFigOne

% debugging macros
% \renewcommand{\frame}{}   % using lines around frames for layout debugging
\renewcommand{\frame}[1]{\colorbox{white}{#1}}   % using lines around frames for layout debugging

% Often used journal defined commands
\providecommand{\arcsec}[1]{\hbox{$^{\prime\prime}$}}
\providecommand{\farcs}[1]{\hbox{$.\!\!^{\prime\prime}$}}
\providecommand{\degr}[1]{\hbox{$^\circ$}}
\providecommand{\fdg}[1]{\hbox{$.\!\!^\circ$}}
\providecommand{\arcmin}[1]{\hbox{$^\prime$}}
\providecommand{\farcm}[1]{\hbox{$.\mkern-4mu^\prime$}}
\providecommand{\la}{\lesssim}
\providecommand{\ga}{\gtrsim}


\newcommand\ion[2]{#1$\;${%
\ifx\@currsize\normalsize\small \else
\ifx\@currsize\small\footnotesize \else
\ifx\@currsize\footnotesize\scriptsize \else
\ifx\@currsize\scriptsize\tiny \else
\ifx\@currsize\large\normalsize \else
\ifx\@currsize\Large\large
\fi\fi\fi\fi\fi\fi
\rmfamily\@Roman{#2}}\relax}% 

%Document found macros ------------------------------------------------------
<MACROS>

% ----------------------------------------------------------------------------------
\begin{document}
% ----------------------------------------------------------------------------------
\thispagestyle{plain}

% title 
\textbf{\LARGE{<TITLE>}}

\vspace{1em}

% Authors
\textbf{\large{<AUTHORS>}}

\hl{<DATE>} -- <COMMENTS>
\vspace{1em}

% Abstract
\begin{fitbox}{2\Widthtempl}{0.2\Highttempl}
	\abstract{ <ABSTRACT> }
\end{fitbox}

% defined automatically
\def\figone{<FIGURE_ONE>}
\def\capone{<CAPTION_ONE>}

\def\figtwo{<FIGURE_TWO>}
\def\captwo{<CAPTION_TWO>}

\def\figthree{<FIGURE_THREE>}
\def\capthree{<CAPTION_THREE>}


% Figure layout decision --------------------------------------------------------
% check figure 1 aspect and adopt the following layouts
% landscape generates 
%
% -----------
% |         |
% -----------
% |    |    |
% -----------
%
% portrait will generate
% -----------
% |    |    |
% |    |----|
% |    |    |
% -----------

% store the figure into a box to retrieve properties
\savebox{\boxFigOne}{<FILE_FIGURE_ONE>}

% For DEBUGGING \pgfmathsetmacro{\ratio}{\the\ht\boxFigOne/\the\wd\boxFigOne}
% \pgfmathsetmacro{\ratio}{\the\wd\boxFigOne/\the\ht\boxFigOne}
% \pgfmathparse{\ratio > 1?int(1):int(0)}
% Ratio: \ratio
\pgfmathparse{\the\wd\boxFigOne/\the\ht\boxFigOne > 1.2 ? int(1):int(0)}


% test orientation
\ifnum\pgfmathresult=1\relax% 
% ------------------------------------------------------------------ {landscape}
\def\maxheight{0.25\paperheight}
\def\maxwidth{\textwidth}
\frame{%
  \begin{minipage}[t][0.5\Highttempl][t]{2\Widthtempl}%
    \vspace*{\fill}
    {\begin{center}\figone\end{center}}  % put contents here
    \capone
    \vspace*{\fill} \ 
  \end{minipage}}% 
\par
\fbox{%
  \begin{minipage}[t][0.49\Highttempl][t]{2\Widthtempl+\gap}
    \frame{\ %
      \begin{minipage}[t][0.5\Highttempl][t]{\Widthtempl-\gap}
        \vspace*{\fill}
	{\begin{center}\figtwo\end{center}}
        \captwo
	\vspace*{\fill} \ 
      \end{minipage}}
    \frame{\ %
      \begin{minipage}[t][0.5\Highttempl][t]{\Widthtempl-\gap}
	   \vspace*{\fill}
           {\begin{center}\figthree\end{center}}
	   \capthree
	   \vspace*{\fill}
	 \end{minipage}}
	\end{minipage}}
\else
% ------------------------------------------------------------------ {portrait}
	\def\maxheight{0.4\paperheight}
	\def\maxwidth{\textwidth}
	\frame{%
	\begin{minipage}[b][1\Highttempl][t]{1\Widthtempl}%
         \vspace*{\fill}
	 {\begin{center}\figone\end{center}}  % put contents here
         \capone
         \vspace*{\fill} \ 
		\end{minipage}}%
	\fbox{%
		\def\maxheight{0.3\paperheight}
		\begin{minipage}[b][1\Highttempl][t]{\Widthtempl+1\gap}
			\frame{\ %
        \begin{minipage}[t][0.5\Highttempl][t]{\Widthtempl}
	\vspace*{\fill}
	  {\begin{center}\figtwo\end{center}}
          \captwo
         \vspace*{\fill} \ 
			\end{minipage}}
			\frame{\ %
		\begin{minipage}[t][0.5\Highttempl][t]{\Widthtempl}
				  \vspace*{\fill}
		{\begin{center}\figthree\end{center}}
            \capthree
            \vspace*{\fill} \ 
        \end{minipage}}
	\end{minipage}}
\fi
			  
% add bottom text -------------------------------------------------------------------
% \frame{
%   \begin{minipage}[b][0.05\Highttempl][b]{2\Widthtempl}
% 	\hl{<DATE>} -- <COMMENTS>
%    \end{minipage}
% }

\end{document}
% -------------------------------------------------------------------------------------
