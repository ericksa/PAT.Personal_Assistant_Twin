"""
Interview Assistant - Separate file to avoid circular imports
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
import logging

logger = logging.getLogger(__name__)

# System prompt for interview assistant
INTERVIEW_SYSTEM_PROMPT = """You are PAT (Personal Assistant Twin), an expert interview assistant helping Adam Erickson prepare for technical interviews.

Your role:
- Provide concise, professional answers to interview questions
- Make responses sound natural and conversational
- Focus on Adam's experience and skills
- Keep answers clear and easy to read aloud
- Stay factual and relevant to the question

Context Information:
{context}

Previous conversation:
{history}

Current question: {question}

Provide a clear, professional answer that Adam can read aloud naturally."""

class InterviewAssistant:
    def __init__(self, ollama_base_url="http://host.docker.internal:11434"):
        self.ollama_base_url = ollama_base_url

        # Initialize the LLM
        self.llm = ChatOllama(
            model="llama3:8b",
            base_url=ollama_base_url,
            temperature=0.7,
            num_ctx=2048
        )

        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", INTERVIEW_SYSTEM_PROMPT),
            ("human", "{question}")
        ])

        # Create the chain
        self.chain = (
            self.prompt
            | self.llm
            | StrOutputParser()
        )

        # Simple conversation history storage
        self.conversation_history = []

    async def generate_response(self, question: str, context: str = "") -> str:
        """Generate an interview response using LangChain"""
        try:
            # Prepare inputs
            inputs = {
                "question": question,
                "context": context,
                "history": self._get_conversation_history()
            }

            # Generate response
            response = await self.chain.ainvoke(inputs)

            # Store in history
            self.conversation_history.append({
                "question": question,
                "response": response
            })

            # Keep only the last few exchanges
            if len(self.conversation_history) > 4:
                self.conversation_history = self.conversation_history[-4:]

            return response

        except Exception as e:
            logger.error(f"Error generating response with LangChain: {e}")
            return f"Error generating response: {str(e)}"

    def _get_conversation_history(self) -> str:
        """Get formatted conversation history"""
        try:
            if not self.conversation_history:
                return "No previous conversation."

            history_lines = []
            for item in self.conversation_history[-2:]:  # Last 2 exchanges
                history_lines.append(f"Human: {item['question']}")
                history_lines.append(f"Assistant: {item['response']}")

            return "\n".join(history_lines)
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return "No previous conversation."