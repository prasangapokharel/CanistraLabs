/** Virtual project file storage — serialized in project.code_content */

export const FILES_MARKER = '__ICP_FILES__:';

export const DEFAULT_FILES: Record<string, string> = {
  'index.html': `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>My Site</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <main>
    <h1>Hello from the Internet Computer</h1>
    <p>Edit this project and click Save & Publish.</p>
  </main>
  <script src="script.js"></script>
</body>
</html>`,
  'style.css': `body {
  font-family: system-ui, sans-serif;
  max-width: 720px;
  margin: 2rem auto;
  padding: 0 1rem;
  line-height: 1.6;
}

h1 { color: #3b82f6; }
`,
  'script.js': `console.log('Running on ICP');
`,
};

export function parseProjectFiles(codeContent: string | null | undefined): Record<string, string> {
  if (!codeContent?.trim()) {
    return { ...DEFAULT_FILES };
  }
  if (codeContent.startsWith(FILES_MARKER)) {
    try {
      const parsed = JSON.parse(codeContent.slice(FILES_MARKER.length)) as Record<string, string>;
      return { ...DEFAULT_FILES, ...parsed };
    } catch {
      return { 'index.html': codeContent, ...DEFAULT_FILES };
    }
  }
  return { 'index.html': codeContent, 'style.css': DEFAULT_FILES['style.css'], 'script.js': DEFAULT_FILES['script.js'] };
}

export function serializeProjectFiles(files: Record<string, string>): string {
  return FILES_MARKER + JSON.stringify(files);
}

/** Bundle virtual files into one HTML document for ICP asset canister deploy */
export function bundleForDeploy(files: Record<string, string>): string {
  let html = files['index.html']?.trim() || DEFAULT_FILES['index.html'];
  const css = files['style.css'] ?? files['styles.css'] ?? '';
  const js = files['script.js'] ?? files['main.js'] ?? '';

  if (css) {
    html = html.replace(/<link[^>]+href=["']style\.css["'][^>]*>/gi, '');
    html = html.replace(/<link[^>]+href=["']styles\.css["'][^>]*>/gi, '');
    if (html.includes('</head>')) {
      html = html.replace('</head>', `<style>\n${css}\n</style>\n</head>`);
    } else {
      html = `<style>\n${css}\n</style>\n` + html;
    }
  }

  if (js) {
    html = html.replace(/<script[^>]+src=["']script\.js["'][^>]*><\/script>/gi, '');
    html = html.replace(/<script[^>]+src=["']main\.js["'][^>]*><\/script>/gi, '');
    if (html.includes('</body>')) {
      html = html.replace('</body>', `<script>\n${js}\n</script>\n</body>`);
    } else {
      html = html + `\n<script>\n${js}\n</script>`;
    }
  }

  return html;
}

export function listFileNames(files: Record<string, string>): string[] {
  return Object.keys(files).sort((a, b) => {
    if (a === 'index.html') return -1;
    if (b === 'index.html') return 1;
    return a.localeCompare(b);
  });
}
