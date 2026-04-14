"""
NovaMind LLM Service
Abstraction layer supporting Anthropic Claude, OpenAI GPT-4o, and mock mode.
"""

from utils.config import ANTHROPIC_API_KEY, OPENAI_API_KEY, LLM_PROVIDER, MOCK_MODE


class LLMService:
    """Unified LLM interface with automatic provider detection and mock fallback."""

    def __init__(self):
        self.mock_mode = MOCK_MODE
        self.provider = LLM_PROVIDER
        self._client = None

        if not self.mock_mode:
            self._init_client()

    def _init_client(self):
        """Initialise the appropriate API client."""
        try:
            if self.provider == "anthropic":
                import anthropic
                self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            elif self.provider == "openai":
                import openai
                self._client = openai.OpenAI(api_key=OPENAI_API_KEY)
        except Exception as e:
            # If client init fails, fall back to mock
            self.mock_mode = True
            self._client = None

    def generate(self, prompt: str, system: str = None, max_tokens: int = 4000) -> str:
        """
        Generate text from the configured LLM provider.
        Falls back to mock_generate if in mock mode or on API error.
        """
        if self.mock_mode or self._client is None:
            return self.mock_generate(prompt)

        try:
            if self.provider == "anthropic":
                return self._generate_anthropic(prompt, system, max_tokens)
            elif self.provider == "openai":
                return self._generate_openai(prompt, system, max_tokens)
        except Exception as e:
            # Graceful degradation: log and return mock content
            print(f"[LLMService] API error ({self.provider}): {e}")
            return self.mock_generate(prompt)

        return self.mock_generate(prompt)

    def _generate_anthropic(self, prompt: str, system: str, max_tokens: int) -> str:
        """Call Claude via Anthropic SDK with adaptive thinking and streaming."""
        import anthropic

        messages = [{"role": "user", "content": prompt}]
        kwargs = {
            "model": "claude-opus-4-5",
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        # Use streaming with get_final_message for reliability
        with self._client.messages.stream(**kwargs) as stream:
            message = stream.get_final_message()

        # Extract text from content blocks
        text_parts = []
        for block in message.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
        return "\n".join(text_parts)

    def _generate_openai(self, prompt: str, system: str, max_tokens: int) -> str:
        """Call GPT-4o via OpenAI SDK."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    # ── Mock Content Generation ─────────────────────────────────────────────

    def mock_generate(self, prompt: str) -> str:
        """
        Return realistic pre-written mock content based on detected prompt type.
        Checks for keyword signals to route to the correct mock template.
        Order matters: more specific checks come first.
        """
        prompt_lower = prompt.lower()

        # Repurposing guide — must be checked FIRST (before newsletter/email checks)
        # Only triggered by the explicit repurposing guide request phrase
        if ("create a detailed content repurposing" in prompt_lower
                or "repurposing guide" in prompt_lower
                or "repurposing recommendations" in prompt_lower):
            return self._mock_repurposing_notes()

        # Full newsletter/email generation
        # Detected by the distinct phrase used in generate_newsletter prompts
        if ("marketing email newsletter" in prompt_lower
                or "personalized marketing email" in prompt_lower):
            return self._mock_newsletter(prompt_lower)

        # Standalone subject line generation
        # Detected by "generate" + "subject line" without "blog post" context
        if ("generate" in prompt_lower and "subject line" in prompt_lower
                and "blog post" not in prompt_lower):
            return self._mock_subject_lines(prompt_lower)

        # Blog post generation
        if ("write a compelling blog" in prompt_lower
                or "write a compelling" in prompt_lower
                or "blog post for novamind" in prompt_lower):
            return self._mock_blog_post()

        # Generic blog fallback
        if "blog" in prompt_lower or "article" in prompt_lower:
            return self._mock_blog_post()

        # Generic newsletter/email fallback
        if "newsletter" in prompt_lower or "email" in prompt_lower:
            return self._mock_newsletter(prompt_lower)

        # Default fallback
        return self._mock_blog_post()

    def _mock_blog_post(self) -> str:
        return """{
  "title": "From One Blog to 100 Personalized Campaigns",
  "meta_description": "You write one great post. NovaMind turns it into personalized campaigns for every segment of your audience — automatically, in minutes.",
  "body": "# From One Blog to 100 Personalized Campaigns\\n\\nYou write one great blog post. Then it sits on your website, gets shared once on LinkedIn, and quietly disappears. Meanwhile, that same content could have become five email sequences, twelve social posts, and a personalized newsletter for every segment of your audience.\\n\\nThis is the repurposing gap — and it's costing small teams more reach than they realize.\\n\\n## The Problem With One-and-Done Publishing\\n\\nMost content teams operate on a simple loop: write, publish, share once, move on. It's not a strategy problem — it's a capacity problem. When you're a team of three running campaigns for fifteen clients, there isn't time to rework every blog post into a newsletter, then rework that newsletter for three different audience segments.\\n\\nSo the content dies on the vine. You've invested hours into research and writing, and the return is a single LinkedIn post that gets 47 likes.\\n\\n## What AI-Driven Repurposing Actually Looks Like\\n\\nNovaMind changes the equation. Instead of treating each piece of content as a one-time asset, the platform treats it as raw material. You paste in your blog post — or describe a topic — and NovaMind generates:\\n\\n- A personalized newsletter for your agency-owner audience (ROI-focused, peer-to-peer tone)\\n- A different newsletter for your startup-marketer segment (data-driven, metric-aware)\\n- A casual, efficiency-first version for freelancers and solo creators\\n- Three subject line variants per segment (A/B test-ready)\\n- A repurposing guide for social, ads, and video scripts\\n\\nAll from one input. All in under three minutes.\\n\\n## Why Personalization at This Scale Matters\\n\\nThe data is unambiguous: segmented campaigns outperform broadcast emails by 14–76% depending on the metric. The problem has never been whether to personalize — it's been the cost of doing it.\\n\\nWhen each personalized variant requires a separate writer, brief, and review cycle, even well-resourced teams send generic blasts and accept the performance hit. NovaMind eliminates that trade-off.\\n\\n## The Workflow in Practice\\n\\nHere's how a typical NovaMind workflow runs for a content team:\\n\\n1. **Monday morning**: The scheduler triggers automatically, pulling the week's topic\\n2. **Content generation**: Blog post + three newsletter variants generated in ~2 minutes\\n3. **Quick review**: The marketer reads, edits tone if needed, approves\\n4. **Send**: Contacts are already segmented in CRM — each persona receives the right version\\n5. **Analytics**: Open rates, CTR, and conversion data feed back into next week's subject line choices\\n\\nThe team went from spending four hours on a single newsletter to reviewing three in twenty minutes.\\n\\n## Getting Started Without Disrupting Your Stack\\n\\nNovaMind is designed to slot into existing workflows, not replace them. It connects to your CRM, exports to your email platform, and generates content in formats you can copy-paste or schedule directly.\\n\\nIf you're already writing content, you're already 80% of the way there. The question is whether that content is working as hard as it could be.\\n\\nStart your first campaign and see what one blog post can become."
}"""

    def _mock_newsletter(self, prompt_lower: str) -> str:
        if "agency" in prompt_lower or "agency_owner" in prompt_lower:
            return """{
  "subject_line": "One blog. Five client campaigns. Automatically.",
  "preview_text": "Agency owners: stop letting great content die after one post.",
  "body": "Hi [First Name],\\n\\nAs an agency owner, you're already producing content worth reading — the problem is you're using each piece exactly once, while client deadlines make sure there's never time to go back.\\n\\nThis week's post breaks down how small agencies are closing that gap without adding headcount.\\n\\n- **One blog, multiplied:** A single post automatically generates newsletters, social variants, and ad copy for each client segment\\n- **Reclaim billable hours:** Teams report saving 4+ hours per campaign cycle — time that goes back to client work, not content admin\\n- **Look enterprise, stay lean:** Your content output starts matching agencies five times your size\\n\\nYour content is already doing the hard work. NovaMind makes sure it goes the distance.\\n\\n[See how it works for agencies →]\\n\\n— The NovaMind Team",
  "cta_text": "See how it works for agencies →"
}"""
        elif "startup" in prompt_lower or "startup_marketer" in prompt_lower:
            return """{
  "subject_line": "Your open rates want segmentation. Here's how.",
  "preview_text": "One content input → three segmented campaigns, automatically.",
  "body": "Hi [First Name],\\n\\nRunning marketing at a startup means your email list is a mix of different buyer types — and right now, they're all getting the same message. That's why your open rates are stuck and your CTR isn't moving.\\n\\nThis week's post is a practical breakdown of how AI-driven segmentation changes those numbers.\\n\\n- **One input, three campaigns:** Paste a blog topic, get persona-specific email variants for each segment — no manual rewriting\\n- **A/B-ready from the start:** Subject line variants per segment are generated automatically, so you're always testing\\n- **Metrics that move:** Teams see an average 22% lift in open rates within the first month of segmented sending\\n\\nYou don't need a bigger team to send smarter campaigns. You need a better workflow.\\n\\n[Start your free 14-day trial →]\\n\\n— The NovaMind Team",
  "cta_text": "Start your free 14-day trial →"
}"""
        else:
            return """{
  "subject_line": "You wrote the blog. Let AI write the rest.",
  "preview_text": "One post → newsletter, social, email follow-up. Done.",
  "body": "Hi [First Name],\\n\\nAs a freelancer, you know exactly what it feels like: you finish a solid blog post, share it once, and then spend the next week staring at a blank screen trying to figure out what to send your newsletter list.\\n\\nNovaMind breaks that loop — and it takes less than three minutes.\\n\\n- **Paste your post, get a full campaign:** Newsletter, subject lines, and social variants generated from a single input\\n- **Stay consistent without burning out:** No more starting from scratch every week — your next email is always one click away\\n- **Sound like yourself, not a bot:** NovaMind adapts to your tone, so the output actually sounds like you wrote it\\n\\nYou already have the ideas. You just needed the system to turn them into content that actually ships.\\n\\n[Try it free — no credit card required →]\\n\\n— The NovaMind Team",
  "cta_text": "Try it free — no credit card required →"
}"""

    def _mock_subject_lines(self, prompt_lower: str) -> str:
        if "agency" in prompt_lower or "agency_owner" in prompt_lower:
            return '["One blog. Five campaigns. Zero extra hours.", "Your content is leaving money on the table.", "How top agencies repurpose without the headcount"]'
        elif "startup" in prompt_lower or "startup_marketer" in prompt_lower:
            return '["Stop sending the same email to everyone.", "Your open rates called — they want personalization.", "Segment smarter. Convert faster. Here\'s how."]'
        else:
            return '["You wrote the blog. Let AI do the rest.", "One post → a full week of content.", "Stop starting from scratch every Monday."]'

    def _mock_repurposing_notes(self) -> str:
        return """## Content Repurposing Recommendations

### LinkedIn Posts (3–5 variations)
- **Hook post**: Open with the core statistic from the blog. "Most content teams spend 4+ hours per newsletter. Here's the workflow that cuts it to 20 minutes."
- **Story post**: Narrate the before/after workflow shift described in the article.
- **Carousel post**: Turn the numbered sections into a 5-slide carousel with one key takeaway per slide.

### Twitter/X Thread
Convert the H2 sections into a 6-tweet thread. Lead with the pain point ("You write a great blog post. It gets one share. Then it dies."), end with a CTA linking to the full post.

### Short-Form Video Script (60 seconds)
**Hook (0–5s)**: "Your content is working harder than you think — but only if you repurpose it right."
**Problem (5–20s)**: Describe the one-and-done publishing trap.
**Solution (20–45s)**: Walk through the NovaMind 3-step workflow.
**CTA (45–60s)**: "Link in bio to generate your first campaign free."

### Email Sequence (3-part drip)
1. **Email 1 (Day 0)**: Send the personalized newsletter variant
2. **Email 2 (Day 3)**: Follow up with the repurposing angle — "Did you try this with your own content?"
3. **Email 3 (Day 7)**: Case study or testimonial reinforcing the time-saving value prop

### Podcast Talking Points
Use the blog's structure as a loose script for a 10-minute episode segment. Key topics: the repurposing gap, why personalization matters, the 5-step workflow, getting started.

### Paid Ad Copy
- **Headline A**: "One Blog Post. 100 Personalized Campaigns."
- **Headline B**: "Your Team Writes Once. NovaMind Distributes Everywhere."
- **Body**: Focus on the time savings and ROI angle for agency/startup audiences."""
