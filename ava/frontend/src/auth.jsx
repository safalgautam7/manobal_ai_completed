import React, { createContext, useContext } from 'react';
import {
    ClerkProvider as ClerkProviderBase,
    SignedIn as ClerkSignedIn,
    SignedOut as ClerkSignedOut,
    UserButton as ClerkUserButton,
    useUser as useClerkUser,
} from '@clerk/clerk-react';

/**
 * Local-development auth.
 *
 * When `VITE_AUTH_DISABLED=true` (or no Clerk publishable key is configured)
 * the app renders without Clerk and `useUser()` returns a dummy signed-in
 * user, so the UI can be developed/tested without a Clerk account.
 */

let authDisabled =
    import.meta.env.VITE_AUTH_DISABLED === 'true' ||
    !import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

export function isAuthDisabled() {
    return authDisabled;
}

export function setAuthDisabled(value) {
    authDisabled = value;
}

const DevUserContext = createContext({
    isSignedIn: true,
    isLoaded: true,
    user: { firstName: 'Dev', lastName: 'User', fullName: 'Dev User', id: 'dev-user' },
});

export function useUser() {
    if (isAuthDisabled()) return useContext(DevUserContext);
    return useClerkUser();
}

export function SignedIn({ children }) {
    if (isAuthDisabled()) return <>{children}</>;
    return <ClerkSignedIn>{children}</ClerkSignedIn>;
}

export function SignedOut({ children }) {
    if (isAuthDisabled()) return null;
    return <ClerkSignedOut>{children}</ClerkSignedOut>;
}

export function UserButton() {
    if (isAuthDisabled()) {
        return (
            <div
                className="flex h-10 w-10 items-center justify-center rounded-full bg-cyan-600 font-bold text-white"
                title="Dev user"
            >
                D
            </div>
        );
    }
    return <ClerkUserButton />;
}

export function AuthProvider({ publishableKey, children }) {
    if (isAuthDisabled()) return <>{children}</>;
    return (
        <ClerkProviderBase publishableKey={publishableKey} afterSignOutUrl="/">
            {children}
        </ClerkProviderBase>
    );
}