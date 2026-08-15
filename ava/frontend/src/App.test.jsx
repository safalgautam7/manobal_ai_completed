import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('./api', () => ({
    sendPrompt: vi.fn(),
    getRandomQuote: vi.fn(() => Promise.reject(new Error('offline'))),
}));

import { setAuthDisabled } from './auth';
import App from './App';

describe('App in auth-disabled (local dev) mode', () => {
    beforeEach(() => {
        setAuthDisabled(true);
    });

    it('renders the chat interface without Clerk', async () => {
        render(
            <MemoryRouter>
                <App />
            </MemoryRouter>
        );
        expect(screen.getByText('ManobalAI')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Type your message...')).toBeInTheDocument();
    });

    it('does not gate the input behind sign-in', () => {
        render(
            <MemoryRouter>
                <App />
            </MemoryRouter>
        );
        expect(screen.queryByText('Please sign in to use the chatbot.')).not.toBeInTheDocument();
    });
});