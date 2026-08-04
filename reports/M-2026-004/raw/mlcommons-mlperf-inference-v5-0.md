# MLPerf Inference v5.0 Advances Language Model Capabilities for GenAI

### Introduction

The Large Language Model (LLM) task force was convened to ensure that the MLPerf® Inference v5.0 (https://mlcommons.org/2025/03/mlperf-inference-v5-0-results/) benchmarks address the evolving demands of LLMs and low-latency serving in real-world applications. We focus on three key aspects: first, benchmarking the performance of inferencing platforms on emerging open large LLMs; second, ensuring support for increased context and output sequence lengths required by Retrieval-Augmented Generation (RAG), agentic AI, and advanced reasoning tasks; and third, achieving reasonable response latency to enable efficient and practical deployment in diverse scenarios. These new benchmarks provide a robust framework for evaluating and advancing large-scale LLM inference performance. In MLPerf Inference v5.0, we added two new benchmarks to the suite: Llama 3.1 405B Instruct and Llama 2 Chat 70B.

### Llama 3.1 405B Instruct

The selection of Meta’s Llama 3.1 405B Instruct model reflects its popularity and alignment with industry requirements. Several features of Llama 3.1 405B are particularly notable in this context:

- Long Context Processing: Its benchmark-proven ability to process 128K-token contexts with minimal accuracy degradation addresses the growing need for models to summarize, analyze, and synthesize information from expansive documents while retaining critical details.

- Structured Data Extraction: Llama 3.1 405B exhibits superior performance on needle-in-a-haystack (NIAH) tasks that extract structured data (e.g., key-value pairs) from noisy or unstructured corpora.

- Multi-Source Synthesis: Llama 3.1 405B has demonstrated an exceptional capacity for reconciling ambiguous information across sources, notably in literature analysis where it matches GPT-4’s accuracy.

- Cross-Contextual Reasoning: The model’s design emphasizes linking distant concepts, making it ideal for tasks requiring multi-document synthesis and cross-referencing.

Collectively, these attributes positioned Llama 3.1 405B Instruct as the best candidate, aligning with MLPerf’s mission to benchmark models that power real-world AI systems amid escalating computational and contextual complexity.

### Dataset and task selection

Llama 3.1 405B Instruct has a context window of 128,000 tokens, compared to Llama 2 70B’s 4,096 tokens. This expanded context window enables Llama 3.1 405B to handle longer conversations, process larger documents or code samples, and perform tasks requiring extended context, such as long-form text summarization.

The dataset for Llama 3.1 405B Instruct was curated to evaluate its capabilities in long-context comprehension, retrieval-augmented reasoning, and task-specific optimization. The MLCommons® task force integrated samples from a diverse mix of open datasets:

- LongBench (https://github.com/THUDM/LongBench/blob/main/task.md) (multi-domain long-context tasks)

- LongDataCollections (https://huggingface.co/datasets/togethercomputer/Long-Data-Collections) (comprehension and inference from large text inputs)

- Ruler (https://github.com/hsiehjackson/RULER) (retrieval and reasoning under noise)

- GovReport-Summary (https://huggingface.co/datasets/ccdv/govreport-summarization) (domain-specific summarization)

This mix reflects real-world challenges such as synthesizing government reports, pinpointing critical data in cluttered contexts (needle-in-a-haystack), and executing precise document-based QA. With mean input/output context lengths of 9,400 and 680 tokens respectively, our dataset stresses the model’s ability to retain coherence and accuracy across extended sequences. By leveraging Llama 3.1 405B Instruct’s strengths, we achieved alignment between generated outputs and ground-truth references, validating its proficiency in parsing, contextual linking, and synthesizing insights from complex, lengthy inputs.

The Llama 3.1 405B Instruct benchmark employs task-specific accuracy metrics to evaluate performance across the dataset. For summarization tasks (e.g., GovReport-Summary), we adopted ROUGE-L, a widely recognized NLP metric that measures lexical overlap between generated summaries and ground-truth references. For precision-critical applications like needle-in-a-haystack retrieval and document-based QA, we utilized exact match (EM) scoring to ensure alignment with target answers, minimizing tolerance for errors in key-value extraction or factual responses. The accuracy threshold for closed division submissions is set to 99% of the FP16 reference.

Figure 1. Histogram of input and output (both ground truth and reference) token length distribution of the dataset for Llama 3.1 405B Instruct.

### Performance metrics

The performance metrics chosen for the Llama 3.1 405B Instruct benchmark are the same as those used for the Llama 2 70B benchmark in MLPerf Inference v4.0: token throughput for the offline scenario and Time To First Token (TTFT) + Time Per Output Token (TPOT) for the server scenario. For more information, please refer to the “Measuring performance of the LLM” section of Llama 2 70B: An MLPerf Inference Benchmark for Large Language Models – MLCommons (https://mlcommons.org/2024/03/mlperf-llama2-70b/). To balance the demands of long-context processing with real-world usability, we set a 99th percentile TTFT of 6 seconds and a 99th percentile TPOT of 175ms. These thresholds reflect the computational challenges of deploying large models with long context, while maintaining reasonable responsiveness.

### Reference implementation

The reference implementation for Llama 3.1 405B Instruct leverages vLLM, a fast and versatile library for LLM inference and serving. This choice was driven by vLLM’s robust support for large language models and its wide-ranging compatibility with a diverse range of hardware, including NVIDIA GPUs, AMD CPUs and GPUs, Intel CPUs, Gaudi accelerators, TPUs etc, making it an ideal choice for deploying Llama 3.1-405B across different computing environments.

For readers interested in running the model themselves, we encourage them to follow the reference implementation (https://github.com/mlcommons/inference/tree/master/language/llama3.1-405b), which contains code and instructions on how to run the entire benchmark end-to-end.

### Llama 2 Chat 70B Interactive Benchmark

The Llama 2 70B benchmark (https://mlcommons.org/2024/03/mlperf-llama2-70b/) was introduced in MLPerf Inference v4.0 and has quickly become one of the most popular benchmarks in the suite. Server latencies were set, according to the usage models and hardware capabilities of the time, at 2s TTFT and 200 ms TPOT. As adoption of generative AI has skyrocketed, state-of-the-art model serving has advanced and use cases such as reasoning models and agents are taking advantage of ever lower latencies. In an effort to set target latencies that are more representative of current requirements, we performed a new analysis of industry research, user surveys, and performance data from leading platforms like ChatGPT and Perplexity AI in late 2024. Our findings indicated that a 50th percentile token generation rate of 20–50 tokens per second (TPOT of 20-50ms) is critical for seamless user experience. To prioritize reliability under peak demand, MLPerf adopts a stricter 99th percentile threshold of 25 tokens/second (TPOT of 40ms), ensuring consistent responsiveness even during high-load scenarios. Additionally, we set a 99th percentile TTFT limit of 450ms to minimize initial latency, aligning with user expectations for near-instantaneous query response.

We continued to utilize the OpenOrca dataset and ROUGE accuracy metrics due to their relevance and proximity to chatbot tasks, which align well with the dataset’s diverse conversational scenarios and high-quality annotations.

### Conclusion

The usage of LLMs is expanding rapidly across a diversity of application domains, with a demand for LLMs at different scales and response latencies. MLPerf is keeping pace with these trends by introducing a very large scale 405B benchmark and a low latency 70B interactive benchmark in the new MLPerf Inference v5.0 release. In this post, we shared the motivation and the complexities involved in the choice of model, task, dataset, accuracy, performance, and verification of such LLM benchmarks. We believe the design choices of this benchmark objectively address most of the critical deployment decisions faced by practitioners while delivering important performance insights to customers. With the addition of these benchmarks to MLPerf Inference, we now offer a comprehensive suite of language benchmarks at all scales (7B to 405B), diversity of architectures (like MoE) and deployment scenarios (datacenter, edge, or low latency).

Details of the MLPerf Inference Llama 3.1 405B Instruct benchmark and reference implementation can be found here (https://github.com/mlcommons/inference/tree/master/language/llama3.1-405b).

For more information on the Llama 2 70B benchmark, please refer to the “Choosing a task and a dataset for the LLM” section of Llama 2 70B: An MLPerf Inference Benchmark for Large Language Models – MLCommons (https://mlcommons.org/2024/03/mlperf-llama2-70b/).
