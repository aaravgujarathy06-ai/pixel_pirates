"""
llm_parser.py
-------------
Natural Language to Structured Geospatial Analysis Plan Translator.

Converts plain English queries (e.g. "Show vegetation loss in Pune between 2015 and 2020")
into validated JSON analysis plans. Supported operations:
  - 'vegetation_loss'
  - 'vegetation_gain'
  - 'ndvi_2015'
  - 'ndvi_2020'
"""

import json
import re

SYSTEM_PROMPT = """
You are a geospatial analysis assistant for QGIS.
Translate the user's natural language request into a valid JSON object matching this strict schema:

{
  "operation": "vegetation_loss" | "vegetation_gain" | "ndvi_2015" | "ndvi_2020",
  "region": string (e.g. "pune"),
  "start_year": integer (e.g. 2015),
  "end_year": integer (e.g. 2020),
  "threshold": float (default: 0.15)
}

Rules:
1. Return ONLY the JSON object. No explanations or extra text.
2. Supported operations are ONLY: 'vegetation_loss', 'vegetation_gain', 'ndvi_2015', 'ndvi_2020'.
3. Default region is "pune" if unspecified.
"""

class LLMParser:
    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def parse_query(self, user_query: str) -> dict:
        """
        Parses natural language query into JSON analysis plan using LLM API
        with an automatic local rule-based fallback if API key is missing or call fails.
        """
        if self.api_key and self.api_key.strip():
            try:
                return self._parse_with_openai(user_query)
            except Exception as e:
                print(f"[GeoGPT LLMParser] API call failed ({e}). Using rule-based parser fallback.")
                return self._parse_fallback(user_query)
        else:
            return self._parse_fallback(user_query)

    def _parse_with_openai(self, user_query: str) -> dict:
        import urllib.request

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key.strip()}"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query}
            ],
            "temperature": 0.0
        }

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            content = res_data["choices"][0]["message"]["content"]
            
            # Extract JSON block if wrapped in markdown code fence
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group(0))
                return self._validate_plan(plan)
            else:
                raise ValueError("No valid JSON found in LLM response.")

    def _parse_fallback(self, user_query: str) -> dict:
        """
        Local deterministic parser for offline / zero-API-key fallback mode.
        """
        query_lower = user_query.lower()
        
        # Extract years using regex
        years = [int(y) for y in re.findall(r'\b(20\d{2})\b', query_lower)]
        start_year = min(years) if years else 2015
        end_year = max(years) if len(years) > 1 else 2020

        # Determine operation using broad keyword matchers
        loss_keywords = ["loss", "lost", "decrease", "deforestation", "degradation", "sprawl", "encroachment", "cut", "drop", "damage", "reduction"]
        gain_keywords = ["gain", "gained", "increase", "growth", "reforestation", "afforestation", "greening", "planting", "recovery", "expansion"]
        
        if any(k in query_lower for k in loss_keywords):
            operation = "vegetation_loss"
        elif any(k in query_lower for k in gain_keywords):
            operation = "vegetation_gain"
        elif "2015" in query_lower and "2020" not in query_lower:
            operation = "ndvi_2015"
        elif "2020" in query_lower and "2015" not in query_lower:
            operation = "ndvi_2020"
        else:
            operation = "vegetation_loss"

        # Determine region
        region = "pune"
        if "bangalore" in query_lower or "bengaluru" in query_lower:
            region = "bangalore"

        plan = {
            "operation": operation,
            "region": region,
            "start_year": start_year,
            "end_year": end_year,
            "threshold": 0.15
        }
        return self._validate_plan(plan)

    def _validate_plan(self, plan: dict) -> dict:
        """Validates and enforces plan standards."""
        valid_ops = ["vegetation_loss", "vegetation_gain", "ndvi_2015", "ndvi_2020"]
        if plan.get("operation") not in valid_ops:
            plan["operation"] = "vegetation_loss"
            
        if "start_year" not in plan:
            plan["start_year"] = 2015
        if "end_year" not in plan:
            plan["end_year"] = 2020
        if "threshold" not in plan:
            plan["threshold"] = 0.15

        return plan

    def generate_solution(self, query: str, stats: dict) -> str:
        """
        Generates structured AI solution and urban policy recommendation.
        Calls live OpenAI API if api_key is set, or returns rich template if offline/no-key.
        """
        if self.api_key and self.api_key.strip():
            try:
                return self._generate_solution_openai(query, stats)
            except Exception as e:
                print(f"[GeoGPT LLMParser] API solution call failed ({e}). Using template fallback.")

        region = stats.get("Region", "Target Region")
        timeframe = stats.get("Timeframe", "2015-2020")
        loss_area = stats.get("Vegetation Area Lost", "N/A")
        pct_loss = stats.get("Percentage Loss", "N/A")
        
        solution_md = f"""
<b style="color: #0284c7;">[AI Key Findings - {region}]</b><br/>
- Analyzed timeframe: <b>{timeframe}</b><br/>
- Total Green Cover Lost: <b>{loss_area}</b> (approx <b>{pct_loss}</b> drop)<br/>
- Primary cause: Rapid urban sprawl & infrastructure expansion into vegetation zones.<br/><br/>

<b style="color: #0284c7;">[Recommended Solutions & Action Plan]</b><br/>
1. <b>Eco-Buffer Zone:</b> Establish a 500m green protection buffer along high-loss sectors.<br/>
2. <b>Targeted Afforestation:</b> Deploy micro-forest re-plantation in high-NDVI drop pixels.<br/>
3. <b>Urban Policy:</b> Implement mandatory green roofing incentives for new developments.
"""
        return solution_md

    def _generate_solution_openai(self, query: str, stats: dict) -> str:
        import urllib.request

        prompt = f"""
Given the following satellite spatial analysis results:
User Query: "{query}"
Stats: {json.dumps(stats, indent=2)}

Write a concise, professional HTML summary (3-4 paragraphs) with:
1. <b>[AI Key Findings]</b> summarizing the numerical spatial findings.
2. <b>[Recommended Solutions & Action Plan]</b> giving 3 actionable urban planning / policy recommendations based on the findings.
Use HTML tags (<b>, <br/>) for clean formatting. Keep it brief.
"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key.strip()}"
        }
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are an expert geospatial environmental urban analyst."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            return res_data["choices"][0]["message"]["content"]
