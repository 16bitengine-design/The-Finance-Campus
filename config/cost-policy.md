# Zero-cost operating policy

The Finance Campus is designed to operate without paid software, paid AI APIs, paid media assets, paid hosting subscriptions, or paid publishing intermediaries.

## Required rules
- Prefer free and open-source software that can be self-hosted or run locally.
- Kokoro TTS is the sole approved narration engine; never call a paid TTS service.
- Generate illustrations, diagrams, captions, and animation from project code and original assets.
- Do not introduce paid LLM, image-generation, stock-media, animation, storage, database, or orchestration APIs.
- Do not require a paid domain, VPS, cloud GPU, or subscription to complete the pipeline.
- Use direct platform publishing APIs only where access is granted, and respect their quotas and terms.
- Store credentials in environment variables or GitHub Secrets; never commit secrets.
- Before adding a dependency or service, document its license, free-use status, resource requirements, and limits.
- If a required step cannot be completed at zero monetary cost, stop and explain the constraint. Never silently activate a paid service or incur charges.
- Add cost/usage guards for free-tier services. Do not assume quotas or access are unlimited or permanent.

## Important operating boundary
The software stack must have a zero software/subscription/API-spend operating path. Execution still consumes computing resources, electricity, internet connectivity, and platform account access. GitHub Actions and social-platform APIs have quotas, eligibility/review requirements, and terms that can change. Do not promise unlimited cloud execution or guaranteed TikTok/YouTube API access. Prefer local/self-hosted execution when hosted free quotas are insufficient.

## Acceptance criteria
A release is not zero-cost compliant if it requires a paid API key, subscription, paid asset, paid hosting plan, paid compute instance, or paid third-party publishing service.