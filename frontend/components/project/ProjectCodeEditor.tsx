'use client';

import { useMemo } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { html } from '@codemirror/lang-html';
import { css } from '@codemirror/lang-css';
import { javascript } from '@codemirror/lang-javascript';
import { json } from '@codemirror/lang-json';
import { oneDark } from '@codemirror/theme-one-dark';
import { useTheme } from 'next-themes';

function languageForFile(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase() ?? '';
  if (ext === 'html' || ext === 'htm') return html();
  if (ext === 'css') return css();
  if (ext === 'js' || ext === 'mjs' || ext === 'cjs') return javascript();
  if (ext === 'json' || ext === 'json5') return json();
  return undefined;
}

interface ProjectCodeEditorProps {
  filename: string;
  value: string;
  onChange: (value: string) => void;
  readOnly?: boolean;
}

export function ProjectCodeEditor({
  filename,
  value,
  onChange,
  readOnly = false,
}: ProjectCodeEditorProps) {
  const { resolvedTheme } = useTheme();

  const extensions = useMemo(() => {
    const lang = languageForFile(filename);
    return lang ? [lang] : [];
  }, [filename]);

  return (
    <CodeMirror
      value={value}
      height="100%"
      theme={resolvedTheme === 'dark' ? oneDark : 'light'}
      extensions={extensions}
      onChange={onChange}
      readOnly={readOnly}
      basicSetup={{
        lineNumbers: true,
        foldGutter: true,
        highlightActiveLine: true,
        indentOnInput: true,
        bracketMatching: true,
        autocompletion: true,
      }}
      className="h-full text-sm [&_.cm-editor]:h-full [&_.cm-scroller]:min-h-[280px] [&_.cm-editor]:rounded-none"
    />
  );
}
