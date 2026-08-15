import asyncio

import numpy as np
import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app import chat, db


def test_history_to_string():
    messages = [
        {"role": "user", "content": "hi"},
        {"role": "bot", "content": "hello"},
    ]
    assert chat._history_to_string(messages) == "Human: hi\nBot: hello"


class FakeEmb(Embeddings):
    def embed_documents(self, texts):
        return [self._embed(t) for t in texts]

    def embed_query(self, text):
        return self._embed(text)

    def _embed(self, t):
        v = np.zeros(8)
        for i, ch in enumerate(t.lower()[:8]):
            v[i] = ord(ch) % 7
        n = np.linalg.norm(v)
        return (v / n).tolist() if n else v.tolist()


def _docs():
    return [
        Document(page_content="I feel anxious about exams and stress"),
        Document(page_content="How to sleep better at night"),
        Document(page_content="Best pizza recipes for dinner"),
    ]


def test_vectorstore_persists_and_retrieves_relevant(tmp_path):
    embeddings = FakeEmb()
    vstore = chat.build_vectorstore(_docs(), embeddings, str(tmp_path / "idx"))
    assert (tmp_path / "idx").exists()

    # reload from disk
    vstore2 = chat.build_vectorstore([], embeddings, str(tmp_path / "idx"))
    assert len(vstore2.index_to_docstore_id) == 3

    retriever = chat.get_retriever(vstore2)
    results = retriever.invoke("I am feeling stressed about exams")
    assert results[0].page_content == "I feel anxious about exams and stress"


def test_generate_response_uses_latest_question_and_persists(settings, monkeypatch):
    class FakeChain:
        def __init__(self):
            self.calls = []

        async def ainvoke(self, inputs):
            self.calls.append(inputs)
            return {"answer": "It sounds stressful."}

    fake = FakeChain()
    monkeypatch.setattr(chat, "get_chain", lambda: fake)

    sid = db.get_or_create_session(None, "user-1")
    db.append_message(sid, "user", "I am stressed")
    db.append_message(sid, "bot", "Tell me more")

    answer = asyncio.run(chat.generate_response("I am stressed about exams", sid, "user-1"))

    assert answer == "It sounds stressful."
    # retrieval used only the latest question, history injected separately
    assert fake.calls[0]["input"] == "I am stressed about exams"
    assert "Tell me more" in fake.calls[0]["history"]

    msgs = db.get_recent_messages(sid, 10)
    assert msgs[-2:] == [
        {"role": "user", "content": "I am stressed about exams"},
        {"role": "bot", "content": "It sounds stressful."},
    ]


def test_generate_response_empty_answer_falls_back(settings, monkeypatch):
    class FakeChain:
        async def ainvoke(self, inputs):
            return {"answer": "   "}

    monkeypatch.setattr(chat, "get_chain", lambda: FakeChain())
    sid = db.get_or_create_session(None, "user-1")
    answer = asyncio.run(chat.generate_response("hello there", sid, "user-1"))
    assert answer == "I can help you with mental health-related questions. What would you like to know?"
    msgs = db.get_recent_messages(sid, 10)
    assert msgs[-1]["content"] == answer


class _FakeLLM:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


def _override_settings(settings, **overrides):
    kwargs = dict(settings.__dict__)
    kwargs.update(overrides)
    return settings.__class__(**kwargs)


def test_build_llm_ollama_default(settings, monkeypatch):
    import sys

    sys.modules["langchain_ollama"] = type(sys)("langchain_ollama")
    sys.modules["langchain_ollama"].ChatOllama = _FakeLLM

    s = _override_settings(
        settings,
        llm_provider="ollama",
        ollama_model="qwen2.5-coder:1.5b",
        ollama_base_url="http://localhost:11434",
    )
    monkeypatch.setattr(chat.config, "get_settings", lambda: s)

    llm = chat.build_llm()
    assert isinstance(llm, _FakeLLM)
    assert llm.kwargs["model"] == "qwen2.5-coder:1.5b"
    assert llm.kwargs["base_url"] == "http://localhost:11434"
    assert "num_predict" in llm.kwargs
    assert "max_tokens" not in llm.kwargs


def test_build_llm_groq(settings, monkeypatch):
    import sys

    sys.modules["langchain_groq"] = type(sys)("langchain_groq")
    sys.modules["langchain_groq"].ChatGroq = _FakeLLM

    s = _override_settings(
        settings,
        llm_provider="groq",
        groq_api_key="gsk-test",
        llm_model="mixtral-8x7b-32768",
    )
    monkeypatch.setattr(chat.config, "get_settings", lambda: s)

    llm = chat.build_llm()
    assert isinstance(llm, _FakeLLM)
    assert llm.kwargs["groq_api_key"] == "gsk-test"
    assert llm.kwargs["model_name"] == "mixtral-8x7b-32768"
    assert "max_tokens" in llm.kwargs
    assert "num_predict" not in llm.kwargs