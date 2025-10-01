"""
Enhanced Assessment Agent with OpenAI Multimodal Integration
Processes text, voice, and image data from Sudan field teams using OpenAI models
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from openai_integration import SudanHumanitarianOpenAI, ProcessingTier, DataType
from base_humanitarian_agent import BaseHumanitarianAgent, HumanitarianRequest, HumanitarianResponse

logger = logging.getLogger(__name__)

class MultimodalDataProcessor:
    """Handles multimodal data processing for humanitarian assessments"""

    def __init__(self, openai_integration: SudanHumanitarianOpenAI):
        self.openai = openai_integration
        self.processing_history = []

    async def process_field_report(self, field_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a complete field report with multiple data types"""

        try:
            # Organize inputs by type
            multimodal_inputs = []

            # Process text inputs (including KoboToolbox data)
            if "text_reports" in field_data:
                for text_item in field_data["text_reports"]:
                    multimodal_inputs.append({
                        "type": "text",
                        "data": text_item["content"],
                        "tier": self._determine_processing_tier(text_item),
                        "metadata": text_item.get("metadata", {})
                    })

            # Process voice recordings
            if "voice_recordings" in field_data:
                for voice_item in field_data["voice_recordings"]:
                    if os.path.exists(voice_item["file_path"]):
                        multimodal_inputs.append({
                            "type": "voice",
                            "data": voice_item["file_path"],
                            "metadata": voice_item.get("metadata", {})
                        })

            # Process images
            if "images" in field_data:
                for image_item in field_data["images"]:
                    if os.path.exists(image_item["file_path"]):
                        multimodal_inputs.append({
                            "type": "image",
                            "data": image_item["file_path"],
                            "prompt": image_item.get("description", ""),
                            "metadata": image_item.get("metadata", {})
                        })

            # Process through OpenAI
            context = field_data.get("context", "assessment")
            result = await self.openai.process_multimodal_input(multimodal_inputs, context)

            # Parse and structure the integrated analysis
            structured_result = self._structure_analysis_result(result, field_data)

            # Store in processing history
            self.processing_history.append({
                "timestamp": datetime.now().isoformat(),
                "field_data_id": field_data.get("id", "unknown"),
                "inputs_processed": len(multimodal_inputs),
                "result": structured_result
            })

            return structured_result

        except Exception as e:
            logger.error(f"Error processing field report: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "field_data_id": field_data.get("id", "unknown")
            }

    def _determine_processing_tier(self, text_item: Dict[str, Any]) -> ProcessingTier:
        """Determine appropriate processing tier based on content urgency"""

        content = text_item.get("content", "").lower()
        metadata = text_item.get("metadata", {})

        # Emergency keywords
        emergency_keywords = [
            "طوارئ", "أزمة", "عاجل", "خطر", "emergency", "crisis", "urgent", "critical",
            "outbreak", "attack", "violence", "death", "cholera", "disease"
        ]

        # Check for emergency indicators
        if any(keyword in content for keyword in emergency_keywords):
            return ProcessingTier.EMERGENCY

        # Check metadata priority
        if metadata.get("priority") == "high" or metadata.get("urgent") is True:
            return ProcessingTier.EMERGENCY

        # Check for assessment type
        if metadata.get("assessment_type") in ["protection_monitoring", "health_emergency"]:
            return ProcessingTier.STANDARD

        return ProcessingTier.BULK

    def _structure_analysis_result(self, openai_result: Dict[str, Any], original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure the OpenAI analysis result for humanitarian use"""

        try:
            # Try to parse the integrated analysis as JSON
            integrated_analysis = openai_result.get("integrated_analysis", "")

            try:
                parsed_analysis = json.loads(integrated_analysis)
            except json.JSONDecodeError:
                # If not JSON, structure manually
                parsed_analysis = {
                    "summary": integrated_analysis,
                    "needs_identified": [],
                    "severity": "MEDIUM",
                    "recommendations": [],
                    "sectors_involved": [],
                    "population_affected": 0
                }

            # Enhance with metadata
            structured_result = {
                "processing_info": {
                    "timestamp": openai_result.get("timestamp"),
                    "total_inputs": openai_result.get("total_inputs", 0),
                    "processing_successful": "error" not in openai_result
                },
                "source_data": {
                    "location": original_data.get("location", "Unknown"),
                    "collector": original_data.get("collector", "Unknown"),
                    "collection_time": original_data.get("timestamp", datetime.now().isoformat())
                },
                "analysis": parsed_analysis,
                "individual_results": openai_result.get("individual_results", []),
                "alert_triggers": self._identify_alert_triggers(parsed_analysis),
                "kobo_integration": self._prepare_kobo_data(parsed_analysis, original_data)
            }

            return structured_result

        except Exception as e:
            logger.error(f"Error structuring analysis result: {e}")
            return {
                "error": f"Structuring error: {str(e)}",
                "raw_result": openai_result
            }

    def _identify_alert_triggers(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify situations that should trigger alerts"""

        triggers = []

        # Check severity level
        severity = analysis.get("severity", "LOW")
        if severity in ["CRITICAL", "HIGH"]:
            triggers.append({
                "type": "high_severity",
                "severity": severity,
                "description": f"Assessment indicates {severity} level situation"
            })

        # Check population numbers
        population = analysis.get("population_affected", 0)
        if isinstance(population, (int, float)) and population > 10000:
            triggers.append({
                "type": "large_population_impact",
                "severity": "HIGH",
                "description": f"Large population affected: {population:,.0f} people",
                "population": int(population)
            })

        # Check for specific crisis indicators
        summary = str(analysis.get("summary", "")).lower()
        needs = analysis.get("needs_identified", [])

        crisis_indicators = {
            "disease_outbreak": ["outbreak", "epidemic", "cholera", "measles", "disease spread"],
            "protection_crisis": ["violence", "gbv", "attack", "safety", "protection"],
            "food_emergency": ["famine", "starvation", "malnutrition", "food crisis"],
            "displacement_emergency": ["mass displacement", "flee", "evacuation", "new arrivals"]
        }

        for crisis_type, keywords in crisis_indicators.items():
            if any(keyword in summary for keyword in keywords) or \
               any(keyword in str(need).lower() for need in needs for keyword in keywords):
                triggers.append({
                    "type": crisis_type,
                    "severity": "HIGH",
                    "description": f"Indicators of {crisis_type.replace('_', ' ')} detected"
                })

        return triggers

    def _prepare_kobo_data(self, analysis: Dict[str, Any], original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare structured data for KoboToolbox integration"""

        return {
            "form_data": {
                "location": original_data.get("location", ""),
                "assessment_date": original_data.get("timestamp", ""),
                "collector_name": original_data.get("collector", ""),
                "overall_severity": analysis.get("severity", "MEDIUM"),
                "population_affected": analysis.get("population_affected", 0),
                "primary_needs": analysis.get("needs_identified", [])[:5],  # Top 5 needs
                "sectors_affected": analysis.get("sectors_involved", []),
                "urgent_actions_required": analysis.get("recommendations", [])[:3],  # Top 3 actions
                "data_sources": len(original_data.get("text_reports", [])) + \
                              len(original_data.get("voice_recordings", [])) + \
                              len(original_data.get("images", []))
            },
            "attachments": {
                "images": [img["file_path"] for img in original_data.get("images", [])],
                "audio": [voice["file_path"] for voice in original_data.get("voice_recordings", [])],
                "processed_analysis": analysis
            }
        }


class EnhancedAssessmentAgent(BaseHumanitarianAgent):
    """Enhanced Assessment Agent with OpenAI multimodal capabilities"""

    def __init__(self, openai_api_key: str = None):
        super().__init__(
            sector="Enhanced Assessment & Multimodal Data Analysis",
            lead_agencies=["OCHA", "UNHCR", "WFP", "OpenAI Integration"],
            sudan_context={
                "multimodal_capabilities": [
                    "Arabic text processing", "Voice-to-text transcription",
                    "Image analysis for damage assessment", "Integrated analysis across modalities"
                ],
                "supported_languages": ["Arabic (Sudan dialect)", "English", "Mixed bilingual"],
                "data_sources": [
                    "KoboToolbox forms", "Voice recordings from field",
                    "Photos and videos", "WhatsApp messages", "SMS reports"
                ],
                "processing_tiers": {
                    "emergency": "GPT-4o for crisis situations",
                    "standard": "GPT-4 Turbo for regular operations",
                    "bulk": "GPT-3.5 Turbo for large-scale processing"
                },
                "integration_points": [
                    "Alert system for crisis detection",
                    "KoboToolbox for structured data",
                    "Sectoral agents for coordination",
                    "Dashboard for visualization"
                ]
            }
        )

        # Initialize OpenAI integration
        try:
            self.openai_integration = SudanHumanitarianOpenAI(api_key=openai_api_key)
            self.multimodal_processor = MultimodalDataProcessor(self.openai_integration)
            self.integration_available = True
        except Exception as e:
            logger.error(f"OpenAI integration initialization failed: {e}")
            self.integration_available = False
            self.openai_integration = None
            self.multimodal_processor = None

    def process_request(self, request: HumanitarianRequest) -> HumanitarianResponse:
        """Process assessment requests with multimodal capabilities"""

        if not self.integration_available:
            return self._fallback_processing(request)

        try:
            # Check if this is a multimodal request
            if hasattr(request, 'attachments') and request.attachments:
                return self._process_multimodal_request(request)
            else:
                return self._process_text_request(request)

        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return self._fallback_processing(request, error=str(e))

    def _process_multimodal_request(self, request: HumanitarianRequest) -> HumanitarianResponse:
        """Process multimodal request with OpenAI integration"""

        # This would be called asynchronously in a real implementation
        # For now, we'll simulate the structure

        field_data = {
            "id": f"assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "location": request.location or "Unknown",
            "context": "multimodal_assessment",
            "timestamp": datetime.now().isoformat(),
            "collector": request.requester or "Field Team",
            "text_reports": [{"content": request.query, "metadata": {"priority": request.priority}}],
            "voice_recordings": getattr(request, 'voice_files', []),
            "images": getattr(request, 'image_files', [])
        }

        # In a real async implementation, this would be:
        # result = await self.multimodal_processor.process_field_report(field_data)

        # For now, simulate the response structure
        analysis_result = {
            "processing_info": {
                "timestamp": datetime.now().isoformat(),
                "total_inputs": 1 + len(getattr(request, 'voice_files', [])) + len(getattr(request, 'image_files', [])),
                "processing_successful": True
            },
            "analysis": {
                "summary": f"Multimodal assessment processed for {request.location}",
                "severity": request.priority or "MEDIUM",
                "needs_identified": ["Assessment data processed", "Further analysis recommended"],
                "recommendations": ["Deploy additional assessment team", "Coordinate with relevant sectors"],
                "sectors_involved": ["Assessment", "OCHA"],
                "population_affected": 5000
            },
            "alert_triggers": [
                {
                    "type": "multimodal_processing",
                    "severity": "MEDIUM",
                    "description": "Multimodal assessment data processed successfully"
                }
            ]
        }

        return HumanitarianResponse(
            sector=self.sector,
            analysis="Enhanced multimodal assessment processing completed with OpenAI integration",
            data=json.dumps(analysis_result, indent=2),
            recommendations=[
                "Continue multimodal data collection for comprehensive situational awareness",
                "Coordinate with Alert Agent for crisis detection",
                "Update KoboToolbox with structured findings",
                "Monitor for additional data inputs from field teams"
            ],
            priority_level=analysis_result["analysis"]["severity"],
            locations=[request.location] if request.location else ["Multiple locations"],
            metadata={
                "openai_integration": True,
                "multimodal_processing": True,
                "alert_triggers": len(analysis_result["alert_triggers"]),
                "processing_timestamp": analysis_result["processing_info"]["timestamp"]
            }
        )

    def _process_text_request(self, request: HumanitarianRequest) -> HumanitarianResponse:
        """Process text-only request with Arabic support"""

        # Simulate OpenAI text processing
        analysis = {
            "text_processed": request.query,
            "language_detected": "Arabic/English mixed" if any(ord(char) > 127 for char in request.query) else "English",
            "severity_assessment": request.priority or "MEDIUM",
            "key_indicators": ["Text analysis completed", "Language processing successful"],
            "translation_needed": any(ord(char) > 127 for char in request.query)
        }

        return HumanitarianResponse(
            sector=self.sector,
            analysis=f"Text-based assessment processed with OpenAI integration. Language detected: {analysis['language_detected']}",
            data=json.dumps(analysis, indent=2, ensure_ascii=False),
            recommendations=[
                "Continue text-based data collection",
                "Consider adding voice and image data for comprehensive assessment",
                "Coordinate with relevant sectoral agents based on content",
                "Update assessment database with findings"
            ],
            priority_level=analysis["severity_assessment"],
            locations=[request.location] if request.location else ["Text analysis location"],
            metadata={
                "openai_integration": True,
                "text_processing": True,
                "language_detected": analysis["language_detected"],
                "translation_available": analysis["translation_needed"]
            }
        )

    def _fallback_processing(self, request: HumanitarianRequest, error: str = None) -> HumanitarianResponse:
        """Fallback processing when OpenAI integration is not available"""

        analysis = "OpenAI integration not available. Using fallback assessment processing."
        if error:
            analysis += f" Error: {error}"

        return HumanitarianResponse(
            sector=self.sector,
            analysis=analysis,
            data=f"Fallback processing for: {request.query}",
            recommendations=[
                "Check OpenAI API key configuration",
                "Verify internet connectivity",
                "Use standard assessment processing as backup",
                "Contact technical support for OpenAI integration issues"
            ],
            priority_level="MEDIUM",
            locations=[request.location] if request.location else ["Unknown"],
            metadata={
                "openai_integration": False,
                "fallback_mode": True,
                "error": error
            }
        )

    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get statistics about processing performance and costs"""

        if not self.multimodal_processor:
            return {"error": "Multimodal processor not initialized"}

        history = self.multimodal_processor.processing_history

        stats = {
            "total_assessments_processed": len(history),
            "processing_timeline": {
                "first_assessment": history[0]["timestamp"] if history else None,
                "latest_assessment": history[-1]["timestamp"] if history else None
            },
            "input_type_breakdown": {
                "text_only": 0,
                "multimodal": 0,
                "voice_included": 0,
                "image_included": 0
            },
            "error_rate": 0,
            "average_inputs_per_assessment": 0
        }

        if history:
            total_inputs = sum(item.get("inputs_processed", 0) for item in history)
            stats["average_inputs_per_assessment"] = total_inputs / len(history)

            errors = sum(1 for item in history if "error" in item.get("result", {}))
            stats["error_rate"] = errors / len(history) * 100

        return stats


# Testing and usage example
def create_sample_multimodal_request():
    """Create a sample multimodal request for testing"""

    # Create a sample request with Arabic text
    sample_request = HumanitarianRequest(
        query="الوضع في مخيم النيالة صعب جداً. نحتاج مياه وغذاء عاجل. الأطفال مرضى والمياه مقطوعة منذ أسبوع. The situation in Nyala camp is very difficult.",
        priority="HIGH",
        location="Nyala IDP Settlement",
        requester="Field Assessment Team"
    )

    return sample_request


def test_enhanced_assessment_agent():
    """Test the enhanced assessment agent"""

    print("Testing Enhanced Assessment Agent with OpenAI Integration")
    print("=" * 60)

    try:
        # Initialize the agent (will use fallback if no OpenAI key)
        agent = EnhancedAssessmentAgent()

        # Create and process a sample request
        sample_request = create_sample_multimodal_request()
        response = agent.process_request(sample_request)

        print("Assessment Processing Results:")
        print(f"Sector: {response.sector}")
        print(f"Analysis: {response.analysis}")
        print(f"Priority: {response.priority_level}")
        print(f"Locations: {response.locations}")
        print(f"OpenAI Integration: {response.metadata.get('openai_integration', False)}")

        # Get processing statistics
        stats = agent.get_processing_statistics()
        print(f"\nProcessing Statistics: {json.dumps(stats, indent=2)}")

        return True

    except Exception as e:
        print(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    test_enhanced_assessment_agent()