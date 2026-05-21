"""SenseiCerebellum - VRM Motion & Reflex Processing Core.

Implements the cerebellum subsystem for analyzing conversational text inputs
and translating them into mathematical state vectors for 3D VRM avatar animation.

Uses the locally-loaded Qwen2.5-1.5B-Instruct model to generate strictly-formatted
JSON output (emotion classification + body_state parameters) for downstream
animation controllers. No external APIs; zero conversational text in responses.
"""

import json
import re
import torch
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langgraph.graph import StateGraph, START, END

from llm_core.utils.logger import get_logger
from llm_core.utils.config_manager import ConfigLoader
from llm_core.agents.state_definitions import AgentState


logger = get_logger(__name__)


@dataclass
class BodyState:
    """Procedural animation parameters for VRM avatar motion.
    
    All parameters are normalized floats within strict ranges per brain/1.5B/rules.md.
    
    Attributes:
        forward_lean: Pitch rotation of spine/chest (0.00-0.25)
        sway_amplitude: Lateral movement magnitude (0.00-0.08)
        sway_frequency: Sway speed in Hertz (0.50-2.00)
        shoulder_tension: Shoulder elevation (0.00-0.30)
    """
    forward_lean: float
    sway_amplitude: float
    sway_frequency: float
    shoulder_tension: float

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for JSON serialization."""
        return {
            "forward_lean": round(self.forward_lean, 2),
            "sway_amplitude": round(self.sway_amplitude, 2),
            "sway_frequency": round(self.sway_frequency, 2),
            "shoulder_tension": round(self.shoulder_tension, 2)
        }

    @staticmethod
    def clamp_values(body_state_dict: Dict[str, float]) -> "BodyState":
        """Enforce strict range constraints per rules.md.
        
        Args:
            body_state_dict: Dictionary with float values (may exceed ranges)
        
        Returns:
            BodyState with all values clamped to valid ranges
        """
        return BodyState(
            forward_lean=max(0.00, min(0.25, body_state_dict.get("forward_lean", 0.0))),
            sway_amplitude=max(0.00, min(0.08, body_state_dict.get("sway_amplitude", 0.0))),
            sway_frequency=max(0.50, min(2.00, body_state_dict.get("sway_frequency", 0.75))),
            shoulder_tension=max(0.00, min(0.30, body_state_dict.get("shoulder_tension", 0.0)))
        )


@dataclass
class MotionResponse:
    """Strict JSON response structure for VRM animation controller.
    
    Attributes:
        emotion: One of: neutral, happy, sad, angry, surprised, relaxed
        body_state: BodyState object with animation parameters
    """
    emotion: str
    body_state: BodyState

    def to_json_string(self) -> str:
        """Convert to minified JSON string (no markdown, no whitespace).
        
        Returns:
            Compact JSON: {"emotion":"...","body_state":{...}}
        """
        data = {
            "emotion": self.emotion,
            "body_state": self.body_state.to_dict()
        }
        return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


class SenseiCerebellum:
    """VRM Avatar Motion & Reflex Processing Engine.
    
    Analyzes conversational text inputs and translates emotional/contextual
    undertones into mathematical state vectors for procedural animation.
    
    Uses Qwen2.5-1.5B-Instruct locally to generate strictly-formatted JSON
    output with emotion classification and body animation parameters.
    
    Attributes:
        model_name: Identifier for the loaded model
        tokenizer: Hugging Face tokenizer instance
        model: Hugging Face model instance  
        pipeline: Transformers inference pipeline
        max_tokens: Maximum output token count
        temperature: Sampling temperature (0.0 - 2.0)
        top_p: Nucleus sampling parameter
        graph: Compiled LangGraph execution graph
        valid_emotions: Set of allowed emotion values
    """

    VALID_EMOTIONS = {"neutral", "happy", "sad", "angry", "surprised", "relaxed"}

    def __init__(
        self,
        config_path: str = "config.yaml",
        model_name: str = "Qwen2.5-1.5B-Instruct",
        device: Optional[str] = None,
        max_tokens: int = 256,
        temperature: float = 0.5,
        top_p: float = 0.95
    ) -> None:
        """Initialize the cerebellum with local model and configuration.
        
        Args:
            config_path: Path to config.yaml for model directory resolution
            model_name: Model identifier in models/ directory
            device: Device to load model on ('cuda', 'cpu'). Auto-detects if None.
            max_tokens: Maximum output token count (1-512, reduced for JSON)
            temperature: Sampling temperature (0.0-2.0, lower for deterministic output)
            top_p: Nucleus sampling threshold (0.0-1.0)
        
        Raises:
            FileNotFoundError: If model weights not found in models/
            ValueError: If invalid parameters provided
            RuntimeError: If model loading fails
        
        Example:
            cerebellum = SenseiCerebellum(
                config_path="config.yaml",
                max_tokens=256,
                temperature=0.5
            )
        """
        logger.info("Initializing SenseiCerebellum | Model: %s", model_name)
        
        # Validate parameters
        if not 1 <= max_tokens <= 512:
            raise ValueError(f"max_tokens must be 1-512 for JSON output, got {max_tokens}")
        if not 0.0 <= temperature <= 2.0:
            raise ValueError(f"temperature must be 0.0-2.0, got {temperature}")
        if not 0.0 <= top_p <= 1.0:
            raise ValueError(f"top_p must be 0.0-1.0, got {top_p}")
        
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        
        # Resolve device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        logger.info("Device: %s", self.device)
        
        # Load configuration and resolve model path
        config_loader = ConfigLoader(config_path)
        model_base_dir = Path(config_loader.get_data_directory()) / model_name
        
        if not model_base_dir.exists():
            logger.error("Model directory not found: %s", model_base_dir)
            raise FileNotFoundError(f"Model not found at {model_base_dir}")
        
        logger.info("Loading tokenizer from %s", model_base_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(model_base_dir),
            trust_remote_code=True,
            local_files_only=True
        )
        
        logger.info("Loading model from %s", model_base_dir)
        self.model = AutoModelForCausalLM.from_pretrained(
            str(model_base_dir),
            trust_remote_code=True,
            local_files_only=True,
            device_map=self.device,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        self.model.eval()
        
        # Create inference pipeline
        self.pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if self.device == "cuda" else -1
        )
        
        logger.info("Model loaded | Device: %s | Parameters: max_tokens=%d, temp=%.2f, top_p=%.2f",
                    self.device, self.max_tokens, self.temperature, self.top_p)
        
        # Build the execution graph
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        """Define and compile the LangGraph execution pipeline.
        
        Creates a simple state machine: START → motion_node → END
        
        Returns:
            Compiled StateGraph for execution
        """
        logger.debug("Building LangGraph execution pipeline")
        
        graph = StateGraph(AgentState)
        graph.add_node("motion", self._motion_node)
        graph.add_edge(START, "motion")
        graph.add_edge("motion", END)
        
        compiled_graph = graph.compile()
        logger.debug("LangGraph compiled successfully")
        
        return compiled_graph

    def _motion_node(self, state: AgentState) -> Dict[str, Any]:
        """Core motion analysis node that processes user input through the model.
        
        This node:
        1. Extracts the latest user message from state
        2. Formats the prompt with motion analysis instructions
        3. Runs inference with strict JSON output enforcement
        4. Parses and validates the JSON response
        5. Returns updated state with JSON result
        
        Args:
            state: AgentState containing message history
        
        Returns:
            Updated state dict with parsed motion response
        """
        try:
            logger.debug("Motion node invoked | Messages: %d", len(state["messages"]))
            
            # Extract latest user message
            messages = state["messages"]
            if not messages:
                logger.warning("Empty message history in motion_node")
                return self._error_response(state, "No input messages")
            
            user_text = messages[-1].content
            
            # Format prompt for motion analysis (strict JSON output enforcer)
            formatted_prompt = self._format_motion_prompt(user_text)
            
            logger.debug("Running inference | Input length: %d chars", len(user_text))
            
            # Execute model inference
            outputs = self.pipeline(
                formatted_prompt,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True,
                num_return_sequences=1
            )
            
            # Extract and clean generated text
            response_text = outputs[0]["generated_text"]
            json_output = response_text[len(formatted_prompt):].strip()
            
            # Parse JSON (with fallback on parse error)
            try:
                motion_data = json.loads(json_output)
                logger.debug("JSON parsed successfully | emotion: %s", 
                           motion_data.get("emotion", "unknown"))
            except json.JSONDecodeError as e:
                logger.warning("JSON parse error, attempting regex extraction: %s", str(e))
                motion_data = self._extract_json_from_malformed(json_output)
            
            # Validate emotion and clamp body_state ranges
            motion_response = self._validate_motion_response(motion_data)
            json_result = motion_response.to_json_string()
            
            logger.info("Motion analysis successful | JSON: %s", json_result[:100])
            
            # Store result in state (avoid LangGraph message append issues)
            state["_motion_result"] = json_result
            return state
            
        except torch.cuda.OutOfMemoryError as e:
            logger.error("CUDA out of memory: %s", str(e))
            return self._error_response(state, "memory_exceeded")
        except RuntimeError as e:
            logger.error("Runtime error: %s", str(e))
            return self._error_response(state, "inference_failed")
        except Exception as e:
            logger.error("Unexpected error in motion_node: %s", str(e), exc_info=True)
            return self._error_response(state, "processing_error")

    def _format_motion_prompt(self, user_input: str) -> str:
        """Format prompt for motion analysis with strict JSON-only output enforcement.
        
        Provides explicit instructions to prevent markdown, explanations, or filler.
        Uses Qwen's standard chat template.
        
        Args:
            user_input: User's conversational query
        
        Returns:
            Formatted prompt string ready for tokenization
        """
        system_instruction = (
            "You function as the Cerebellum (Motion & Reflex Processing Unit) for a 3D VRM avatar. "
            "Analyze the user's conversational text and translate psychological, emotional, and contextual undertones "
            "into mathematical state vectors.\n\n"
            "CRITICAL OUTPUT CONSTRAINT:\n"
            "- Output ONLY minified JSON with two keys: \"emotion\" and \"body_state\"\n"
            "- NO markdown code blocks (no ```json ... ```)\n"
            "- NO conversational text, explanations, or filler\n"
            "- Emotion MUST be one of: neutral, happy, sad, angry, surprised, relaxed\n"
            "- body_state MUST contain: forward_lean (0.00-0.25), sway_amplitude (0.00-0.08), "
            "sway_frequency (0.50-2.00), shoulder_tension (0.00-0.30)\n"
            "- Output raw JSON only: {\"emotion\":\"...\",\"body_state\":{...}}\n"
        )
        
        # Qwen standard chat template
        formatted = (
            f"<|im_start|>system\n{system_instruction}<|im_end|>\n"
            f"<|im_start|>user\n{user_input}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        return formatted

    def _extract_json_from_malformed(self, text: str) -> Dict[str, Any]:
        """Attempt to extract valid JSON from malformed or markdown-wrapped output.
        
        Handles cases where model outputs: ```json {...} ``` or conversational prefix.
        
        Args:
            text: Raw model output that may contain extra text
        
        Returns:
            Dictionary with extracted JSON or fallback structure
        """
        # Remove markdown code blocks
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*$", "", text)
        
        # Try to find JSON object
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        logger.warning("Could not extract valid JSON from: %s", text[:200])
        return self._default_motion_data()

    def _validate_motion_response(self, data: Dict[str, Any]) -> MotionResponse:
        """Validate emotion and clamp body_state parameters to valid ranges.
        
        Args:
            data: Parsed JSON dictionary from model
        
        Returns:
            MotionResponse with validated emotion and clamped body_state
        """
        emotion = str(data.get("emotion", "neutral")).lower().strip()
        if emotion not in self.VALID_EMOTIONS:
            logger.warning("Invalid emotion '%s', defaulting to neutral", emotion)
            emotion = "neutral"
        
        body_state_dict = data.get("body_state", {})
        if not isinstance(body_state_dict, dict):
            logger.warning("body_state is not a dict, using defaults")
            body_state_dict = {}
        
        body_state = BodyState.clamp_values(body_state_dict)
        
        return MotionResponse(emotion=emotion, body_state=body_state)

    def generate_response(self, user_query: str) -> str:
        """Generate strict JSON motion response from user input.
        
        Public API method that:
        1. Validates input string
        2. Initializes AgentState from query
        3. Executes the compiled graph
        4. Returns minified JSON string (no markdown)
        
        Args:
            user_query: User's conversational query string
        
        Returns:
            Minified JSON string: {"emotion":"...","body_state":{...}}
            Returns fallback JSON if any error occurs
        
        Raises:
            ValueError: If user_query is empty or not a string
        
        Example:
            json_response = cerebellum.generate_response("本当に感謝しています！")
            print(json_response)  # {"emotion":"happy","body_state":{...}}
        """
        if not isinstance(user_query, str):
            logger.error("user_query must be str, got %s", type(user_query).__name__)
            raise ValueError(f"user_query must be str, got {type(user_query).__name__}")
        
        user_query = user_query.strip()
        if not user_query:
            logger.warning("Empty user_query provided")
            return self._fallback_motion_json("neutral")
        
        logger.info("generate_response | Input length: %d chars", len(user_query))
        
        try:
            # Initialize state with user query
            from langchain_core.messages import HumanMessage
            initial_state: AgentState = {
                "messages": [HumanMessage(content=user_query)],
                "display_lang": "en",
                "retrieved_documents": None,
                "reasoning_step": 0,
                "tool_used": None
            }
            
            # Execute graph
            final_state = self.graph.invoke(initial_state)
            
            # Extract motion result stored in state
            if "_motion_result" in final_state:
                json_result = final_state["_motion_result"]
                logger.info("Response generated successfully | Length: %d chars", len(json_result))
                return json_result
            
            logger.warning("No motion result in final state")
            return self._fallback_motion_json("neutral")
            
        except Exception as e:
            logger.error("Error in generate_response: %s", str(e), exc_info=True)
            return self._fallback_motion_json("neutral")

    def _error_response(self, state: AgentState, error_type: str) -> Dict[str, Any]:
        """Format error response that maintains JSON structure for downstream consumers.
        
        Appends fallback motion data to state without crashing the pipeline.
        
        Args:
            state: Current AgentState
            error_type: Error classification (memory_exceeded, inference_failed, etc.)
        
        Returns:
            Updated state with fallback motion result
        """
        fallback_emotion = "neutral"
        if "memory" in error_type.lower():
            fallback_emotion = "relaxed"
        
        json_result = self._fallback_motion_json(fallback_emotion)
        state["_motion_result"] = json_result
        
        logger.warning("Error response appended | Type: %s | Emotion: %s", error_type, fallback_emotion)
        return state

    def _fallback_motion_json(self, emotion: str = "neutral") -> str:
        """Generate fallback JSON response with safe default values.
        
        Args:
            emotion: Emotion to use in fallback (must be valid)
        
        Returns:
            Minified JSON string with default body_state values
        """
        if emotion not in self.VALID_EMOTIONS:
            emotion = "neutral"
        
        fallback_response = MotionResponse(
            emotion=emotion,
            body_state=BodyState(
                forward_lean=0.05,
                sway_amplitude=0.02,
                sway_frequency=0.75,
                shoulder_tension=0.05
            )
        )
        
        json_result = fallback_response.to_json_string()
        logger.debug("Fallback motion JSON generated | Emotion: %s", emotion)
        return json_result

    def _default_motion_data(self) -> Dict[str, Any]:
        """Return default motion data structure for JSON parsing failures.
        
        Returns:
            Dictionary with neutral emotion and baseline body_state
        """
        return {
            "emotion": "neutral",
            "body_state": {
                "forward_lean": 0.05,
                "sway_amplitude": 0.02,
                "sway_frequency": 0.75,
                "shoulder_tension": 0.05
            }
        }
