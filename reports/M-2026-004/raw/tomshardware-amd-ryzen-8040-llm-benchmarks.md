# AMD claims LLMs run up to 79% faster on Ryzen 8040 CPUs compared to Intel’s newest Core Ultra chips

URL: https://www.tomshardware.com/pc-components/cpus/amd-claims-llms-run-up-to-79-faster-on-ryzen-8040-cpus-compared-to-intels-newest-core-ultra-chips

Publication date observed: 2024-04-05

Collection date: 2026-08-03

Source type: news

Status: selected

---

PC Components

CPUs

AMD claims LLMs run up to 79% faster on Ryzen 8040 CPUs compared to Intel’s newest Core Ultra chips

AMD has a leg up on Intel

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

AMD reports that its older Ryzen mobile 7040 Phoenix and Ryzen mobile 8040 series processors outperform Intel’s Core Ultra Meteor Lake CPUs by up to 79% in various large language models (LLMs). The CPU manufacturer unveiled a plethora of benchmarks against Intel’s Core Ultra 7 155H CPU compared to the Ryzen 7 8740U. Both chips sport hardware-based Neural Processing Units (NPUs).

AMD put together several slides featuring performance results in Mistral 7b, Llama v2 and Mistral Instruct 7B with the two CPUs. In Llama v2 Chat using a Q4 bit size, the Ryzen chip achieved 14% faster tokens per second than the Core Ultra 7 155H. With the same bit size in Mistral Instruct, the Ryzen chips achieved 17% faster tokens per second. In the same LLMs, but looking at Time to First Token for Sample Prompt, AMD’s competitor was 79% faster than the Core Ultra 7 in Llama v2 and 41% faster in Mistral Instruct.

AMD showed another chart of Llama 2 7B Chat using a plethora of different bit sizes, block sizes, and quality levels. On average, the Ryzen 7 7840U was 55% quicker than the Intel counterpart and up to 70% faster in the Q8 results. Despite Q8 being the fastest, AMD recommends a 4-bit K M quantization for running LLMs for real-world use and setting a 5-bit K M for tasks requiring extreme accuracy, like coding.

We are not surprised that AMD is currently winning the AI performance war with Intel. Despite its Ryzen 7040 series architecture having the same level of performance (in TOPS) as Meteor Lake, we discovered late last year that AMD often outperforms Meteor Lake in AI-based workloads. This appears to be a problem with LLM optimization rather than a hardware or driver issue. We noticed AMD notably wins in AI workloads that don’t take advantage of Intel’s OpenVINO framework, which is optimized for Intel products only. OpenVINO appears to be vital to significantly boosting Intel AI performance. Intel’s A770, for instance, gets a tremendous 54% performance improvement purely from OpenVINO optimizations.

Don’t expect this performance behavior to last long. We are only at the beginning of NPU development, after all. If more apps don’t embrace OpenVINO, we expect Intel to switch gears and try a better optimization route—one that will be adopted by more developers. Intel is also getting ready to unleash its next-generation Lunar Lake mobile CPU architecture later this year, which will reportedly feature 3x the AI performance of Meteor Lake (on top of huge IPC improvements for the CPU cores).

Intel's P-core Core 9 273PQE 'Bartlett Lake' CPU beats 14900K by up to 9% in gaming tests

AMD's next-gen 10-core 'Medusa Point' APU shows up on Geekbench again, with its best score yet

AMD's upcoming Zen 6 Medusa Point 10-core APU pops up on Geekbench

For now, AMD’s slides demonstrate that it currently has the edge in NPU performance, especially with its Ryzen 8040 series CPUs, which have even more NPU performance than the Ryzen 7 7840U. But by the end of this year, the tables could turn depending on how successful Intel is with Lunar Lake and its AI optimization plans.

Get Tom's Hardware's best news and in-depth reviews, straight to your inbox.

Aaron Klotz is a contributing writer for Tom’s Hardware, covering news related to computer hardware such as CPUs, and graphics cards.

newtechldtech Who cares ... Apple M3 pro outperform them both... Reply

Eximo And it is the GPU doing the heavy lifting anyway. Is anyone surprised? Reply

Eximo said:And it is the GPU doing the heavy lifting anyway. Is anyone surprised?

Alvar "Miles" Udell Last I saw the Ryzen 8040 was rated for 39TOPS, which is less than the 40TOPS Microsoft requires to be labeled an "AI PC", so does it -really- matter that it's faster (supposedly) than Intel if it's still slower than requirements? Reply

newtechldtech said:Who cares ... Apple M3 pro outperform them both...

scottslayer Wow, I sure am glad AMD gets to self report results again. Reply

Amdlova Amd self claims is the pure truth =]You can belive lol Reply

Amdlova said:Amd self claims is the pure truth =]You can belive lol

Notton said:You mean under-performs both? M3 only does 18 TOPS Core Ultra is max 34 TOPS Ryzen 8040 series is max 38 TOPS Snapdragon X Elite claims to do between 45 to 75 TOPS.

usertests said:You're comparing the Apple M3 Neural Engine (NPU only) to Intel/AMD using CPU+iGPU+NPU all at the same time, so not exactly fair. https://en.wikipedia.org/wiki/Apple_M3#Variants Apparently the iPhone 15 Pro's NPU is almost twice as fast as the M3 variants. Despite the months of hype, Snapdragon X Elite isn't out yet. AMD will also be doing 45+ TOPS out of the Strix Point NPU by the end of the year.

View All 16 Comments
