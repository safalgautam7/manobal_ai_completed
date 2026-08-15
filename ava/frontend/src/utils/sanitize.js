const URL_REGEX = /(https?:\/\/[^\s<>"']+|www\.[^\s<>"']+)/g;

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/**
 * Convert a plain-text bot response into safe HTML for the typewriter.
 * Everything is HTML-escaped except validated URLs, which become links.
 */
export function toSafeMessageHtml(text) {
  return String(text)
    .split(URL_REGEX)
    .map((part) => {
      if (!part) return '';
      if (part.startsWith('http') || part.startsWith('www')) {
        const href = part.startsWith('http') ? part : `https://${part}`;
        return (
          `<a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer" class="neon-link">` +
          `${escapeHtml(part)}</a>`
        );
      }
      return escapeHtml(part);
    })
    .join('')
    .replace(/\n/g, '<br/>');
}