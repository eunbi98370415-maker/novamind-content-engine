"""
NovaMind Content Service
Orchestrates all LLM-powered content generation using ContentService.
Produces blogs, newsletters, subject lines, and repurposing notes.
"""

import json
import re
from services.llm_service import LLMService
from utils.helpers import word_count, estimate_read_time


SYSTEM_PROMPT = """You are NovaMind's expert content strategist and copywriter.
NovaMind is an AI-powered content repurposing platform that helps small teams
(agencies, startup marketers, solo creators) turn one blog post into personalized
campaigns for every audience segment — automatically.

Your job is to generate high-quality, professional marketing content that:
- Reads like it was written by a skilled human marketer (not generic AI)
- Is tailored precisely to the specified audience persona
- Opens with a compelling pain point or hook
- Delivers clear, actionable value
- Ends with a natural, non-pushy CTA

Always respond with valid JSON in the exact format requested. No markdown code fences
around the JSON. No extra explanation outside the JSON structure."""


LENGTH_GUIDE = {
    "Short": {"target": "400–600 words", "sections": 3},
    "Medium": {"target": "800–1000 words", "sections": 4},
    "Long": {"target": "1200–1500 words", "sections": 5},
}


class ContentService:
    """High-level content generation orchestrator."""

    def __init__(self):
        self.llm = LLMService()

    # ── Blog Generation ────────────────────────────────────────────────────────

    def generate_blog(self, topic: str, angle: str, tone: str, length: str) -> dict:
        """
        Generate a full blog post for the given topic.

        Returns:
            dict with keys: title, meta_description, body, word_count, read_time, cta
        """
        length_info = LENGTH_GUIDE.get(length, LENGTH_GUIDE["Medium"])
        angle_note = f"\nAngle / Objective: {angle}" if angle else ""

        prompt = f"""Write a compelling blog post for NovaMind's content marketing.

Topic: {topic}{angle_note}
Tone: {tone}
Target length: {length_info['target']}

Requirements:
- Open with a sharp, relatable pain point in the first sentence
- Use {length_info['sections']} H2 sections (## in markdown)
- Each section should be practical and actionable
- Naturally mention NovaMind as the solution (not in every section — once or twice)
- End with a brief, encouraging CTA paragraph
- Write in a {tone.lower()} tone throughout

Return ONLY valid JSON in this exact structure:
{{
  "title": "compelling title here",
  "meta_description": "SEO meta description under 160 characters",
  "body": "full markdown body here with ## headings",
  "cta": "CTA text for end of post"
}}"""

        raw = self.llm.generate(prompt, system=SYSTEM_PROMPT, max_tokens=3000)
        parsed = self._parse_json(raw)

        # Enrich with computed fields
        body = parsed.get("body", "")
        parsed["word_count"] = word_count(body)
        parsed["read_time"] = estimate_read_time(body)
        return parsed

    # ── Newsletter Generation ─────────────────────────────────────────────────

    def generate_newsletter(
        self, blog: dict, persona: dict, tone: str, cta_type: str
    ) -> dict:
        """
        Generate a persona-specific newsletter from a blog post.

        Returns:
            dict with keys: subject_line, preview_text, body, cta_text
        """
        # Build a rich persona context block
        persona_id = persona.get("id", "")
        persona_name = persona.get("name", "")
        goals = persona.get("goals", [])
        pain_points = persona.get("pain_points", [])
        hooks = persona.get("content_hooks", [])

        # Derive a role label and scenario for the opener
        role_labels = {
            "agency_owner":      "a creative agency owner",
            "startup_marketer":  "a marketing manager at a startup",
            "solo_creator":      "a freelancer or solo creator",
        }
        top_pains = {
            "agency_owner":      "You write good content, but you're only using each piece once — while client deadlines eat every spare hour.",
            "startup_marketer":  "You're sending the same email to your entire list, watching open rates flatline, and have no clean way to segment at scale.",
            "solo_creator":      "You know you should be repurposing your content, but between client work and everything else, it never actually happens.",
        }
        differentiator_notes = {
            "agency_owner": (
                "Emphasise: team leverage, client acquisition, agency reputation. "
                "Use examples relevant to running campaigns for multiple clients. "
                "Value prop = one workflow that multiplies output without adding headcount. "
                "Avoid startup/growth language — speak peer-to-peer, like one agency strategist to another."
            ),
            "startup_marketer": (
                "Emphasise: funnel performance, CTR, segmentation, measurable ROI. "
                "Use metric-forward language (open rates, conversion lift, A/B tests). "
                "Value prop = automatic segmentation that makes every send smarter. "
                "Avoid freelancer/lifestyle language — this reader reports to leadership and needs numbers."
            ),
            "solo_creator": (
                "Emphasise: time saved, consistency, getting more reach without more work. "
                "Use relatable solo-operator scenarios (Sunday-night dread, blank page, juggling everything). "
                "Value prop = AI handles the distribution layer so they can focus on the work they love. "
                "Avoid enterprise/team language — this reader works alone and wants simplicity."
            ),
        }

        cta_templates = {
            "Free Trial":         "Start free — no credit card required →",
            "Newsletter Signup":  "Join the weekly NovaMind workflow →",
            "Book a Demo":        "Book a 20-minute walkthrough →",
            "Download Guide":     "Download the free repurposing guide →",
        }
        cta_suggestion = cta_templates.get(cta_type, "Start free — no credit card required →")
        persona_must_include = {
            "agency_owner": """
Must make the email feel written for an agency owner.
Include language about client work, ROI, team capacity, or delivering results for multiple clients.
The examples and benefits should sound like they are for someone running an agency.
""",
            "startup_marketer": """
Must make the email feel written for a startup marketer.
Include language about growth, campaign performance, testing, conversion, and reporting results.
The examples and benefits should sound metrics-driven and execution-focused.
""",
            "solo_creator": """
Must make the email feel written for a solo creator.
Include language about saving time, staying consistent, reducing workload, and simplifying content creation.
The examples and benefits should sound personal, practical, and lightweight.
""",
        }
        prompt = f"""Write a persona-specific marketing email for NovaMind.

─── SOURCE CONTENT ───────────────────────────────────────
Blog title:   {blog.get('title', '')}
Blog summary: {blog.get('meta_description', '')}
Blog excerpt:
{blog.get('body', '')[:1000]}

─── AUDIENCE ─────────────────────────────────────────────
This email is for: {persona_name} ({persona_id})
Role description: {role_labels.get(persona_id, persona_name)}
Their profile: {persona.get('profile', '')}
Their top goals: {'; '.join(goals)}
Their pain points: {'; '.join(pain_points)}
Content hooks that resonate: {'; '.join(hooks)}
Messaging angle: {persona.get('messaging_angle', '')}

─── DIFFERENTIATION BRIEF ────────────────────────────────
{differentiator_notes.get(persona_id, '')}

─── PERSONA-SPECIFIC REQUIREMENT ─────────────────────────
{persona_must_include.get(persona_id, '')}

─── TONE & CTA ───────────────────────────────────────────
Overall tone: {tone}
CTA action:   {cta_type}  →  Suggested CTA text: "{cta_suggestion}"

─── EXACT STRUCTURE TO FOLLOW ────────────────────────────

Opening line (REQUIRED — do this exactly):
  Start with "Hi [First Name]," then a single sentence that:
  • names the reader's role explicitly (e.g. "As an agency owner...", "Running marketing at a startup...")
  • immediately surfaces their specific pain point: "{top_pains.get(persona_id, '')}"
  Keep it 1–2 sentences. No fluff, no generic welcome.

Transition paragraph (1–2 sentences):
  Briefly connect their pain to what this week's content addresses.
  Make it feel like a helpful insight, not a pitch.

Value section — use bullet points:
  Exactly 3 bullets. Each bullet must:
  • start with a bold keyword (e.g. **One input,**)
  • deliver a concrete, persona-specific benefit
  • be no longer than one line
  Bullets must feel meaningfully different from the other two persona versions.
  Reference specific outcomes from the blog content.

Closing (1–2 sentences):
  Warm but brief. Reinforce the core value without restating the bullets.
  Do NOT use "Best," or "Sincerely," — end naturally.

CTA line (final line, standalone):
  Use this exact format:
  [{cta_suggestion}]
  Make it the last line of the body, on its own line.

─── HARD RULES ───────────────────────────────────────────
✗ Do NOT write more than 200 words total in the body
✗ Do NOT use generic phrases like "In today's fast-paced world" or "We're excited to share"
✗ Do NOT mention other personas or compare audiences
✗ Do NOT use a formal sign-off — end with the CTA then "— The NovaMind Team"
✓ Short paragraphs (2 sentences max before a break)
✓ Sound like a knowledgeable colleague, not a newsletter bot
✓ The subject line must hook THIS specific persona — not a generic audience
✓ The body must feel obviously different for each persona, even if the source blog is the same
✓ Use persona-specific vocabulary and examples that would not fit the other personas

Return ONLY valid JSON (no markdown fences, no commentary):
{{
  "subject_line": "max 52 chars — specific to {persona_name}",
  "preview_text": "max 90 chars — extends the subject naturally",
  "body": "full email body with [First Name] — follows the structure above exactly",
  "cta_text": "{cta_suggestion}"
}}"""

        raw = self.llm.generate(prompt, system=SYSTEM_PROMPT, max_tokens=1800)
        return self._parse_json(raw)

    # ── Subject Line Generation ───────────────────────────────────────────────

    def generate_subject_lines(self, topic: str, persona: dict) -> list:
        """
        Generate 3 A/B-testable subject lines for a persona.

        Returns:
            list of 3 subject line strings
        """
        prompt = f"""Generate 3 distinct email subject lines for the following topic
and audience persona. Each should use a different psychological hook.

Topic: {topic}
Persona: {persona.get('name', '')}
Their pain points: {', '.join(persona.get('pain_points', [])[:2])}
Content hooks that resonate with them: {', '.join(persona.get('content_hooks', []))}
Preferred tone: {persona.get('preferred_tone', '')}

Hook types to use (one each):
1. Curiosity / pattern interrupt
2. Direct benefit / outcome
3. Pain point / problem awareness

Rules:
- Max 50 characters each
- No clickbait or false promises
- Feel human and conversational
- Avoid ALL CAPS and excessive punctuation

Return ONLY a valid JSON array of exactly 3 strings:
["subject line 1", "subject line 2", "subject line 3"]"""

        raw = self.llm.generate(prompt, system=SYSTEM_PROMPT, max_tokens=500)
        parsed = self._parse_json(raw)
        if isinstance(parsed, list):
            return parsed[:3]
        # Fallback if JSON parse failed
        return persona.get("content_hooks", ["Your content is underperforming.", "Fix this today.", "One click to better campaigns."])[:3]

    # ── Repurposing Notes ─────────────────────────────────────────────────────

    def generate_repurposing_notes(self, blog: dict, personas: list) -> str:
        """
        Generate a markdown repurposing guide for a blog post across multiple personas.

        Returns:
            Markdown string with channel-by-channel repurposing recommendations
        """
        persona_names = ", ".join(p.get("name", "") for p in personas)

        prompt = f"""Create a detailed content repurposing guide for this blog post.

BLOG TITLE: {blog.get('title', '')}
BLOG SUMMARY: {blog.get('meta_description', '')}
TARGET PERSONAS: {persona_names}

Generate a markdown guide with repurposing recommendations for:
1. LinkedIn posts (3 angles: hook post, story post, carousel idea)
2. Twitter/X thread structure
3. Short-form video script outline (60 seconds)
4. 3-email drip sequence plan
5. Podcast talking points
6. Paid ad copy variants (2 headlines + body)

For each channel, make the recommendations specific to the blog content —
not generic advice. Reference actual points from the blog title and topic.
Keep each section concise but actionable."""

        return self.llm.generate(prompt, system=SYSTEM_PROMPT, max_tokens=2000)

    # ── Full Campaign Orchestration ───────────────────────────────────────────

    def generate_campaign(
        self,
        topic: str,
        angle: str,
        tone: str,
        cta_type: str,
        length: str,
        persona_ids: list,
        personas_data: list,
    ) -> dict:
        """
        Orchestrate full campaign generation: blog + newsletters + subject lines
        + repurposing notes for all specified personas.

        Returns:
            Complete campaign dict ready to be saved to DB.
        """
        # Filter personas_data to only selected persona_ids
        selected_personas = [
            p for p in personas_data if p["id"] in persona_ids
        ]

        # 1. Generate blog post
        blog = self.generate_blog(topic, angle, tone, length)

        # 2. Generate newsletters and subject lines per persona
        newsletters = {}
        subject_lines = {}
        for persona in selected_personas:
            pid = persona["id"]
            newsletter = self.generate_newsletter(blog, persona, tone, cta_type)
            newsletters[pid] = newsletter
            lines = self.generate_subject_lines(topic, persona)
            subject_lines[pid] = lines

        # 3. Generate repurposing notes
        repurposing_notes = self.generate_repurposing_notes(blog, selected_personas)

        return {
            "topic": topic,
            "angle": angle,
            "tone": tone,
            "cta_type": cta_type,
            "length_preference": length,
            "personas": persona_ids,
            "blog_content": blog,
            "newsletters": newsletters,
            "repurposing_notes": repurposing_notes,
            "subject_lines": subject_lines,
            "status": "draft",
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _parse_json(self, text: str) -> dict | list:
        """
        Attempt to parse JSON from LLM output.
        Handles code-fenced JSON and leading/trailing whitespace.
        """
        if not text:
            return {}

        # Strip markdown code fences if present
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON object/array from surrounding text
            match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            # Last resort: return raw text in a body field
            return {"body": text, "title": "Generated Content"}
