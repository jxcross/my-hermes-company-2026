# IBM's open source Granite 4.0 Nano AI models are small enough to run locally directly in your browser

URL: https://venturebeat.com/technology/ibms-open-source-granite-4-0-nano-ai-models-are-small-enough-to-run-locally

Publication date observed: 2025-10-28

Collection date: 2026-08-03

Source type: news

Status: selected

---

In an industry where model size is often seen as a proxy for intelligence, IBM is charting a different course — one that values efficiency over enormity, and accessibility over abstraction.

The 114-year-old tech giant's four new Granite 4.0 Nano models, released today, range from just 350 million to 1.5 billion parameters, a fraction of the size of their server-bound cousins from the likes of OpenAI, Anthropic, and Google.

These models are designed to be highly accessible: the 350M variants can run comfortably on a modern laptop CPU with 8–16GB of RAM, while the 1.5B models typically require a GPU with at least 6–8GB of VRAM for smooth performance — or sufficient system RAM and swap for CPU-only inference. This makes them well-suited for developers building applications on consumer hardware or at the edge, without relying on cloud compute.

In fact, the smallest ones can even run locally on your own web browser, as Joshua Lochner aka Xenova, creator of Transformer.js and a machine learning engineer at Hugging Face, wrote on the social network X.

All the Granite 4.0 Nano models are released under the Apache 2.0 license — perfect for use by researchers and enterprise or indie developers, even for commercial usage.

They are natively compatible with llama.cpp, vLLM, and MLX and are certified under ISO 42001 for responsible AI development — a standard IBM helped pioneer.

These compact models are built not for data centers, but for edge devices, laptops, and local inference, where compute is scarce and latency matters.

The Granite 4.0 Nano family includes four open-source models now available on Hugging Face:

Granite-4.0-H-1B (~1.5B parameters) – Hybrid-SSM architecture

Granite-4.0-H-350M (~350M parameters) – Hybrid-SSM architecture

Granite-4.0-1B – Transformer-based variant, parameter count closer to 2B

Granite-4.0-350M – Transformer-based variant

The H-series models — Granite-4.0-H-1B and H-350M — use a hybrid state space architecture (SSM) that combines efficiency with strong performance, ideal for low-latency edge environments.

Meanwhile, the standard transformer variants — Granite-4.0-1B and 350M — offer broader compatibility with tools like llama.cpp, designed for use cases where hybrid architecture isn’t yet supported.

In benchmark testing, IBM’s new models consistently top the charts in their class. According to data shared on X by David Cox, VP of AI Models at IBM Research:

On IFEval (instruction following), Granite-4.0-H-1B scored 78.5, outperforming Qwen3-1.7B (73.1) and other 1–2B models.

On BFCLv3 (function/tool calling), Granite-4.0-1B led with a score of 54.8, the highest in its size class.

On safety benchmarks (SALAD and AttaQ), the Granite models scored over 90%, surpassing similarly sized competitors.

Overall, the Granite-4.0-1B achieved a leading average benchmark score of 68.3% across general knowledge, math, code, and safety domains.

This performance is especially significant given the hardware constraints these models are designed for.

They require less memory, run faster on CPUs or mobile devices, and don’t need cloud infrastructure or GPU acceleration to deliver usable results.
