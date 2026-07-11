import re
import logging
from typing import Set

logger = logging.getLogger(__name__)

class ResponseValidator:
    @staticmethod
    def validate(response: str, context: str) -> str:
        # Standard fallback output
        fallback_msg = "I cannot find that information in the analytical results."
        
        # Check if the response matches or is very similar to the fallback or mock fallback
        if fallback_msg.lower() in response.lower():
            return fallback_msg

        # Extract numbers using regex
        response_nums = ResponseValidator._extract_numbers(response)
        context_nums = ResponseValidator._extract_numbers(context)
        
        # Define allowed generic numbers (e.g., loop counters, dates, standard configurations)
        allowed_generic = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 30, 60, 90, 100}
        
        # Check if any response number is a hallucinated numeric claim
        for num in response_nums:
            if num in allowed_generic:
                continue
                
            # Check if this number is in the context (using approximate float mapping to cover rounding)
            matched = False
            for c_num in context_nums:
                if abs(num - c_num) < 0.05:  # Tolerance threshold for rounding
                    matched = True
                    break
                    
            if not matched:
                logger.warning(f"Hallucination Detected: Response number {num} is not grounded in context.")
                return fallback_msg
                
        return response

    @staticmethod
    def _extract_numbers(text: str) -> Set[float]:
        # Regex to match integers and floats, ignoring currency symbols and commas
        # Matches: 10,000.50 -> 10000.50, $15.5 -> 15.5
        numbers = set()
        clean_text = text.replace(",", "")
        matches = re.findall(r'\b\d+(?:\.\d+)?\b', clean_text)
        
        for m in matches:
            try:
                val = float(m)
                # Ignore very small fractional values if not relevant, or save
                numbers.add(val)
            except ValueError:
                pass
        return numbers
