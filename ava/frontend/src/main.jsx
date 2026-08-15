import ReactDOM from 'react-dom/client';
import './main.css';
import App from './App';
import React, { lazy, Suspense } from 'react';
import {
    createBrowserRouter,
    RouterProvider,
} from "react-router-dom";

import { UserProfile } from "@clerk/clerk-react";
import SignInPage from './component/SignInPage';
import './App.css';
import ErrorPage from './component/ErrorPage';
import UserName from './component/UserName'
import { AuthProvider, SignedIn, UserButton, isAuthDisabled } from './auth'

const GraphPage = lazy(() => import('./component/GraphPage'));


const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

if (!isAuthDisabled() && !PUBLISHABLE_KEY) {
    throw new Error("Missing Publishable Key")
}




const router = createBrowserRouter([
    {
        path: "/",
        errorElement: (
            <ErrorPage />
        ),

        element: (
            <header>
                <SignInPage />
                <SignedIn>
                    <div className="absolute   right-12 mt-5 flex flex-col ">
                        <UserButton
                            appearance={{
                                elements: {
                                    userButtonAvatarBox: "w-10 h-10 rounded-50 ml-9",
                                },
                            }}
                        />
                        <h1 className="  text-sm mt-3  pr-7 text-gray-400 italic font-semibold   ">
                            <UserName />
                        </h1>
                    </div>
                    <App />
                </SignedIn>
            </header>
        ),
    },
    {
        path: "/profile",
        element: isAuthDisabled() ? (
            <div className="flex h-screen flex-col items-center justify-center bg-gray-100 text-gray-500">
                Profile requires Clerk authentication (disabled in local dev mode).
            </div>
        ) : (
            <SignedIn>
                <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
                    <UserProfile
                        appearance={{
                            elements: {},
                        }}
                    />
                </div>
            </SignedIn>
        ),
    },
    {
        path: "/Graph",
        element: (
            <Suspense fallback={<div className="h-screen flex items-center justify-center bg-gray-800 text-gray-200">Loading...</div>}>
                <GraphPage />
            </Suspense>
        ),
    },
]);


ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <AuthProvider publishableKey={PUBLISHABLE_KEY}>
            <RouterProvider router={router} />
        </AuthProvider>
    </React.StrictMode>,
);