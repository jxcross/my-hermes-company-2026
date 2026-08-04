# Ryzen AI 300 takes big wins over Intel in LLM AI performance — up to 27% faster token generation than Lunar Lake in LM Studio

URL: https://www.tomshardware.com/pc-components/cpus/ryzen-ai-300-takes-big-wins-over-intel-in-llm-ai-performance-up-to-27-percent-faster-token-generation-than-lunar-lake-in-lm-studio

Publication date observed: 2024-10-30

Collection date: 2026-08-03

Source type: news

Status: selected

---

PC Components

CPUs

Ryzen AI 300 takes big wins over Intel in LLM AI performance — up to 27% faster token generation than Lunar Lake in LM Studio

Strix Point runs the tables when it comes to local LLM performance

When you purchase through links on our site, we may earn an affiliate commission. Here’s how it works.

(Image credit: AMD)

Copy link

Facebook

X

Whatsapp

Reddit

Pinterest

Flipboard

Email

AMD's Ryzen AI 300 series of mobile processors beats Intel's mobile competition handily at local large language model (LLM) performance, according to recent in-house testing by AMD. A new blog post from the company's community blog outlines the tests AMD performed to beat Team Blue in AI performance, and how to make the most of the popular LLM program LM Studio for any interested users.

Most of AMD's tests were performed in LM Studio, a desktop app for downloading and hosting LLMs locally. The software, built on the llama.cpp code library, allows for CPU and/or GPU acceleration to power LLMs, and offers other control over the functionality of the models.

Using the 1b and 3b variants of Meta's Llama 3.2, Microsoft Phi 3.1 4k Mini Instruct 3b, Google's Gemma 2 9b, and Mistral's Nemo 2407 12b models, AMD tested laptops powered by AMD's flagship Ryzen AI 9 HX 375 against Intel's midrange Core Ultra 7 258V. The pair of laptops were tested against each other measuring speed in tokens per second and acceleration in the time it took to generate the first token, which roughly match to words printed on-screen per second and the buffer time between when a prompt is submitted and when the LLM begins output.

View Original

As seen in the graphs above, the Ryzen AI 9 HX 375 shows off better performance than the Core Ultra 7 258V across all five tested LLMs, in both speed and time to start outputting text. At its most dominant, AMD's chip represents 27% better speeds than Intel's. It is unknown what laptops were used for the above tests, but AMD was quick to mention that the tested AMD laptop was running slower RAM than the Intel machine—7500 MT/s vs. 8533 MT/s—when faster RAM typically corresponds to better LLM performance.

It should be noted that Intel's Ultra 7 258V processor is not exactly on a fair playing field against the HX 375; the 258V sits in the middle of Intel's 200-series SKUs, with a max turbo speed of 4.8 GHz versus the HX 375's 5.1 GHz. AMD's choice to pit its flagship Strix Point chip against Intel's medium-spec chip reads as a bit unfair, so take the 27% improvement claims with that in mind.

AMD Ryzen AI 5 435G APU goes head-to-head with the Ryzen 5 8600G in early benchmarks

Exploring Apple Silicon’s local AI performance with the Mac Studio and M4 Max

Intel's P-core Core 9 273PQE 'Bartlett Lake' CPU beats 14900K by up to 9% in gaming tests

AMD also showed off LM Studio's GPU acceleration features in tests showing off the HX 375 against itself. While the dedicated NPU in Ryzen AI 300-series laptops is meant to be the driving force in AI tasks, on-demand program-level AI tasks are more prone to use the iGPU. AMD's tests with GPU acceleration using the Vulkan API in LM Studio so heavily favored the HX 375 that AMD did not include Intel's performance numbers with GPU acceleration turned on. With GPU acceleration on, the Ryzen AI 9 HX 375 saw up to 20% faster tk/s than when it ran tasks without GPU acceleration.

With so much current press around computers based on AI performance, vendors are eager to prove that AI matters to the end user. Apps like LM Studio or Intel's AI Playground do their best to offer a user-friendly and foolproof way to harness the latest 1 billion+ iteration LLMs for personal use. Whether large language models and getting the best out of your computer for LLM use matters to most users is another story.

Get Tom's Hardware's best news and in-depth reviews, straight to your inbox.

Sunny Grimm is a contributing writer for Tom's Hardware. He has been building and breaking computers since 2017, serving as the resident youngster at Tom's. From APUs to RGB, Sunny has a handle on all the latest tech news.

TheHerald 10% better performance for 40% more power, bravo I guess. Reply

User of Computers AMD's flubbing the numbers a bit, but I believe AMD's latency numbers. Even when you factor in AMD's usage of their highest-end part versus Intel's u7-class part, and the much higher power envelope that Strix Point operates at, they're probably still ahead by a bit. Reply

rluker5 Hard to find the details from AMD, but it looks like it is a default comparison where it is 28W for AMD vs 17W for Intel. Reply

TheHerald said:10% better performance for 40% more power, bravo I guess.

Pierce2623 said: I know you didn’t mention power draw when you were claiming Raptor Lake was great.

TheHerald said:Of course I was.

Pierce2623 said:So you’re going to sit here with a straight face and pretend that Intel isn’t getting slapped around in consumer CPU performance? They just dropped 10% performance from workloads with lots of random memory accesses like gaming when they weren’t competitive in the first place. Arrow Lake literally only performs well on workloads it’s been optimized for. If it’s not something Intel expects to see in benchmarks, it’ll perform worse than Raptor Lake.

Pierce2623 said:So you’re going to sit here with a straight face and pretend that Intel isn’t getting slapped around in consumer CPU performance?

TheHerald said:Getting slapped around? It beats the competition by a wide margin in the majority of workloads in the majority of segments. See it's posts like yours that make me seem like an Intel fan, just because I have to state the obvious. Especially when you focus on MT performance intel is light years ahead. You do realize that even the latest r7 can't decisively beat in MT intels 2021 i7, right? God forbid we compare it against a 13,14 or 15700k. It will be a massacre.

View All 29 Comments
