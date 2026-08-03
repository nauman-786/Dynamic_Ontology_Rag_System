from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.settings import settings
from retrieval.hybrid_retriever import HybridContext

class AnswerGenerationAgent:
    """Generates final answers using retrieved graph facts, global graph summaries, and vector passages."""

    def __init__(self):
        self.llm = ChatGroq(
            model=settings.DEFAULT_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.3,
            max_retries=5
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an advanced Ontology-aware AI Assistant.
You have complete access to the global graph structure and specific retrieved document context.

=== GLOBAL KNOWLEDGE GRAPH OVERVIEW ===
{graph_summary}

=== RECENT CONVERSATION HISTORY (Last 5 Messages) ===
{history}

=== RETRIEVED LOCAL CONTEXT CHUNKS ===
{context}

Rules — follow these exactly:
1. Never quote, repeat, paraphrase-with-headers, or otherwise reproduce the context blocks themselves. They are internal reference material.
2. Do not mention "KNOWLEDGE GRAPH FACTS", "DOCUMENT TEXT PASSAGES", "GLOBAL KNOWLEDGE GRAPH OVERVIEW", or any other internal section label in your reply.
3. Write your answer as if you already knew the information — a direct, natural response to the question.
4. Use the Global Knowledge Graph Overview to answer macro-level questions (e.g., total entities, central hubs, categories, overall graph summary).
5. Use the Retrieved Local Context Chunks for specific detailed queries.
6. Prioritize graph facts for "who / what / how are they related" questions; use document passages for nuance or when graph facts are insufficient.
7. If the user's message isn't a real question, respond conversationally and invite them to ask something based on the history.
8. If the answer truly isn't in the context or graph overview, say plainly that you don't know.
9. Keep the answer concise and in clean Markdown. DO NOT append a "Sources:" list at the end of your response under any circumstances.
"""),
            ("user", "{question}")
        ])

        self.chain = self.prompt | self.llm | StrOutputParser()

    def stream_answer(self, question: str, hybrid_context: HybridContext = None, history: list = None, graph_summary: str = ""):
        """Streams the LLM response chunk by chunk with history and graph awareness."""
        
        # 1. Safely extract and format conversation history
        formatted_history = "No previous conversation history."
        if history:
            lines = []
            for m in history:
                # Safely handle both Pydantic models and dictionaries
                role = m.role if hasattr(m, 'role') else m.get('role', '')
                content = m.content if hasattr(m, 'content') else m.get('content', '')
                speaker = "User" if role == 'user' else "Assistant"
                lines.append(f"{speaker}: {content}")
            
            if lines:
                formatted_history = "\n".join(lines)

        # 2. Extract local context, providing a fallback if none exists
        local_context = hybrid_context.formatted_context if hybrid_context and hybrid_context.formatted_context else "No specific local context found for this query."

        # 3. Stream the response from the LLM
        for chunk in self.chain.stream({
            "graph_summary": graph_summary,
            "history": formatted_history,
            "context": local_context,
            "question": question
        }):
            yield chunk