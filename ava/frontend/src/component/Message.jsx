import Typewriter from 'typewriter-effect';
import React, { useEffect, useState } from "react";
import { toSafeMessageHtml } from "../utils/sanitize";

function Message({ text }) {
    const [html, setHtml] = useState("");
    useEffect(() => {
        setHtml(toSafeMessageHtml(text));
    }, [text]);

    return (
        <>
            {html && (
                <div>
                    <Typewriter
                        onInit={(typewriter) => {
                            typewriter
                                .changeDelay(0.4)
                                .typeString(html)
                                .start()
                                .callFunction((s) => {
                                    s.elements.cursor.style.display = "none";
                                });
                        }}
                    />
                </div>
            )}
        </>
    );
}

export default Message;