# =============================================================================
# OsdagBridge Report Tables — Repeating Header Post-Processor
# =============================================================================
"""Post-processor to add repeating headers to longtable environments.

This module provides the add_repeating_headers() function that automatically
injects \\endfirsthead and \\endhead blocks into longtable environments that
have single-row bold headers but no existing header repetition.

Algorithm (per implementation_plan.md section 6.2):
1. Find each \\begin{longtable} in the LaTeX source
2. Skip tables that already have a non-empty \\endhead block
3. Detect single-row headers: first row after \\hline where every cell starts with \\textbf{
4. Inject:
   - first head = caption + header + \\endfirsthead
   - continuation head = (continued) + header + \\endhead
5. Leave multi-row headers (\\multirow, \\cline, etc.) unchanged
"""

import re
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Helper Functions
# =============================================================================

def _match_brace(s: str, i: int) -> int:
    """Return the index of the '}' that closes the '{' at s[i].
    
    Ignores escaped braces (\\{ and \\}).
    
    Args:
        s: The string to search
        i: Index of the opening '{'
        
    Returns:
        Index of the matching '}', or -1 if not found
    """
    if i >= len(s) or s[i] != '{':
        return -1
    
    depth = 1
    j = i + 1
    while j < len(s) and depth > 0:
        if s[j] == '\\':
            j += 2  # Skip escaped character
            continue
        if s[j] == '{':
            depth += 1
        elif s[j] == '}':
            depth -= 1
        j += 1
    
    return j - 1 if depth == 0 else -1


def count_columns(spec: str) -> int:
    """Count columns in a tabular/longtable column specification.
    
    Counts column-defining characters (l, c, r, p, m, b, L, C, R, X) at
    brace depth 0. Characters inside {...} (widths, >{...} prefixes, @{...})
    are ignored.
    
    Args:
        spec: Column specification string (e.g. "|C{2.5cm}|L{3cm}|")
        
    Returns:
        Number of columns
    """
    depth = 0
    n = 0
    for ch in spec:
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        elif depth == 0 and ch in 'lcrpmbLCRX':
            n += 1
    return n


def _find_header_row(body: str, start: int) -> tuple:
    """Find the header row in a longtable body.
    
    Looks for the pattern: \\hline ... \\\\ ... \\hline
    
    Args:
        body: Table body text
        start: Starting position in body
        
    Returns:
        Tuple of (header_start, header_end, row_content) or (None, None, None)
    """
    # Find first \hline
    hline1 = body.find(r'\hline', start)
    if hline1 == -1:
        return (None, None, None)
    
    # Find first \\ after the hline (end of header row)
    row_end_search = hline1 + 6  # len('\\hline')
    row_end = body.find(r'\\', row_end_search)
    if row_end == -1:
        return (None, None, None)
    
    # Skip optional [6pt] or similar spacing
    bracket_start = row_end + 2
    while bracket_start < len(body) and body[bracket_start] in ' \t\n':
        bracket_start += 1
    if bracket_start < len(body) and body[bracket_start] == '[':
        bracket_end = body.find(']', bracket_start)
        if bracket_end != -1:
            row_end = bracket_end + 1
    
    # Find second \hline (closing the header)
    hline2 = body.find(r'\hline', row_end)
    if hline2 == -1:
        return (None, None, None)
    
    # Extract row content between hlines
    row_content = body[hline1 + 6:row_end].strip()
    
    return (hline1, hline2 + 6, row_content)


def _is_bold_header(row_content: str) -> bool:
    """Check if a row is a single-row bold header.
    
    A row is considered a bold header if every cell (separated by &) starts
    with \\textbf{.
    
    Args:
        row_content: The content between \\hline and \\\\ (header row)
        
    Returns:
        True if every cell starts with \\textbf{
    """
    # Split on unescaped &
    cells = []
    current = []
    i = 0
    while i < len(row_content):
        if row_content[i] == '\\':
            if i + 1 < len(row_content):
                current.append(row_content[i:i+2])
                i += 2
            else:
                i += 1
        elif row_content[i] == '&':
            cells.append(''.join(current).strip())
            current = []
            i += 1
        else:
            current.append(row_content[i])
            i += 1
    cells.append(''.join(current).strip())
    
    # Check if every cell starts with \textbf{
    if not cells:
        return False
    
    for cell in cells:
        if not cell.startswith(r'\textbf{'):
            return False
    
    return True


# =============================================================================
# Main Post-Processor
# =============================================================================

def add_repeating_headers(latex: str) -> str:
    """Add repeating headers to longtable environments in LaTeX source.
    
    This function processes all \\begin{longtable} environments in the input
    and adds \\endfirsthead and \\endhead blocks to tables that:
    - Have a single-row bold header (every cell starts with \\textbf{)
    - Do NOT already have a non-empty \\endhead block
    
    Tables with existing working headers (chap4 style) are unchanged.
    Tables with empty \\endhead blocks (chap2 style) are repaired.
    
    Args:
        latex: Full LaTeX document source
        
    Returns:
        Modified LaTeX source with repeating headers added
    """
    result = []
    pos = 0
    tables_processed = 0
    tables_modified = 0
    
    while True:
        # Find next \begin{longtable}
        start = latex.find(r'\begin{longtable}', pos)
        if start == -1:
            # No more tables, append rest of document
            result.append(latex[pos:])
            break
        
        # Append text before this table
        result.append(latex[pos:start])
        
        # Find the column spec (between { and })
        spec_start = start + len(r'\begin{longtable}')
        while spec_start < len(latex) and latex[spec_start] in ' \t\n':
            spec_start += 1
        
        # Skip optional [pos] argument
        if spec_start < len(latex) and latex[spec_start] == '[':
            bracket_end = latex.find(']', spec_start)
            if bracket_end != -1:
                spec_start = bracket_end + 1
                while spec_start < len(latex) and latex[spec_start] in ' \t\n':
                    spec_start += 1
        
        if spec_start >= len(latex) or latex[spec_start] != '{':
            # Malformed table, skip
            result.append(latex[start:spec_start])
            pos = spec_start
            continue
        
        spec_end = _match_brace(latex, spec_start)
        if spec_end == -1:
            # Malformed table, skip
            result.append(latex[start:spec_start + 1])
            pos = spec_start + 1
            continue
        
        col_spec = latex[spec_start + 1:spec_end]
        n_cols = count_columns(col_spec)
        
        # Find \end{longtable}
        table_end = latex.find(r'\end{longtable}', spec_end)
        if table_end == -1:
            # Unclosed table, skip
            result.append(latex[start:spec_end + 1])
            pos = spec_end + 1
            continue
        
        # Extract table body
        body_start = spec_end + 1
        body = latex[body_start:table_end]
        
        tables_processed += 1
        
        # Check if table already has a non-empty \endhead
        has_endhead = r'\endhead' in body
        has_endfirsthead = r'\endfirsthead' in body
        
        if has_endhead and has_endfirsthead:
            # Check if it's the empty chap2 pattern: \endfirsthead followed immediately by \endhead
            firsthead_pos = body.find(r'\endfirsthead')
            endhead_pos = body.find(r'\endhead', firsthead_pos)
            between = body[firsthead_pos + len(r'\endfirsthead'):endhead_pos].strip()
            if not between or between.replace('\n', '').replace(' ', '') == '':
                # Empty endhead, repair it
                pass  # Continue to processing
            else:
                # Working header exists, leave unchanged
                result.append(latex[start:table_end + len(r'\end{longtable}')])
                pos = table_end + len(r'\end{longtable}')
                continue
        elif has_endhead and not has_endfirsthead:
            # Has bare \endhead without \endfirsthead - this is broken, repair it
            pass  # Continue to processing
        elif not has_endhead:
            # No headers at all, add them
            pass  # Continue to processing
        
        # Find the header row
        header_start, header_end, row_content = _find_header_row(body, 0)
        
        if header_start is None or not _is_bold_header(row_content):
            # Not a simple bold header or no header found, skip
            result.append(latex[start:table_end + len(r'\end{longtable}')])
            pos = table_end + len(r'\end{longtable}')
            continue
        
        # Check if there's a caption before the header
        caption_start_match = re.search(r'\\caption\{', body[:header_start])
        if caption_start_match:
            # Find the matching closing brace for the caption
            cap_brace_start = caption_start_match.end() - 1  # Position of the {
            cap_brace_end = _match_brace(body, cap_brace_start)
            if cap_brace_end != -1:
                caption_text = body[caption_start_match.start():cap_brace_end + 1]
                caption_end = cap_brace_end + 1
            else:
                caption_text = ''
                caption_end = 0
        else:
            caption_text = ''
            caption_end = 0
        
        # Extract the header row (from first \hline to second \hline)
        full_header = body[header_start:header_end]
        
        # Build first head block (caption + header + \endfirsthead)
        first_head = caption_text
        if caption_text:
            first_head += '\n'
        first_head += full_header + '\n' + r'\endfirsthead'
        
        # Build continuation head block
        # Check if spec starts with | for multicolumn borders
        has_leading_pipe = col_spec.strip().startswith('|')
        border = '|c|' if has_leading_pipe else 'c'
        
        continuation_head = (
            r'\hline' + '\n'
            + r'\multicolumn{' + str(n_cols) + r'}{' + border + r'}{\small\textit{(continued)}} \\' + '\n'
            + full_header + '\n'
            + r'\endhead'
        )
        
        # Reconstruct table body
        before_header = body[caption_end:header_start]
        after_header = body[header_end:]
        
        # If there was a bare \endhead in the original, remove it
        if has_endhead and not (has_endfirsthead and r'\endfirsthead' in before_header + full_header[:header_end - header_start]):
            after_header = after_header.replace(r'\endhead', '', 1)
        
        new_body = (
            before_header
            + first_head + '\n'
            + continuation_head + '\n'
            + after_header
        )
        
        # Append modified table
        result.append(latex[start:body_start])
        result.append(new_body)
        result.append(r'\end{longtable}')
        
        tables_modified += 1
        pos = table_end + len(r'\end{longtable}')
    
    logger.info(f"add_repeating_headers: processed {tables_processed} tables, modified {tables_modified}")
    
    return ''.join(result)
