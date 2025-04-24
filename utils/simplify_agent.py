from typing import List, Dict, Any
import autogen
from utils.vector_store import VectorStore
import os
from dotenv import load_dotenv
from openai import OpenAI
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from fastapi import HTTPException
import re

# Load environment variables
load_dotenv()

class SimplifyAgent:
    def __init__(self):
        # Initialize vector store
        self.vector_store = VectorStore()
        
        # Get OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        
        # Configure Autogen with retry settings
        self.config_list = [
            {
                "model": "gpt-4",
                "api_key": api_key,
                "base_url": "https://api.openai.com/v1",
                "request_timeout": 600,  # 10 minutes timeout
                "max_retries": 3,  # Maximum number of retries
                "retry_min_seconds": 1,  # Minimum wait time between retries
                "retry_max_seconds": 10,  # Maximum wait time between retries
            }
        ]
        
        # Create assistant agent
        self.assistant = autogen.AssistantAgent(
            name="simplify_assistant",
            llm_config={
                "config_list": self.config_list,
                "temperature": 0.7,
            },
            system_message="""You are a text simplification expert. Your goal is to explain complex concepts in simple terms.
            You should:
            1. Break down complex ideas into smaller, understandable parts
            2. Use analogies and examples
            3. Avoid technical jargon
            4. Adjust your explanation based on user feedback
            5. Reference previous explanations when relevant
            """
        )
        
        # Create user proxy agent with increased timeout
        self.user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=5,
            code_execution_config=False,
            request_timeout=600,  # 10 minutes timeout
        )

    def _fallback_simplification(self, text: str) -> str:
        """
        Fallback method when OpenAI API is unavailable.
        Uses a simple rule-based approach to simplify text.
        """
        # Basic simplification rules
        rules = [
            (r'\b(?:is|are|was|were)\b', 'is'),
            (r'\b(?:very|extremely|really)\b', ''),
            (r'\b(?:therefore|thus|hence)\b', 'so'),
            (r'\b(?:however|nevertheless|nonetheless)\b', 'but'),
            (r'\b(?:utilize|utilization)\b', 'use'),
            (r'\b(?:commence|initiate)\b', 'start'),
            (r'\b(?:terminate|cease)\b', 'stop'),
            (r'\b(?:approximately|roughly)\b', 'about'),
            (r'\b(?:subsequently|afterward)\b', 'then'),
            (r'\b(?:prior to|beforehand)\b', 'before'),
        ]
        
        simplified = text
        for pattern, replacement in rules:
            simplified = re.sub(pattern, replacement, simplified, flags=re.IGNORECASE)
        
        return simplified

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def simplify_text(self, text: str, user_id: int, 
                          previous_context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Simplify text using Autogen with context from vector store.
        Falls back to rule-based simplification if OpenAI API is unavailable.
        """
        try:
            # Find similar previous simplifications
            similar_simplifications = self.vector_store.find_similar_simplifications(
                text, user_id
            )
            
            # Prepare context for the agent
            context = ""
            if similar_simplifications:
                context = "Previous similar explanations:\n"
                for sim in similar_simplifications:
                    context += f"Original: {sim['original_text']}\n"
                    context += f"Simplified: {sim['simplified_text']}\n\n"
            
            # Prepare the message for the agent
            message = f"""
            {context}
            Please simplify this text for better understanding:
            {text}
            
            Provide a simplified version that:
            1. Maintains the core meaning
            2. Uses simpler language
            3. Includes examples if helpful
            4. Is appropriate for a general audience
            """
            
            # Start the conversation with retry logic
            try:
                chat_result = await self.user_proxy.initiate_chat(
                    self.assistant,
                    message=message
                )
                simplified_text = chat_result.last_message()["content"]
            except Exception as e:
                if "service unavailable" in str(e).lower():
                    # Use fallback simplification
                    simplified_text = self._fallback_simplification(text)
                else:
                    raise
            
            # Store the simplification in vector database
            point_id = self.vector_store.store_simplification(
                original_text=text,
                simplified_text=simplified_text,
                complexity_level=1,  # Can be adjusted based on feedback
                user_id=user_id
            )
            
            return {
                "original_text": text,
                "simplified_text": simplified_text,
                "point_id": point_id,
                "used_fallback": "service unavailable" in str(e).lower() if 'e' in locals() else False
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Service temporarily unavailable. Please try again later. Error: {str(e)}"
            )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def handle_follow_up(self, text: str, user_id: int, 
                             previous_point_id: int) -> Dict[str, Any]:
        """
        Handle follow-up questions or requests for further simplification.
        Falls back to rule-based simplification if OpenAI API is unavailable.
        """
        try:
            # Get the previous simplification
            previous_simplification = self.vector_store.get_simplification_history(
                user_id, limit=1
            )[0]
            
            # Prepare context for the agent
            context = f"""
            Previous explanation:
            Original: {previous_simplification['original_text']}
            Simplified: {previous_simplification['simplified_text']}
            
            User feedback: {text}
            """
            
            # Start the conversation with retry logic
            try:
                chat_result = await self.user_proxy.initiate_chat(
                    self.assistant,
                    message=context
                )
                new_simplified_text = chat_result.last_message()["content"]
            except Exception as e:
                if "service unavailable" in str(e).lower():
                    # Use fallback simplification
                    new_simplified_text = self._fallback_simplification(previous_simplification['original_text'])
                else:
                    raise
            
            # Store the new simplification
            point_id = self.vector_store.store_simplification(
                original_text=previous_simplification['original_text'],
                simplified_text=new_simplified_text,
                complexity_level=previous_simplification['complexity_level'] + 1,
                user_id=user_id
            )
            
            return {
                "original_text": previous_simplification['original_text'],
                "simplified_text": new_simplified_text,
                "point_id": point_id,
                "used_fallback": "service unavailable" in str(e).lower() if 'e' in locals() else False
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Service temporarily unavailable. Please try again later. Error: {str(e)}"
            ) 