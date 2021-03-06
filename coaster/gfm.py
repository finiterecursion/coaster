# -*- coding: utf-8 -*-
"""
GitHub Flavoured Markdown: because normal markdown has some vicious
gotchas.

Further reading on the gotchas:
http://blog.stackoverflow.com/2009/10/markdown-one-year-later/

This is a Python port of GitHub code, taken from
https://gist.github.com/Wilfred/901706
"""

from markdown import Markdown
import re

__all__ = ['gfm', 'markdown']

markdown_convert = Markdown(safe_mode='escape', output_format='html5',
    enable_attributes=False,
    extensions=['codehilite'],
    extension_configs={'codehilite': {'css_class': 'syntax'}}
    ).convert


def remove_pre_blocks(markdown_source):
    # replace <pre> blocks with placeholders, so we don't accidentally
    # muck up stuff inside the block with our other transformations
    original_blocks = []

    pattern = re.compile(r'<pre>.*?</pre>', re.MULTILINE | re.DOTALL)

    while re.search(pattern, markdown_source):
        # save the original block
        original_block = re.search(pattern, markdown_source).group(0)
        original_blocks.append(original_block)

        # put in a placeholder
        markdown_source = re.sub(pattern, '{placeholder}', markdown_source,
                                 count=1)

    return (markdown_source, original_blocks)


def remove_inline_code_blocks(markdown_source):
    original_blocks = []

    pattern = re.compile(r'`.*?`', re.DOTALL)

    while re.search(pattern, markdown_source):
        # save the original block
        original_block = re.search(pattern, markdown_source).group(0)
        original_blocks.append(original_block)

        # put in a placeholder
        markdown_source = re.sub(pattern, '{placeholder}', markdown_source,
                                 count=1)

    return (markdown_source, original_blocks)


CODEPATTERN_RE = re.compile('^```(.*?)\n(.*?)^```$', re.MULTILINE | re.UNICODE | re.DOTALL)
ITALICSPATTERN_RE = re.compile(r'^(?! {4}|\t).*\w+(?<!_)_\w+_\w[\w_]*', re.MULTILINE | re.UNICODE)
NAKEDURL_RE = re.compile("""
(^|\s) # start of string or has whitespace before it
(https?://[:/.?=&;a-zA-Z0-9_-]+) # the URL itself, http or https only
(\s|$) # trailing whitespace or end of string
""", re.VERBOSE | re.MULTILINE | re.UNICODE)
NEWLINE_RE = re.compile(r'^[\w\<][^\n]*(\n+)', re.MULTILINE | re.UNICODE)


def gfm(text):
    """
    Prepare text for rendering by a regular Markdown processor.
    """
    def indent_code(matchobj):
        syntax = matchobj.group(1)
        code = matchobj.group(2)
        if syntax:
            result = '    :::' + syntax + '\n'
        else:
            result = ''
        # The last line will be blank since it had the closing "```". Discard it
        # when indenting the lines.
        return result + '\n'.join(['    ' + line for line in code.split('\n')[:-1]])

    use_crlf = text.find('\r') != -1
    if use_crlf:
        text = text.replace('\r\n', '\n')

    # Render GitHub-style ```code blocks``` into Markdown-style 4-space indented blocks
    text = CODEPATTERN_RE.sub(indent_code, text)

    text, code_blocks = remove_pre_blocks(text)
    text, inline_blocks = remove_inline_code_blocks(text)

    # Prevent foo_bar_baz from ending up with an italic word in the middle.
    def italic_callback(matchobj):
        s = matchobj.group(0)
        # don't mess with URLs:
        if 'http:' in s or 'https:' in s:
            return s

        return s.replace('_', '\_')

    # fix italics for code blocks
    text = ITALICSPATTERN_RE.sub(italic_callback, text)

    # linkify naked URLs
    # wrap the URL in brackets: http://foo -> [http://foo](http://foo)
    text = NAKEDURL_RE.sub(r'\1[\2](\2)\3', text)

    # In very clear cases, let newlines become <br /> tags.
    def newline_callback(matchobj):
        if len(matchobj.group(1)) == 1:
            return matchobj.group(0).rstrip() + '  \n'
        else:
            return matchobj.group(0)

    text = NEWLINE_RE.sub(newline_callback, text)

    # now restore removed code blocks
    removed_blocks = code_blocks + inline_blocks
    for removed_block in removed_blocks:
        text = text.replace('{placeholder}', removed_block, 1)

    if use_crlf:
        text = text.replace('\n', '\r\n')

    return text


def markdown(text):
    """
    Return Markdown rendered text using GitHub Flavoured Markdown,
    with HTML escaped and syntax-highlighting enabled.
    """
    if text is None:
        return None
    return markdown_convert(gfm(text))
