import React, { useState, useEffect } from "react";
import { getRandomQuote } from "../api";

const Test = () => {
    const [quote, setQuote] = useState("");

    useEffect(() => {
        let cancelled = false;
        getRandomQuote()
            .then(({ data }) => {
                if (!cancelled) setQuote(data.quote);
            })
            .catch((err) => {
                console.error("Error fetching quote:", err);
                if (!cancelled) {
                    setQuote("Sorry, we couldn't fetch a quote. Please try again later.");
                }
            });
        return () => {
            cancelled = true;
        };
    }, []);

    return (
        <div className="flex border-2 justify-between rounded-md p-3 border-cyan-400 ml-8">
            <p className="text-sm text-cyan-700">{quote}</p>
        </div>
    );
};

export default Test;