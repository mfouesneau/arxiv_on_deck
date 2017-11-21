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

% Internal macros --------------------------------------------------------------

% convert files on the fly to pdflatex compilation
% requires `-enable-write18 -shell-escape`' compilation options
\DeclareGraphicsExtensions{.jpg, .ps, .eps, .png, .pdf}
\DeclareGraphicsRule{.ps}{pdf}{.pdf}{`convert -trim +repage #1 pdf:`dirname #1`/`basename #1 .ps`-ps-converted-to.pdf}
\DeclareGraphicsRule{.eps}{pdf}{.pdf}{`convert -trim +repage #1 pdf:`dirname #1`/`basename #1 .eps`-eps-converted-to.pdf}
\DeclareGraphicsRule{.pdf}{pdf}{.pdf}{`convert -trim +repage #1 pdf:`dirname #1`/`basename #1 .pdf`-pdf-converted-to.pdf}
\DeclareGraphicsRule{.png}{pdf}{.pdf}{`convert -trim +repage #1 pdf:`dirname #1`/`basename #1 .png`-png-converted-to.pdf}

% highlight in yellow some text (e.g., authors)
\newcommand\hl[1]{\colorbox{yellow}{#1}}

% makes abstract macro
\renewcommand{\abstract}[1]{%
  \textbf{\hl{arXiv:1711.03971} } #1
}

% Inhibit most of article macros
\renewcommand{\thanks}[1]{}
\renewcommand{\caption}[1]{{\raggedright\scriptsize{#1}}}
\providecommand{\acronymused}[1]{}
\providecommand{\altaffilmark}[1]{}
\providecommand{\keywords}{}

% Layout definition --------------------------------------------------------
% sets some dimensions
\newlength\Wi% width for 1,2,3,4
\newlength\Hi% height for 1
\newlength\gap% separation between boxes
\setlength\gap{4pt}
\setlength\Wi{\dimexpr0.5\textwidth-0.75\gap\relax}
\setlength\Hi{.7\textheight}
\parindent0pt
\fboxsep0pt
\fboxrule0pt

% Will be used to store the first figure properties
\newsavebox\boxFigOne

% debugging macros
% \renewcommand{\frame}{}   % using lines around frames for layout debugging
\renewcommand{\frame}[1]{\colorbox{white}{#1}}   % using lines around frames for layout debugging

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

\vspace{1em}

% Abstract
\frame{
	\begin{minipage}[t][0.25\Hi][t]{2\Wi}%
		\abstract{ 
			<ABSTRACT> 
		}
	\end{minipage}
}

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
  \begin{minipage}[t][0.5\Hi][t]{2\Wi}%
    \vspace*{\fill}
    {\begin{center}\figone\end{center}}\\  % put contents here
    \capone
    \vspace*{\fill} \ 
  \end{minipage}}% 
\par
\fbox{%
  \begin{minipage}[t][0.49\Hi][t]{2\Wi+\gap}
    \frame{\ %
      \begin{minipage}[t][0.5\Hi][t]{\Wi-\gap}
        \vspace*{\fill}
	{\begin{center}\figtwo\end{center}}\\
        \captwo
	\vspace*{\fill} \ 
      \end{minipage}}
    \frame{\ %
      \begin{minipage}[t][0.5\Hi][t]{\Wi-\gap}
	   \vspace*{\fill}
           {\begin{center}\figthree\end{center}}\\
	   \capthree
	   \vspace*{\fill}
	 \end{minipage}}
	\end{minipage}}
\else
% ------------------------------------------------------------------ {portrait}
	\def\maxheight{0.4\paperheight}
	\def\maxwidth{\textwidth}
	\frame{%
	\begin{minipage}[b][1\Hi][t]{1\Wi}%
         \vspace*{\fill}
	 {\begin{center}\figone\end{center}}\\  % put contents here
         \capone
         \vspace*{\fill} \ 
		\end{minipage}}%
	\fbox{%
		\def\maxheight{0.3\paperheight}
		\begin{minipage}[b][1\Hi][t]{\Wi+1\gap}
			\frame{\ %
        \begin{minipage}[t][0.5\Hi][t]{\Wi}
	\vspace*{\fill}
	  {\begin{center}\figtwo\end{center}}\\
          \captwo
         \vspace*{\fill} \ 
			\end{minipage}}
			\frame{\ %
		\begin{minipage}[t][0.5\Hi][t]{\Wi}
				  \vspace*{\fill}
		{\begin{center}\figthree\end{center}}\\
            \capthree\\
            \vspace*{\fill} \ 
        \end{minipage}}
	\end{minipage}}
\fi
			  
% add bottom text -------------------------------------------------------------------
\frame{
  \begin{minipage}[b][0.05\Hi][b]{2\Wi}
	\hl{<DATE>} -- <COMMENTS>
   \end{minipage}
}

\end{document}
% -------------------------------------------------------------------------------------
