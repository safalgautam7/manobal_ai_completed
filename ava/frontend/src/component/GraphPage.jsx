import React, { useState } from "react";
import { analyzeEmotion, getEmotionGraph } from "../api";

const MAX_BAR_WIDTH = 100;

const Graph = () => {
    const [userInput, setUserInput] = useState("");
    const [emotionResult, setEmotionResult] = useState(null);
    const [error, setError] = useState("");
    const [graphData, setGraphData] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!userInput.trim()) {
            setError("Please enter some text to analyze.");
            return;
        }
        setError("");
        setEmotionResult(null);
        try {
            const { data } = await analyzeEmotion(userInput);
            setEmotionResult(data);
            setUserInput("");
        } catch (err) {
            console.error(err);
            setError("An error occurred while analyzing the emotion.");
        }
    };

    const generateGraph = async () => {
        setError("");
        setGraphData(null);
        try {
            const { data } = await getEmotionGraph();
            const max = Math.max(...Object.values(data), 1);
            setGraphData({ counts: data, max });
        } catch (err) {
            console.error(err);
            setError("An error occurred while loading the emotion graph.");
        }
    };

    return (
        <>
            <div className="p-6 bg-gray-800 text-gray-200 min-h-screen flex flex-col items-center">
                {/* Back Button */}
                <button
                    onClick={() => window.history.back()}
                    className="self-start mb-4 px-4 py-2 bg-red-600 text-white font-semibold rounded-lg transition-all duration-300 hover:shadow-lg hover:shadow-red-400 focus:ring-2 focus:ring-red-500"
                >
                    Back
                </button>

                {/* Analyze Emotion Form */}
                <form onSubmit={handleSubmit} className="w-full max-w-md">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            placeholder="Type something to analyze..."
                            value={userInput}
                            onChange={(e) => setUserInput(e.target.value)}
                            className="flex-grow bg-gray-700 text-gray-200 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        />
                        <button
                            type="submit"
                            className="px-6 py-3 bg-cyan-600 text-white font-semibold rounded-lg transition-all duration-300 hover:shadow-lg hover:shadow-cyan-400 focus:ring-2 focus:ring-cyan-500"
                        >
                            Analyze
                        </button>
                    </div>
                </form>

                {/* Emotion Result */}
                {emotionResult && (
                    <div className="mt-6 bg-gray-700 p-4 rounded-lg shadow-md w-full max-w-md">
                        <h3 className="text-lg font-bold text-cyan-400">Detected Emotion</h3>
                        <p className="mt-2 text-lg">
                            Emotion: <span className="font-semibold">{emotionResult.emotion}</span>
                        </p>
                        <p className="mt-1">
                            Confidence Score:{" "}
                            <span className="font-mono">{Number(emotionResult.score).toFixed(4)}</span>
                        </p>
                        {emotionResult.suggestion && (
                            <p className="mt-3 text-sm text-gray-300">{emotionResult.suggestion}</p>
                        )}
                    </div>
                )}

                {/* Error Message */}
                {error && <p className="mt-4 text-red-500 font-semibold">{error}</p>}

                {/* Generate Graph Button */}
                <button
                    onClick={generateGraph}
                    className="mt-6 px-6 py-3 bg-indigo-600 text-white font-semibold rounded-lg transition-all duration-300 hover:shadow-lg hover:shadow-indigo-400 focus:ring-2 focus:ring-indigo-500"
                >
                    Generate Emotion Graph
                </button>

                {/* Display Graph */}
                {graphData && (
                    <div className="mt-6 bg-gray-700 p-4 rounded-lg shadow-md w-full max-w-2xl">
                        <h3 className="text-xl font-bold text-indigo-400">Emotion Graph</h3>
                        <div className="mt-4 space-y-3">
                            {Object.entries(graphData.counts).map(([emotion, count]) => (
                                <div key={emotion} className="flex items-center gap-3">
                                    <span className="w-28 text-sm capitalize">{emotion}</span>
                                    <div className="flex-grow bg-gray-900 rounded h-6 overflow-hidden">
                                        <div
                                            className="h-full bg-cyan-500"
                                            style={{
                                                width: `${Math.max(
                                                    (count / graphData.max) * MAX_BAR_WIDTH,
                                                    4
                                                )}%`,
                                            }}
                                        />
                                    </div>
                                    <span className="w-8 text-right text-sm">{count}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </>
    );
};

export default Graph;