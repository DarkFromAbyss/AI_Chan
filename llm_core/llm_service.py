import logging
from llm_core.schemas import MessageInputSchema, ModelResponseSchema
from llm_core.semantic_cache import SenseiSemanticCache


class SenseiAgent:
    """Encapsulate the LangChain/LangGraph orchestration and semantic cache."""

    def __init__(self, model_path: str = "models/qwen2.5-7b-instruct.gguf") -> None:
        self.model_path = model_path
        self.logger = logging.getLogger(__name__)
        self.logger.info("Creating SenseiAgent with model_path=%s", self.model_path)
        self.semantic_cache = SenseiSemanticCache()

    def generate_response(self, message_input: MessageInputSchema) -> ModelResponseSchema:
        """Generate a response from the AI core using validated Pydantic input."""
        self.logger.info("Generating response for session_id=%s", message_input.session_id)
        retrieval_sources = self.semantic_cache.search(message_input.user_text)

        assistant_text = (
            "This placeholder response preserves the backend/LLM contract while "
            "the LangChain/LangGraph implementation is developed."
        )

        return ModelResponseSchema(
            session_id=message_input.session_id,
            assistant_text=assistant_text,
            sources=retrieval_sources,
        )
