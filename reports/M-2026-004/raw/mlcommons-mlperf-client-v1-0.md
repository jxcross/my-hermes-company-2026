# MLCommons Releases MLPerf Client v1.0: A New Standard for AI PC and Client LLM Benchmarking

MLCommons®, the consortium behind the industry-standard MLPerf® benchmarks, today announced the release of MLPerf Client v1.0, a benchmark that sets a new standard for measuring the performance of large language models (LLMs) on PCs and other client-class systems. This release marks a major milestone in the effort to bring standardized, transparent AI performance metrics to the fast-emerging AI PC market.

MLPerf Client v1.0 introduces an expanded set of supported models, including Llama 2 7B Chat, Llama 3.1 8B Instruct, and Phi 3.5 Mini Instruct. It also adds Phi 4 Reasoning 14B as an experimental option to preview the next generation of high-reasoning-capable LLMs. These additions allow the benchmark to reflect real-world use cases across a broader range of model sizes and capabilities.

The benchmark also expands its evaluation scope with new prompt categories. These include structured prompts for code analysis and experimental long-context summarization tests using roughly 4,000- and 8,000-token inputs, representing workloads increasingly relevant to both developers and advanced users.

Hardware and platform support have also expanded significantly. MLPerf Client v1.0 now supports AMD NPUs and GPUs working together via the ONNX Runtime and the Ryzen AI SDK. Intel NPUs and GPUs are supported through OpenVINO. GPUs from AMD, Intel, and NVIDIA are supported across the board through the ONNX Runtime GenAI with DirectML, offering wide compatibility for GPU-equipped systems. Qualcomm Technologies NPUs and CPUs are supported in hybrid operation using Qualcomm Genie and the QAIRT SDK. Also, Apple Mac GPUs are supported through MLX.

Additionally, the benchmark offers early, experimental support for several other acceleration paths. Intel NPUs and GPUs are supported via Microsoft Windows ML using the OpenVINO execution provider. NVIDIA GPUs are supported via llama.cpp with CUDA, and Apple Mac GPUs are supported via llama.cpp with Metal.

For users and developers, MLPerf Client v1.0 provides both command-line and graphical user interfaces. The newly developed GUI offers intuitive, cross-platform benchmarking with key usability enhancements, such as real-time readouts of compute and memory usage, persistent results history, comparison tables across test runs, and CSV exports for offline analysis. The CLI enables easy automation and scripting for regression testing or large-scale evaluations.

MLPerf Client v1.0 is the result of collaboration among major industry stakeholders, including AMD, Intel, Microsoft, NVIDIA, Qualcomm Technologies, and leading PC OEMs. The benchmark is available now as an open and free download from mlcommons.org (https://mlcommons.org), and it will continue to evolve alongside the rapidly growing AI PC ecosystem.

“MLPerf Client v1.0 is a major step forward for benchmarking AI capabilities on consumer systems,” said Ramesh Jaladi, co-chair of the MLPerf Client working group at MLCommons. “It provides a reliable, vendor-neutral standard that OEMs, silicon providers, reviewers, and end users can trust.”

### About MLCommons

MLCommons is an open engineering consortium with a mission to make machine learning better for everyone. The organization produces industry-leading benchmarks, datasets, and best practices that span the full range of ML applications—from massive cloud training to resource-constrained edge devices. Its MLPerf benchmark suite has become the de facto standard for evaluating AI performance.

Learn more at www.mlcommons.org (http://www.mlcommons.org).
