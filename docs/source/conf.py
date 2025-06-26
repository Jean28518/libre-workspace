# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import datetime

project = 'Libre Workspace'
copyright = f'{datetime.datetime.now().year}, Jean28518'
author = 'Jean28518'

release = ''
version = ''

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'

language = 'en'

latex_engine = 'xelatex' # or 'lualatex'

latex_elements = {
    'papersize': 'a4paper',
    # 'pointsize': '10pt', # Default font size

    'preamble': r'''
\usepackage{fontspec} % Required for font selection with Xe/LuaLaTeX
% \setmainfont{Lato} % Example: Use Lato font (must be installed on your system)
% \setsansfont{Fira Sans} % Example: Use Fira Sans for sans-serif
% \setmonofont{Fira Mono} % Example: Use Fira Mono for code blocks

\usepackage{geometry} % For page layout
\geometry{a4paper, margin=1in} % Adjust margins

\usepackage{titlesec} % For customizing section titles
% Example: Simpler section headings
\titleformat{\chapter}{\Huge\bfseries}{\thechapter}{1em}{}
\titleformat{\section}{\Large\bfseries}{\thesection}{1em}{}
\titleformat{\subsection}{\large\bfseries}{\thesubsection}{1em}{}

\usepackage{microtype} % Improves typography (subtle but nice)

% Add other custom packages or commands here
''',
    # Other elements like 'figure_align', 'maketitle', etc. can be customized too
}
