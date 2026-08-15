import { describe, it, expect } from 'vitest';
import { toSafeMessageHtml } from '../utils/sanitize';

describe('toSafeMessageHtml', () => {
    it('escapes HTML to prevent XSS', () => {
        const out = toSafeMessageHtml('<script>alert("xss")</script>');
        expect(out).not.toContain('<script>');
        expect(out).toContain('&lt;script&gt;');
    });

    it('turns http/https URLs into safe links', () => {
        const out = toSafeMessageHtml('Visit https://example.com/a?b=1 now');
        expect(out).toContain('href="https://example.com/a?b=1"');
        expect(out).toContain('class="neon-link"');
        expect(out).toContain('target="_blank"');
    });

    it('prepends https to www links', () => {
        const out = toSafeMessageHtml('www.example.org');
        expect(out).toContain('href="https://www.example.org"');
    });

    it('does not allow javascript: URLs', () => {
        const out = toSafeMessageHtml('click javascript:alert(1)');
        expect(out).not.toContain('href="javascript:');
    });

    it('converts newlines to <br/>', () => {
        expect(toSafeMessageHtml('line1\nline2')).toContain('line1<br/>line2');
    });

    it('leaves plain text unchanged', () => {
        const out = toSafeMessageHtml('just a normal message');
        expect(out).toBe('just a normal message');
    });

    it('keeps apostrophes readable (no &#39; entities)', () => {
        const out = toSafeMessageHtml("I don't feel well. It's okay.");
        expect(out).not.toContain('&#39;');
        expect(out).toContain("don't");
        expect(out).toContain("It's");
    });
});