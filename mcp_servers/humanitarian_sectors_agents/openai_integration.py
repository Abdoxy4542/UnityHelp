"""
OpenAI Integration Layer for Sudan Humanitarian Data Collection
Handles text, voice, and image processing using OpenAI models
with specific support for Arabic Sudan dialect
"""

import os
import json
import base64
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
import logging

try:
    from openai import OpenAI
    from openai import AsyncOpenAI
except ImportError:
    print("OpenAI package not installed. Run: pip install openai")
    OpenAI = None
    AsyncOpenAI = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessingTier(Enum):
    """Processing tiers for cost optimization"""
    EMERGENCY = "emergency"      # GPT-4o for critical situations
    STANDARD = "standard"        # GPT-4 Turbo for regular operations
    BULK = "bulk"               # GPT-3.5 Turbo for large-scale processing

class DataType(Enum):
    """Types of data inputs from field"""
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    MULTIMODAL = "multimodal"

class SudanHumanitarianOpenAI:
    """Main class for OpenAI integration with Sudan humanitarian context"""

    def __init__(self, api_key: str = None):
        """Initialize OpenAI client with API key"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        if OpenAI is None:
            raise ImportError("OpenAI package not installed. Run: pip install openai")

        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)

        # Model configuration for different processing tiers
        self.models = {
            ProcessingTier.EMERGENCY: "gpt-4o",
            ProcessingTier.STANDARD: "gpt-4-turbo-preview",
            ProcessingTier.BULK: "gpt-3.5-turbo"
        }

        # Sudan-specific context and terminology
        self.sudan_context = {
            "locations": ["Nyala", "El Geneina", "Kassala", "Khartoum", "Port Sudan", "Zalingei", "Geneina"],
            "arabic_terms": {
                "نازح": "displaced person/IDP",
                "لاجئ": "refugee",
                "مخيم": "camp",
                "مياه": "water",
                "غذاء": "food",
                "صحة": "health",
                "حماية": "protection",
                "تعليم": "education",
                "مأوى": "shelter",
                "أمان": "safety",
                "عنف": "violence",
                "احتياجات": "needs",
                "خدمات": "services",
                "طوارئ": "emergency",
                "أزمة": "crisis"
            },
            "local_phrases": {
                "الوضع صعب جداً": "The situation is very difficult",
                "نحتاج مساعدة عاجلة": "We need urgent help",
                "المياه مقطوعة": "Water is cut off",
                "الأطفال جوعانين": "The children are hungry",
                "مافي أمان": "There is no safety"
            }
        }

        # System prompts for different contexts
        self.system_prompts = self._create_system_prompts()

    def _create_system_prompts(self) -> Dict[str, str]:
        """Create specialized system prompts for different humanitarian contexts"""
        return {
            "assessment_processing": f"""
You are an AI assistant specialized in processing humanitarian assessment data from Sudan.
You understand Arabic Sudan dialect and can interpret informal field reports.

Context:
- Current crisis: 25.6 million people need humanitarian assistance
- 6.2 million internally displaced persons
- Priority locations: {', '.join(self.sudan_context['locations'])}
- You understand both formal Arabic and Sudan dialect expressions

Your role:
1. Process text, voice transcripts, and image descriptions from field teams
2. Extract key humanitarian indicators and urgent needs
3. Identify protection concerns, health emergencies, and service gaps
4. Generate structured data for assessment systems
5. Flag critical situations requiring immediate attention

Always maintain sensitivity to the humanitarian context and dignity of affected populations.
""",

            "crisis_detection": """
You are a crisis detection specialist for Sudan humanitarian operations.
Your role is to identify emergency situations requiring immediate response.

Crisis Indicators to Watch For:
- Disease outbreaks (cholera, measles, etc.)
- Mass population movements
- Protection incidents (GBV, violence)
- Critical service disruptions
- Food security emergencies
- Conflict escalation

When processing data:
1. Assess severity level (CRITICAL, HIGH, MEDIUM, LOW)
2. Estimate population affected
3. Identify required response sectors
4. Recommend immediate actions
5. Generate alert notifications

Respond in both English and Arabic when communicating with field teams.
""",

            "multimodal_analysis": """
You are analyzing multimodal humanitarian data (text, audio transcripts, images) from Sudan.

For each input type:
- Text: Extract facts, concerns, requests for assistance
- Audio transcripts: Focus on emotional context and urgency indicators
- Images: Describe conditions, damage, population density, infrastructure status

Integration approach:
1. Combine insights from all modalities
2. Cross-validate information across sources
3. Identify discrepancies or confirmation patterns
4. Generate comprehensive situational awareness
5. Prioritize findings by urgency and impact

Maintain cultural sensitivity and respect for affected communities.
"""
        }

    async def process_text_input(self,
                                text: str,
                                context: str = "general",
                                tier: ProcessingTier = ProcessingTier.STANDARD) -> Dict[str, Any]:
        """Process Arabic/English text input from field teams"""

        try:
            # Select appropriate model and prompt
            model = self.models[tier]
            system_prompt = self.system_prompts.get("assessment_processing", "")

            # Add context-specific instructions
            if context == "emergency":
                system_prompt = self.system_prompts["crisis_detection"]
            elif context == "multimodal":
                system_prompt = self.system_prompts["multimodal_analysis"]

            response = await self.async_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"""
Process this field report from Sudan:

Text: {text}

Please provide:
1. Summary of key findings
2. Identified needs and gaps
3. Severity assessment (CRITICAL/HIGH/MEDIUM/LOW)
4. Recommended actions
5. Sectors involved
6. Population affected (estimate)
7. Location (if mentioned)
8. Any Arabic terms translated

Format as structured JSON.
"""}
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=1500
            )

            result = {
                "input_type": "text",
                "processing_tier": tier.value,
                "timestamp": datetime.now().isoformat(),
                "model_used": model,
                "response": response.choices[0].message.content,
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

            # Try to parse as JSON if possible
            try:
                parsed_response = json.loads(response.choices[0].message.content)
                result["structured_data"] = parsed_response
            except json.JSONDecodeError:
                result["structured_data"] = None

            return result

        except Exception as e:
            logger.error(f"Error processing text input: {e}")
            return {
                "error": str(e),
                "input_type": "text",
                "timestamp": datetime.now().isoformat()
            }

    async def process_voice_input(self,
                                 audio_file_path: str,
                                 language: str = "ar",
                                 context: str = "general") -> Dict[str, Any]:
        """Process voice input using Whisper API"""

        try:
            # Transcribe audio using Whisper
            with open(audio_file_path, "rb") as audio_file:
                transcript = await self.async_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,  # Arabic
                    prompt="This is a humanitarian field report from Sudan. May contain Arabic dialect and humanitarian terminology."
                )

            # Process the transcript text
            text_analysis = await self.process_text_input(
                text=transcript.text,
                context=context,
                tier=ProcessingTier.STANDARD
            )

            result = {
                "input_type": "voice",
                "audio_file": audio_file_path,
                "language": language,
                "transcript": transcript.text,
                "timestamp": datetime.now().isoformat(),
                "text_analysis": text_analysis
            }

            return result

        except Exception as e:
            logger.error(f"Error processing voice input: {e}")
            return {
                "error": str(e),
                "input_type": "voice",
                "timestamp": datetime.now().isoformat()
            }

    async def process_image_input(self,
                                 image_path: str,
                                 context: str = "assessment",
                                 additional_prompt: str = "") -> Dict[str, Any]:
        """Process image input using GPT-4 Vision"""

        try:
            # Encode image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            # Prepare image analysis prompt
            image_prompt = f"""
Analyze this image from a humanitarian assessment in Sudan.

Context: {context}
{additional_prompt}

Please provide:
1. Description of what you see
2. Humanitarian indicators visible
3. Infrastructure condition assessment
4. Population density estimation (if people visible)
5. Immediate needs identified
6. Safety/security concerns
7. Recommended follow-up actions

Focus on humanitarian assessment criteria and provide actionable insights.
"""

            response = await self.async_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "system", "content": self.system_prompts["multimodal_analysis"]},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": image_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1200
            )

            result = {
                "input_type": "image",
                "image_path": image_path,
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "analysis": response.choices[0].message.content,
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

            return result

        except Exception as e:
            logger.error(f"Error processing image input: {e}")
            return {
                "error": str(e),
                "input_type": "image",
                "timestamp": datetime.now().isoformat()
            }

    async def process_multimodal_input(self,
                                      inputs: List[Dict[str, Any]],
                                      context: str = "assessment") -> Dict[str, Any]:
        """Process multiple input types and provide integrated analysis"""

        try:
            results = []

            # Process each input type
            for input_item in inputs:
                if input_item["type"] == "text":
                    result = await self.process_text_input(
                        text=input_item["data"],
                        context=context,
                        tier=input_item.get("tier", ProcessingTier.STANDARD)
                    )
                elif input_item["type"] == "voice":
                    result = await self.process_voice_input(
                        audio_file_path=input_item["data"],
                        context=context
                    )
                elif input_item["type"] == "image":
                    result = await self.process_image_input(
                        image_path=input_item["data"],
                        context=context,
                        additional_prompt=input_item.get("prompt", "")
                    )

                results.append(result)

            # Integrate all results
            integration_prompt = f"""
You have received humanitarian assessment data from multiple sources in Sudan.
Context: {context}

Data Sources:
{json.dumps([r.get("structured_data", r.get("analysis", r.get("response", ""))) for r in results], indent=2)}

Please provide an integrated analysis:
1. Consolidated situation overview
2. Cross-validated findings
3. Priority needs identified across all sources
4. Confidence level of assessments
5. Recommended immediate actions
6. Sectors requiring coordination
7. Overall severity assessment

Provide response in structured JSON format.
"""

            integration_response = await self.async_client.chat.completions.create(
                model=self.models[ProcessingTier.EMERGENCY],  # Use best model for integration
                messages=[
                    {"role": "system", "content": self.system_prompts["multimodal_analysis"]},
                    {"role": "user", "content": integration_prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )

            integrated_result = {
                "input_type": "multimodal",
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "individual_results": results,
                "integrated_analysis": integration_response.choices[0].message.content,
                "total_inputs": len(inputs)
            }

            return integrated_result

        except Exception as e:
            logger.error(f"Error processing multimodal input: {e}")
            return {
                "error": str(e),
                "input_type": "multimodal",
                "timestamp": datetime.now().isoformat()
            }

    def estimate_costs(self, usage_stats: Dict[str, int]) -> Dict[str, float]:
        """Estimate API costs based on usage statistics"""

        # Approximate pricing (as of Jan 2024, subject to change)
        pricing = {
            "gpt-4o": {"input": 0.005, "output": 0.015},  # per 1K tokens
            "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            "whisper-1": 0.006,  # per minute
            "gpt-4-vision-preview": {"input": 0.01, "output": 0.03}
        }

        cost_breakdown = {}
        total_cost = 0

        for model, usage in usage_stats.items():
            if model == "whisper-1":
                cost = usage.get("minutes", 0) * pricing[model]
            else:
                input_cost = (usage.get("input_tokens", 0) / 1000) * pricing[model]["input"]
                output_cost = (usage.get("output_tokens", 0) / 1000) * pricing[model]["output"]
                cost = input_cost + output_cost

            cost_breakdown[model] = cost
            total_cost += cost

        return {
            "breakdown": cost_breakdown,
            "total_estimated_cost": total_cost,
            "currency": "USD"
        }

    def get_arabic_translation(self, text: str) -> str:
        """Translate English humanitarian terms to Arabic"""

        for arabic, english in self.sudan_context["arabic_terms"].items():
            if english.lower() in text.lower():
                text = text.replace(english, f"{english} ({arabic})")

        return text


# Usage example and testing
async def test_openai_integration():
    """Test the OpenAI integration with sample data"""

    # Initialize the integration (requires OPENAI_API_KEY env variable)
    try:
        openai_integration = SudanHumanitarianOpenAI()

        # Test text processing
        print("Testing text processing...")
        sample_text = "الوضع في مخيم النيالة صعب جداً. نحتاج مياه وغذاء. الأطفال مرضى والمياه مقطوعة منذ أسبوع."

        result = await openai_integration.process_text_input(
            text=sample_text,
            context="emergency",
            tier=ProcessingTier.STANDARD
        )

        print("Text processing result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        return result

    except Exception as e:
        print(f"Test failed: {e}")
        return None

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_openai_integration())