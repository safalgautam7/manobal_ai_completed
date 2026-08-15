import { describe, it, expect, vi, beforeEach } from 'vitest';

const { mockPost, mockGet } = vi.hoisted(() => ({
    mockPost: vi.fn(),
    mockGet: vi.fn(),
}));

vi.mock('axios', () => ({
    default: {
        create: () => ({ post: mockPost, get: mockGet }),
    },
}));

import { sendPrompt, analyzeEmotion, getEmotionGraph, getRandomQuote } from './api';

describe('api client', () => {
    beforeEach(() => {
        mockPost.mockReset();
        mockGet.mockReset();
    });

    it('sendPrompt posts query and session to /prompt', async () => {
        mockPost.mockResolvedValue({ data: { response: 'hi' } });
        await sendPrompt('hello', 'abc123');
        expect(mockPost).toHaveBeenCalledWith('/prompt', { query: 'hello', session_id: 'abc123' });
    });

    it('sendPrompt handles missing session id', async () => {
        mockPost.mockResolvedValue({ data: { response: 'hi' } });
        await sendPrompt('hello', null);
        expect(mockPost).toHaveBeenCalledWith('/prompt', { query: 'hello', session_id: null });
    });

    it('analyzeEmotion posts text', async () => {
        mockPost.mockResolvedValue({ data: { emotion: 'joy' } });
        await analyzeEmotion('I am happy');
        expect(mockPost).toHaveBeenCalledWith('/analyze-emotion', { text: 'I am happy' });
    });

    it('getEmotionGraph and getRandomQuote hit the right endpoints', async () => {
        mockGet.mockResolvedValue({ data: {} });
        await getEmotionGraph();
        expect(mockGet).toHaveBeenCalledWith('/emotion-graph');

        mockGet.mockResolvedValue({ data: { quote: 'q' } });
        await getRandomQuote();
        expect(mockGet).toHaveBeenCalledWith('/random-quote');
    });

    it('rejects propagate errors to callers', async () => {
        mockPost.mockRejectedValue(new Error('network'));
        await expect(sendPrompt('hello', null)).rejects.toThrow('network');
    });
});