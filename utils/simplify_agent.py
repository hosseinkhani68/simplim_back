from typing import List, Dict, Any
import autogen
from utils.vector_store import VectorStore
import os
from dotenv import load_dotenv
from openai import OpenAI

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
        
        # Configure Autogen
        config_list = [
            {
                "model": "gpt-4",
                "api_key": api_key,
                "base_url": "https://api.openai.com/v1"
            }
        ]
        
        # Create assistant agent
        self.assistant = autogen.AssistantAgent(
            name="simplify_assistant",
            llm_config={
                "config_list": config_list,
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
        
        # Create user proxy agent
        self.user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=5,
            code_execution_config=False,
        )

    async def simplify_text(self, text: str, user_id: int, 
                          previous_context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Simplify text using Autogen with context from vector store.
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
            
            # Start the conversation
            chat_result = await self.user_proxy.initiate_chat(
                self.assistant,
                message=message
            )
            
            # Get the simplified text from the last message
            simplified_text = chat_result.last_message()["content"]
            
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
                "point_id": point_id
            }
            
        except Exception as e:
            raise Exception(f"Error in text simplification: {str(e)}")

    async def handle_follow_up(self, text: str, user_id: int, 
                             previous_point_id: int) -> Dict[str, Any]:
        """
        Handle follow-up questions or requests for further simplification.
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
            
            # Start the conversation
            chat_result = await self.user_proxy.initiate_chat(
                self.assistant,
                message=context
            )
            
            # Get the new simplified text
            new_simplified_text = chat_result.last_message()["content"]
            
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
                "point_id": point_id
            }
            
        except Exception as e:
            raise Exception(f"Error handling follow-up: {str(e)}") 