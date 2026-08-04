

<!DOCTYPE html>
<html lang="en">
  	<head>
        <meta charset="utf-8" />
        
        <title>
            
            On-device small language models with multimodality, RAG, and Function Calling
            
            
            - Google Developers Blog
            
        </title>
        <meta property="og:title" content="On-device small language models with multimodality, RAG, and Function Calling- Google Developers Blog" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        
	<meta name="description" content="Develop next-gen on-device apps with Google AI Edge&#x27;s generative AI, new Gemma 3 models, broader model support, and Function Calling to enhance capabilities on Android, iOS, and Web" />
  <meta content="summary_large_image" name="twitter:card"/>
  <meta content="Google for Developers Blog - News about Web, Mobile, AI and Cloud" property="twitter:title"/>
  <meta property="og:title" content="On-device small language models with multimodality, RAG, and Function Calling" />
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [{
      "@type": "ListItem",
      "position": 1,
      "name": "Google for Developers Blog",
      "item": "https://developers.googleblog.com/"
    },{
      "@type": "ListItem",
      "position": 2,
      "name": "On-device small language models with multimodality, RAG, and Function Calling",
      "item": "https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling/"
    }]
  }
  </script>
  <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "On-device small language models with multimodality, RAG, and Function Calling",
      "description": "Google AI Edge advancements, include new Gemma 3 models, broader model support, and features like on-device RAG and Function Calling to enhance on-device generative AI capabilities.",
      "image": "https://storage.googleapis.com/gweb-developer-goog-blog-assets/images/O25-BHero-AI-4-Meta.2e16d0ba.fill-800x400.png",
      "datePublished": "2025-05-20",
      "author": [
        
        
          { "@type": "Person", "name": "Mark Sherwood", "url": "/en/search/?author=Mark+Sherwood" },
        
          { "@type": "Person", "name": "Matthew Chan", "url": "/en/search/?author=Matthew+Chan" },
        
          { "@type": "Person", "name": "Marissa Ikonomidis", "url": "/en/search/?author=Marissa+Ikonomidis" },
        
          { "@type": "Person", "name": "Milen Ferev", "url": "/en/search/?author=Milen+Ferev" }
        
        
      ]
    }
  </script>
  
  <meta content="https://storage.googleapis.com/gweb-developer-goog-blog-assets/images/O25-BHero-AI-4-Meta.2e16d0ba.fill-1200x600.png" property="og:image"/>
  


        
        

        <!-- Google Tag Manager -->
        <script type="text/javascript" nonce="Glb5I5IK697ZB8sm2v3WkA==" src="https://storage.googleapis.com/gweb-developer-goog-blog-cms-assets/site/20260731-000318/js/analytics.js"></script>
        <!-- End Google Tag Manager -->

        
        <link href="//www.gstatic.com/glue/v27_1/glue.min.css" rel="stylesheet">
        <link rel="stylesheet" type="text/css" href="https://storage.googleapis.com/gweb-developer-goog-blog-cms-assets/site/20260731-000318/css/dgc_blog.css">
        <link rel="icon" href="https://storage.googleapis.com/gweb-developer-goog-blog-assets/meta/favicon.ico" type="image/x-icon">
        <link rel="apple-touch-icon" href="https://storage.googleapis.com/gweb-developer-goog-blog-assets/meta/apple-touch-icon.png">

        
				<link rel="preconnect" href="https://fonts.googleapis.com">
				<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
				<link rel="preload" href="https://fonts.googleapis.com/css2?family=Product+Sans&family=Google+Sans+Display:ital@0;1&family=Google+Sans:ital,wght@0,400;0,500;0,700;1,400;1,500;1,700&family=Google+Sans+Text:ital,wght@0,400;0,500;0,700;1,400;1,500;1,700&display=swap" as="style">
				<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Product+Sans&family=Google+Sans+Display:ital@0;1&family=Google+Sans:ital,wght@0,400;0,500;0,700;1,400;1,500;1,700&family=Google+Sans+Text:ital,wght@0,400;0,500;0,700;1,400;1,500;1,700&display=swap">
        <link href="https://fonts.googleapis.com/css2?family=Google+Sans+Code:ital,wght,MONO@0,300..800,1;1,300..800,1&amp;family=Google+Sans+Flex:opsz,wght@6..144,1..1000&amp;display=swap" rel="stylesheet" data-page-link="">
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@400&display=swap">

        
        <link href="https://www.gstatic.com/glue/cookienotificationbar/cookienotificationbar.min.css" rel="stylesheet">

        
  <link
    rel="stylesheet"
    type="text/css"
    href="https://storage.googleapis.com/gweb-developer-goog-blog-cms-assets/site/20260731-000318/css/blog_detail.css"
  />
  <link type="text/css" href="https://storage.googleapis.com/gweb-developer-goog-blog-cms-assets/site/20260731-000318/css/prism.css" rel="stylesheet" />

    </head>

    <body id="main-content" class="glue-body ">
        <!-- Google Tag Manager (noscript) -->
        <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-WVTLDSL "
        height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
        <!-- End Google Tag Manager (noscript) -->

        

				
        

<!-- HTML -->
<header class="dgc-header">
  <div class="dgc-header-inner">
    <button class="hamburger" aria-haspopup="true" aria-expanded="false" aria-label="Open Menu">
      <svg role="presentation" aria-hidden="true" class="glue-icon">
        <use href="/glue-icon/#menu"></use>
      </svg>
    </button>
    <div class="product-name-wrapper">
      <a href="https://developers.google.com/" class="site-logo-link" data-label="Site logo">
        <img src="https://storage.googleapis.com/gweb-developer-goog-blog-cms-assets/site/20260731-000318/images/g-dev.svg" class="site-logo" alt="Google for Developers">
      </a>
    </div>
    <div class="desktop-nav-wrapper">
      <div class="upper-tabs-wrapper">
        <div class="upper-tabs">
          <nav class="tabs" aria-label="Upper Tabs">
            <div class="tab">
              <a
                href="//developers.google.com/community"
                class="top-nav-title">
                Community/Events
              </a>
            </div>
            <div class="tab">
              <a
                href="//developers.google.com/solutions/catalog"
                class="top-nav-title">
                Learn
              </a>
            </div>
            <div class="tab">
              <a
                href="//developers.googleblog.com"
                class="top-nav-title">
                Blog
              </a>
            </div>
            <div class="tab">
              <a
                href="https://www.youtube.com/user/GoogleDevelopers"
                class="top-nav-title">
                YouTube
              </a>
            </div>
          </nav>
        </div>
      </div>
    </div>
  </div>
  <div class="dgc-header-search">
    <div class="search-wrapper glue-page">
      <div class="glue-grid">
        <form id="search-form"  action="/en/search/" method="get" class="search-content glue-grid__col glue-grid__col--span-4-sm glue-grid__col--span-9-md glue-grid__col--span-7-lg">
          <div class="search-input-wrapper">
            <svg role="presentation" aria-hidden="true" class="glue-icon search-icon">
              <use href="/glue-icon/#search"></use>
            </svg>
            <input
              type="text"
              name="query"
              
              placeholder="Search all articles..."
              aria-label="Search"
              class="search-input-field"
            />
          </div>
          <button class="glue-button glue-button--high-emphasis">
            Search
          </button>
        </form>
      </div>
    </div>
  </div>
</header>

<div class="mobile-drawer" top-level-nav>
  <nav class="nav-content" aria-label="Side menu">
    <div class="mobile-header">
      <button class="nav-close-btn nav-btn" aria-label="Close navigation">
        <svg role="presentation" aria-hidden="true" class="glue-icon">
          <use href="/glue-icon/#close"></use>
        </svg>
      </button>
      <button class="nav-back-btn nav-btn hidden" aria-label="Back to Menu">
        <svg role="presentation" aria-hidden="true" class="glue-icon">
          <use href="/glue-icon/#arrow-back"></use>
        </svg>
      </button>
      <div class="product-name-wrapper">
        <a href="https://developers.google.com/" class="site-logo-link" data-label="Site logo">
          <img src="https://storage.googleapis.com/gweb-developer-goog-blog-cms-assets/site/20260731-000318/images/g-dev.svg" class="site-logo" alt="Google for Developers">
        </a>
      </div>
    </div>
    <div class="nav-wrapper">
      <div class="mobile-nav-top">
        <ul class="nav-list">
          <li class="nav-item">
            <a href="//developers.google.com/community" class="nav-title" data-label="Tab: Community/Events">
              <span class="nav-text" tooltip="">
                Community/Events
             </span>
            </a>
          </li>
          <li class="nav-item">
            <a href="//developers.google.com/solutions/catalog" class="nav-title" data-label="Tab: Learn">
              <span class="nav-text" tooltip="">
                Learn
             </span>
            </a>
          </li>
          <li class="nav-item">
            <a href="//developers.googleblog.com" class="nav-title" data-label="Tab: Blog">
              <span class="nav-text" tooltip="">
                Blog
             </span>
            </a>
          </li>
          <li class="nav-item">
            <a href="https://www.youtube.com/user/GoogleDevelopers" class="nav-title" data-label="Tab: YouTube">
              <span class="nav-text" tooltip="">
                YouTube
             </span>
            </a>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</div>

<div class="backdrop"></div>

        
  <div class="blog-detail-container">

    
      <section class="tags-container glue-page glue-spacer-5-top">
        <div class="glue-eyebrow"><a href="/en/search/?product_categories=AI+Edge">AI Edge</a></div>
      </section>
    

    <section class="heading-container glue-page  glue-spacer-1-top">
      <h1 class="glue-headline glue-headline--headline-1">On-device small language models with multimodality, RAG, and Function Calling</h1>
    </section>

    <section class="summary-container glue-page glue-spacer-4-top">
      <div class="date-time">
        <div class="published-date glue-font-weight-medium">MAY 20, 2025</div>
      </div>
    </section>

    <section class="glue-page glue-grid glue-spacer-1-top">

      <section class="author-container glue-grid__col glue-grid__col--span-4-sm glue-grid__col--span-10-md">
      
        
          <div class="author-obj">
            <a class="glue-font-weight-medium" href="/en/search/?author=Mark+Sherwood">Mark Sherwood</a>
            
              <span class="glue-font-weight-medium role">Senior Product Manager</span>
            
            
          </div>
        
          <div class="author-obj">
            <a class="glue-font-weight-medium" href="/en/search/?author=Matthew+Chan">Matthew Chan</a>
            
              <span class="glue-font-weight-medium role">Staff Software Engineer</span>
            
            
          </div>
        
          <div class="author-obj">
            <a class="glue-font-weight-medium" href="/en/search/?author=Marissa+Ikonomidis">Marissa Ikonomidis</a>
            
              <span class="glue-font-weight-medium role">Staff Software Engineer</span>
            
            
          </div>
        
          <div class="author-obj">
            <a class="glue-font-weight-medium" href="/en/search/?author=Milen+Ferev">Milen Ferev</a>
            
              <span class="glue-font-weight-medium role">Software Engineer</span>
            
            
          </div>
        

      
      </section>
      <section class="social-container glue-grid__col glue-grid__col--span-4-sm glue-grid__col--span-2-md">
        <button id="social-button" class="glue-button glue-button--low-emphasis glue-button--icon" aria-haspopup="true" aria-expanded="false">
          <svg role="presentation" aria-hidden="true" class="glue-icon">
            <use href="/glue-icon/#share"></use>
          </svg>
          <span>Share</span>
        </button>
        <ul id="social-menu" class="glue-elevation-level-1" role="menu" aria-labelledby="social-button">
          <li>
            <a href="https://www.facebook.com/sharer/sharer.php?u={url}"
                title="Share on Facebook" target="_blank" rel="noopener">
              <svg role="presentation" aria-hidden="true"
                  class="glue-icon glue-icon--social glue-icon--32px">
                <use href="/glue-icon/#post-facebook"></use>
              </svg>
              <span>Facebook</span>
            </a>
          </li>
          <li>
            <a href="https://twitter.com/intent/tweet?text={url}"
                title="Share on Twitter" target="_blank" rel="noopener">
              <svg role="presentation" aria-hidden="true"
                  class="glue-icon glue-icon--social glue-icon--32px">
                <use href="/glue-icon/#twitter-x"></use>
              </svg>
              <span>Twitter</span>
            </a>
          </li>
          <li>
            <a href="https://www.linkedin.com/shareArticle?url={url}&amp;mini=true" title="Share on LinkedIn" target="_blank" rel="noopener">
              <svg role="presentation" aria-hidden="true"
                  class="glue-icon glue-icon--social glue-icon--32px">
                <use href="/glue-icon/#post-linkedin"></use>
              </svg>
              <span>LinkedIn</span>
            </a>
          </li>
          <li>
            <a href="mailto:name@example.com?subject=Check%20out%20this%20site&body=Check%20out%20{url}" title="Send via Email">
              <svg role="presentation" aria-hidden="true"
                  class="glue-icon glue-icon--social glue-icon--32px">
                <use href="/glue-icon/#email"></use>
              </svg>
              <span>Mail</span>
            </a>
          </li>
          <li>
            <a href="#" title="Get shareable link" data-link="" data-copy-text="Copy Link" data-copied-text="Copied!">
              <svg role="presentation" aria-hidden="true"
                  class="glue-icon glue-icon--social glue-icon--32px">
                <use href="/glue-icon/#link"></use>
              </svg>
              <span></span>
            </a>
          </li>
        </ul>
      </section>
    </section>

    
    <section class="blocks-container glue-page glue-spacer-3-top">
      <div class="block">
          

<img
    class="banner-image"
    src="https://storage.googleapis.com/gweb-developer-goog-blog-assets/images/O25-BHero-AI-4.original.png"
    alt="On-Device Small Language Models with Multimodality, RAG, and Function Calling"
/>  <div class="inner-block-content rich-content">
    <p data-block-key="1hui9">Last year <a href="https://ai.google.dev/edge">Google AI Edge</a> introduced support for <a href="https://developers.googleblog.com/en/large-language-models-on-device-with-mediapipe-and-tensorflow-lite/">on-device small language models</a> (SLMs) with four initial models on Android, iOS, and Web. Today, we are excited to expand support to over a dozen models including the new <a href="https://blog.google/technology/developers/gemma-3/">Gemma 3</a> and Gemma 3n models, hosted on our new LiteRT Hugging Face <a href="https://huggingface.co/litert-community">community</a>.</p><p data-block-key="4bka"><a href="https://developers.googleblog.com/en/introducing-gemma-3n">Gemma 3n</a>, available via Google AI Edge as an early preview, is Gemma’s first multimodal on-device small language model supporting text, image, video, and audio inputs. Paired with our new <a href="https://ai.google.dev/edge/mediapipe/solutions/genai/rag">Retrieval Augmented Generation (RAG)</a> and <a href="https://ai.google.dev/edge/mediapipe/solutions/genai/function_calling">Function Calling</a> libraries, you have everything you need to prototype and build transformative AI features fully on the edge.</p>
</div>   

<div class="inner-block-content video-block">
    
        <video  autoplay="" loop="" muted="" playsinline="" poster="https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/wagtailvideo-9q9c9i_s_thumb.jpg">
<source src='https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/io25-function-calling-demo-gif.mp4' type='video/mp4'>
<p>Sorry, your browser doesn't support playback for this video</p>

</video>
    
    
        
            <div class="video-description">Let users control apps with on-device SLMs and our new function calling library</div>
        
    
</div>  <div class="inner-block-content rich-content">
    <h2 data-block-key="67ny9" id="broader-model-support">Broader model support</h2><p data-block-key="a7bro">You can find our growing list of models to choose from in the <a href="https://huggingface.co/litert-community">LiteRT Hugging Face Community</a>. Download any of these models and easily run them on-device with just a few lines of code. The models are fully optimized and converted for mobile and web. Full instructions on how to run these models can be found in our <a href="https://ai.google.dev/edge/mediapipe/solutions/genai/llm_inference">documentation</a> and on each model card on Hugging Face.</p><p data-block-key="ajb9">To customize any of these models, you finetune the base model and then <a href="https://github.com/google-ai-edge/ai-edge-torch/tree/main/ai_edge_torch/generative">convert</a> and <a href="https://github.com/google-ai-edge/ai-edge-quantizer">quantize</a> the model using the appropriate AI Edge libraries. We have a <a href="https://colab.sandbox.google.com/github/google-ai-edge/mediapipe-samples/blob/main/codelabs/litert_inference/Gemma3_1b_fine_tune.ipynb">Colab</a> showing every step you need to fine-tune and then convert Gemma 3 1B.</p><p data-block-key="6so3i">With the latest release of our <a href="https://github.com/google-ai-edge/ai-edge-torch/tree/main/ai_edge_torch/generative/quantize">quantization tools</a>, we have new quantization schemes that allow for much higher quality int4 post training quantization. Compared to bf16, the default data type for many models, int4 quantization can reduce the size of language models by a factor of 2.5-4X while significantly decreasing latency and peak memory consumption.</p><h2 data-block-key="t1y28" id="gemma-3-1b-and-gemma-3n"><b><br/></b>Gemma 3 1B &amp; Gemma 3n</h2><p data-block-key="6t02e">Earlier this year, we <a href="https://developers.googleblog.com/en/gemma-3-on-mobile-and-web-with-google-ai-edge/">introduced Gemma 3 1B</a>. At only 529MB, this model can run up to 2,585 tokens per second pre-fill on the mobile GPU, allowing it to process up to a page of content in under a second. Gemma 3 1B’s small footprint allows it to support a wide range of devices and limits the size of files an end user would need to download in their application.</p><p data-block-key="2e1re">Today, we are thrilled to add an early preview of Gemma 3n to our collection of supported models. The <a href="https://huggingface.co/google/gemma-3n-E2B-it-litert-preview">2B</a> and <a href="https://huggingface.co/google/gemma-3n-E4B-it-litert-preview">4B</a> parameter variants will both support native text, image, video, and audio inputs. The text and image modalities are available on Hugging Face with audio to follow shortly.</p>
</div>   

<div class="inner-block-content video-block">
    
        <video  autoplay="" loop="" muted="" playsinline="" poster="https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/wagtailvideo-yowt4luo_thumb.jpg">
<source src='https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/gemma-3n-4b-on-device-ml-google-io.mp4' type='video/mp4'>
<p>Sorry, your browser doesn't support playback for this video</p>

</video>
    
    
        
            <div class="video-description">Gemma 3n analyzing images fully on-device</div>
        
    
</div>  <div class="inner-block-content rich-content">
    <p data-block-key="1hui9">Gemma 3n is great for enterprise use cases where developers have the full resources of the device available to them, allowing for larger models on mobile. Field technicians with no service could snap a photo of a part and ask a question. Workers in a warehouse or a kitchen could update inventory via voice while their hands were full.</p><h2 data-block-key="psm1v" id="bringing-context-to-conversations:-on-device-retrieval-augmented-generation-(rag)"><br/>Bringing context to conversations: On-device Retrieval Augmented Generation (RAG)</h2><p data-block-key="5tunu">One of the most exciting new capabilities we&#x27;re bringing to Google AI Edge is robust support for on-device Retrieval Augmented Generation (RAG). RAG allows you to augment your small language model with data specific to your application, without the need for fine-tuning. From 1000 pages of information or 1000 photos, RAG can help find just the most relevant few pieces of data to feed to your model.</p><p data-block-key="6las2">The <a href="https://ai.google.dev/edge/mediapipe/solutions/genai/rag">AI Edge RAG</a> library works with any of our supported small language models. Furthermore it offers the flexibility to change any part of the RAG pipeline enabling custom databases, chunking methods, and retrieval functions. The AI Edge RAG library is available today on Android with more platforms to follow. This means your on-device generative AI applications can now be grounded in specific, user-relevant information, unlocking a new class of intelligent features.</p><h2 data-block-key="su1qx" id="enabling-action:-on-device-function-calling"><b><br/></b>Enabling action: On-device function calling</h2><p data-block-key="4ltii">To make on-device language models truly interactive, we&#x27;re introducing on-device function calling. The <a href="https://github.com/google-ai-edge/ai-edge-apis/tree/main/local_agents/function_calling">AI Edge Function Calling</a> library is available on Android today with more platforms to follow. The library includes all of the utilities you need to integrate with an on-device language model, register your application functions, parse the response, and call your functions. Check out the <a href="https://ai.google.dev/edge/mediapipe/solutions/genai/function_calling">documentation</a> to try it yourself.</p><p data-block-key="cl3hk">This powerful feature enables your language models to intelligently decide when to call predefined functions or APIs within your application. For example, in our <a href="https://github.com/google-ai-edge/ai-edge-apis/tree/main/examples/function_calling/healthcare_form_demo">sample app</a>, we demonstrate how function calling can be used to fill out a form through natural language. In the context of a medical app asking for pre-appointment patient history, the user dictates their personal information. With our function calling library and an on-device language model, the app converts the voice to text, extracts the relevant information, and then calls application specific functions to fill out the individual fields.</p><p data-block-key="dl8r0">The function calling library can also be paired with our python<a href="https://pypi.org/project/ai-edge-tool-simulation/"> tool simulation library</a>. The tool simulation library aids you in creating a custom language model for your specific functions through synthetic data generation and evaluation, increasing the accuracy of function calling on-device.</p><h2 data-block-key="uwfzi" id="what&#x27;s-next"><b><br/></b>What’s next</h2><p data-block-key="aeonv">We will continue to support the latest and greatest small language models on the edge, including new modalities. Keep an eye on our <a href="https://huggingface.co/litert-community">LiteRT Hugging Face Community</a> for new model releases. Our RAG and function calling libraries will continue to expand in functionality and supported platforms.</p><p data-block-key="airm9">For more Google AI Edge news, read about the <a href="https://developers.googleblog.com/en/litert-maximum-performance-simplified">new LiteRT APIs</a> and our new <a href="https://cloud.google.com/blog/products/ai-machine-learning/ai-edge-portal-brings-on-device-ml-testing-at-scale">AI Edge Portal</a> service for broad coverage on-device benchmarking and evals.</p><p data-block-key="9e8qi">Explore this announcement and all Google I/O 2025 updates on <a href="https://io.google/2025/?utm_source=blogpost&amp;utm_medium=pr&amp;utm_campaign=event&amp;utm_content=">io.google</a> starting May 22.<br/></p><hr/><h3 data-block-key="e86cq" id="acknowledgements"><b>Acknowledgements</b></h3><p data-block-key="820oo"><sup>We also want to thank the following Googlers for their support in these launches: Advait Jain, Akshat Sharma, Alan Kelly, Andrei Kulik, Byungchul Kim, Chunlei Niu, Chun-nien Chan, Chuo-Ling Chang, Claudio Basile, Cormac Brick, Ekaterina Ignasheva, Eric Yang, Fengwu Yao, Frank Ban, Gerardo Carranza, Grant Jensen, Haoliang Zhang, Henry Wang, Ho Ko, Ivan Grishchenko, Jae Yoo, Jingjiang Li, Jiuqiang Tang, Juhyun Lee, Jun Jiang, Kris Tonthat, Lin Chen, Lu Wang, Marissa Ikonomidis, Matthew Soulanille, Matthias Grundmann, Milen Ferev, Mogan Shieh, Mohammadreza Heydary, Na Li, Pauline Sho, Pedro Gonnet, Ping Yu, Pulkit Bhuwalka, Quentin Khan, Ram Iyengar, Raman Sarokin, Rishika Sinha, Ronghui Zhu, Sachin Kotwani, Sebastian Schmidt, Steven Toribio, Suleman Shahid, T.J. Alumbaugh, Tenghui Zhu, Terry (Woncheol) Heo, Tyler Mullen, Vitalii Dziuba, Wai Hon Law, Weiyi Wang, Xu Chen, Yi-Chun Kuo, Yishuang Pang, Youchuan Hu, Yu-hui Chen, Zichuan Wei</sup></p>
</div> 
      </div>
    </section>
    

    <section class="navigation-container glue-page glue-spacer-6-top">
      <div class="posted-in-section">
        <div class="posted-in-section__heading">
          <span class="glue-caption">
            posted in:
          </span>
        </div>
        <div class="posted-in-section__tags">
          <ul>
              
                  <li>
                      <a href="/en/search/?product_categories=AI+Edge" class="glue-caption">AI Edge</a>
                  </li>
              
                  <li>
                      <a href="/en/search/?technology_categories=Mobile" class="glue-caption">Mobile</a>
                  </li>
              
                  <li>
                      <a href="/en/search/?technology_categories=Web" class="glue-caption">Web</a>
                  </li>
              
                  <li>
                      <a href="/en/search/?technology_categories=AI" class="glue-caption">AI</a>
                  </li>
              
                  <li>
                      <a href="/en/search/?content_type_categories=Announcements" class="glue-caption">Announcements</a>
                  </li>
              
                  <li>
                      <a href="/en/search/?content_type_categories=Industry+Trends" class="glue-caption">Industry Trends</a>
                  </li>
              
              
                  <li>
                      <a href="/en/search/?tag=Function Calling" class="glue-caption">Function Calling</a>
                  </li>
              
                  <li>
                      <a href="/en/search/?tag=RAG" class="glue-caption">RAG</a>
                  </li>
              
                  <li>
                      <a href="/en/search/?tag=Android" class="glue-caption">Android</a>
                  </li>
              
                  <li>
                      <a href="/en/search/?tag=Generative AI" class="glue-caption">Generative AI</a>
                  </li>
              
                  <li>
                      <a href="/en/search/?tag=Gemma 3" class="glue-caption">Gemma 3</a>
                  </li>
              
                  <li>
                      <a href="/en/search/?tag=Mobile App Development" class="glue-caption">Mobile App Development</a>
                  </li>
              
                  <li>
                      <a href="/en/search/?tag=Google I/O 2025" class="glue-caption">Google I/O 2025</a>
                  </li>
              
                  <li>
                      <a href="/en/search/?tag=on-device AI" class="glue-caption">on-device AI</a>
                  </li>
              
                  <li>
                      <a href="/en/search/?tag=iOS" class="glue-caption">iOS</a>
                  </li>
              
          </ul>
      </div>
      </div>
      <div class="buttons-section">
        <div class="buttons-section__left">
          <a href="/en/build-train-recommender-system-keras-jax/" class="glue-button--icon glue-elevation-level-1 " aria-label="Previous">
            <svg role="presentation" aria-hidden="true" class="glue-icon">
              <use href="/glue-icon/#chevron-left"></use>
            </svg>
          </a>
          <span class="caption ">Previous</span>
        </div>
        <div class="buttons-section__right">
          <span class="caption ">Next</span>
          <a href="/en/explore-the-latest-updates-google-wallet-io-25/" class="glue-button--icon glue-elevation-level-1 "  aria-label="Next">
            <svg role="presentation" aria-hidden="true" class="glue-icon">
              <use href="/glue-icon/#chevron-right"></use>
            </svg>
          </a>
        </div>
      </div>
    </section>

    
    <section class="related-posts-container glue-page glue-spacer-6-top glue-spacer-3-bottom">
      <span class="glue-headline glue-headline--headline-3">Related Posts</span>
      <div class="related-posts-container__carousel glue-page glue-spacer-5-top">
        <div class="glue-carousel glue-carousel--cards glue-carousel-related-posts" aria-label="Related Posts">
          <!-- Previous -->
          <button class="glue-carousel__button glue-carousel__button--prev"
              aria-label="Go to the previous slide">
            <svg role="presentation" aria-hidden="true" class="glue-icon glue-icon--32px">
              <use href="/glue-icon/#chevron-left"></use>
            </svg>
          </button>
          <!-- Next -->
          <button class="glue-carousel__button glue-carousel__button--next"
              aria-label="Go to the next slide">
            <svg role="presentation" aria-hidden="true" class="glue-icon glue-icon--32px">
              <use href="/glue-icon/#chevron-right"></use>
            </svg>
          </button>
          <!-- List -->
          <div class="glue-carousel__viewport">
            <div class="glue-carousel__list">
              
                <a class="glue-card glue-carousel__item" href="/en/litert-maximum-performance-simplified/">
                  <div aria-label="LiteRT: Maximum performance, simplified" class="glue-card__inner">
                    <picture class="glue-card__asset">
                      <img alt="LiteRT: Maximum performance, simplified" src="https://storage.googleapis.com/gweb-developer-goog-blog-assets/images/O25-BHero-AI-3-Meta.2e16d0ba.fill-800x400.png">
                    </picture>
                    <div class="glue-card__content">
                      <div class="glue-card__tags glue-spacer-2-top">
                        
                            
                            <span class="glue-label">AI Edge</span>
                            
                            
                            <span class="glue-label">Mobile</span>
                            
                            <span class="glue-label">AI</span>
                            
                            
                            <span class="glue-label">How-To Guides</span>
                            
                            <span class="glue-label">Announcements</span>
                            
                        
                      </div>
                      <p class="glue-headline glue-headline--headline-5">LiteRT: Maximum performance, simplified</p>
                      <div class="glue-card__cta-custom glue-spacer-3-top">
                        <span class="glue-cta">MAY 20, 2025</span>
                        <svg aria-hidden="true" class="glue-icon glue-icon--24px" role="presentation">
                          <use href="/glue-icon/#arrow-forward"></use>
                        </svg>
                      </div>
                    </div>
                  </div>
                </a>
              
                <a class="glue-card glue-carousel__item" href="/en/bridging-the-domain-gap-ai-race-coach-built-with-antigravity-and-gemini/">
                  <div aria-label="Bridging the Domain Gap: AI Race Coach built with Antigravity and Gemini" class="glue-card__inner">
                    <picture class="glue-card__asset">
                      <img alt="Bridging the Domain Gap: AI Race Coach built with Antigravity and Gemini" src="https://storage.googleapis.com/gweb-developer-goog-blog-assets/images/GGBM3681_1.2e16d0ba.fill-800x400.jpg">
                    </picture>
                    <div class="glue-card__content">
                      <div class="glue-card__tags glue-spacer-2-top">
                        
                            
                            
                            <span class="glue-label">Mobile</span>
                            
                            <span class="glue-label">Web</span>
                            
                            
                            <span class="glue-label">Case Studies</span>
                            
                            <span class="glue-label">Community</span>
                            
                        
                      </div>
                      <p class="glue-headline glue-headline--headline-5">Bridging the Domain Gap: AI Race Coach built with Antigravity and Gemini</p>
                      <div class="glue-card__cta-custom glue-spacer-3-top">
                        <span class="glue-cta">JULY 8, 2026</span>
                        <svg aria-hidden="true" class="glue-icon glue-icon--24px" role="presentation">
                          <use href="/glue-icon/#arrow-forward"></use>
                        </svg>
                      </div>
                    </div>
                  </div>
                </a>
              
                <a class="glue-card glue-carousel__item" href="/en/run-ray-on-tpu-part-2-ray-ai-libraries/">
                  <div aria-label="Run Ray on TPU, Part 2: Ray AI libraries" class="glue-card__inner">
                    <picture class="glue-card__asset">
                      <img alt="Run Ray on TPU, Part 2: Ray AI libraries" src="https://storage.googleapis.com/gweb-developer-goog-blog-assets/images/header.2e16d0ba.fill-800x400_pp6EXuC.png">
                    </picture>
                    <div class="glue-card__content">
                      <div class="glue-card__tags glue-spacer-2-top">
                        
                            
                            
                            <span class="glue-label">AI</span>
                            
                            
                            <span class="glue-label">Case Studies</span>
                            
                            <span class="glue-label">How-To Guides</span>
                            
                        
                      </div>
                      <p class="glue-headline glue-headline--headline-5">Run Ray on TPU, Part 2: Ray AI libraries</p>
                      <div class="glue-card__cta-custom glue-spacer-3-top">
                        <span class="glue-cta">JULY 24, 2026</span>
                        <svg aria-hidden="true" class="glue-icon glue-icon--24px" role="presentation">
                          <use href="/glue-icon/#arrow-forward"></use>
                        </svg>
                      </div>
                    </div>
                  </div>
                </a>
              
                <a class="glue-card glue-carousel__item" href="/en/agent-and-model-evaluations-in-gemini-enterprise-agent-platform-are-now-ga/">
                  <div aria-label="Agent and Model Evaluations in Gemini Enterprise Agent Platform are now GA" class="glue-card__inner">
                    <picture class="glue-card__asset">
                      <img alt="Agent and Model Evaluations in Gemini Enterprise Agent Platform are now GA" src="https://storage.googleapis.com/gweb-developer-goog-blog-assets/images/unnamed_8.2e16d0ba.fill-800x400.png">
                    </picture>
                    <div class="glue-card__content">
                      <div class="glue-card__tags glue-spacer-2-top">
                        
                            
                            
                            <span class="glue-label">AI</span>
                            
                            <span class="glue-label">Cloud</span>
                            
                            
                            <span class="glue-label">Tutorials</span>
                            
                            <span class="glue-label">Announcements</span>
                            
                        
                      </div>
                      <p class="glue-headline glue-headline--headline-5">Agent and Model Evaluations in Gemini Enterprise Agent Platform are now GA</p>
                      <div class="glue-card__cta-custom glue-spacer-3-top">
                        <span class="glue-cta">JULY 31, 2026</span>
                        <svg aria-hidden="true" class="glue-icon glue-icon--24px" role="presentation">
                          <use href="/glue-icon/#arrow-forward"></use>
                        </svg>
                      </div>
                    </div>
                  </div>
                </a>
              
                <a class="glue-card glue-carousel__item" href="/en/google-ai-for-game-developers/">
                  <div aria-label="Google AI for game developers" class="glue-card__inner">
                    <picture class="glue-card__asset">
                      <img alt="Google AI for game developers" src="https://storage.googleapis.com/gweb-developer-goog-blog-assets/images/google-ai-games-meta.2e16d0ba.fill-800x400.png">
                    </picture>
                    <div class="glue-card__content">
                      <div class="glue-card__tags glue-spacer-2-top">
                        
                            
                            <span class="glue-label">Cloud</span>
                            
                            <span class="glue-label">Gemini</span>
                            
                            
                            <span class="glue-label">AI</span>
                            
                            <span class="glue-label">Cloud</span>
                            
                            
                            <span class="glue-label">Announcements</span>
                            
                            <span class="glue-label">Community</span>
                            
                        
                      </div>
                      <p class="glue-headline glue-headline--headline-5">Google AI for game developers</p>
                      <div class="glue-card__cta-custom glue-spacer-3-top">
                        <span class="glue-cta">MAY 9, 2025</span>
                        <svg aria-hidden="true" class="glue-icon glue-icon--24px" role="presentation">
                          <use href="/glue-icon/#arrow-forward"></use>
                        </svg>
                      </div>
                    </div>
                  </div>
                </a>
              
                <a class="glue-card glue-carousel__item" href="/en/enhance-security-and-trust-new-session-metadata-in-sign-in-with-google/">
                  <div aria-label="Enhance Security and Trust: New Session Metadata in Sign in with Google" class="glue-card__inner">
                    <picture class="glue-card__asset">
                      <img alt="Enhance Security and Trust: New Session Metadata in Sign in with Google" src="https://storage.googleapis.com/gweb-developer-goog-blog-assets/images/banner-usability-safety-updates-go.2e16d0ba.fill-800x400.png">
                    </picture>
                    <div class="glue-card__content">
                      <div class="glue-card__tags glue-spacer-2-top">
                        
                            
                            
                            <span class="glue-label">Mobile</span>
                            
                            <span class="glue-label">Web</span>
                            
                            
                            <span class="glue-label">Announcements</span>
                            
                            <span class="glue-label">Best Practices</span>
                            
                        
                      </div>
                      <p class="glue-headline glue-headline--headline-5">Enhance Security and Trust: New Session Metadata in Sign in with Google</p>
                      <div class="glue-card__cta-custom glue-spacer-3-top">
                        <span class="glue-cta">JUNE 16, 2026</span>
                        <svg aria-hidden="true" class="glue-icon glue-icon--24px" role="presentation">
                          <use href="/glue-icon/#arrow-forward"></use>
                        </svg>
                      </div>
                    </div>
                  </div>
                </a>
              
            </div>
          </div>
          <!-- Navigation dots -->
          <div class="glue-carousel__navigation" aria-label="Choose a page"
               data-glue-carousel-navigation-label="Selected tab $glue_carousel_page_number$ of $glue_carousel_page_total$">
          </div>
        </div>
      </div>
    </section>
    
  </div>


				
				

<div class="footer-linkboxes__wrapper">
  <nav class="footer-linkboxes" aria-label="Footer links">
    <ul class="footer-linkboxes__list">
      <li class="footer-linkbox">
        <span class="footer-linkbox-heading">
          Connect
        </span>
        <ul class="footer-linkbox-list">
          
            <li class="footer-linkbox-list__item">
              <a href="//googledevelopers.blogspot.com" class="footer-linkbox-list__link">
                Blog
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="https://goo.gle/3FReQXN" class="footer-linkbox-list__link">
                Bluesky
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="https://goo.gle/googlefordevs" class="footer-linkbox-list__link">
                Instagram
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="https://goo.gle/gdevs-li" class="footer-linkbox-list__link">
                LinkedIn
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="https://goo.gle/gdevs-tw" class="footer-linkbox-list__link">
                X (Twitter)
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="https://goo.gle/developers" class="footer-linkbox-list__link">
                YouTube
              </a>
            </li>
          
        </ul>
      </li>
      <li class="footer-linkbox">
        <span class="footer-linkbox-heading">
          Programs
        </span>
        <ul class="footer-linkbox-list">
          
            <li class="footer-linkbox-list__item">
              <a href="//developers.google.com/program" class="footer-linkbox-list__link">
                Google Developer Program
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="//developers.google.com/community/gdg" class="footer-linkbox-list__link">
                Google Developer Groups
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="//developers.google.com/community/experts" class="footer-linkbox-list__link">
                Google Developer Experts
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="//developers.google.com/community/accelerators" class="footer-linkbox-list__link">
                Accelerators
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="//www.womentechmakers.com" class="footer-linkbox-list__link">
                Women Techmakers
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="//developers.google.com/community/nvidia" class="footer-linkbox-list__link">
                Google Cloud &amp; NVIDIA
              </a>
            </li>
          
        </ul>
      </li>
      <li class="footer-linkbox">
        <span class="footer-linkbox-heading">
          Developer consoles
        </span>
        <ul class="footer-linkbox-list">
          
            <li class="footer-linkbox-list__item">
              <a href="//console.developers.google.com" class="footer-linkbox-list__link">
                Google API Console
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="//console.cloud.google.com" class="footer-linkbox-list__link">
                Google Cloud Platform Console
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="//play.google.com/apps/publish" class="footer-linkbox-list__link">
                Google Play Console
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="//console.firebase.google.com" class="footer-linkbox-list__link">
                Firebase Console
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="//console.actions.google.com" class="footer-linkbox-list__link">
                Actions on Google Console
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="//cast.google.com/publish" class="footer-linkbox-list__link">
                Cast SDK Developer Console
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="//chrome.google.com/webstore/developer/dashboard" class="footer-linkbox-list__link">
                Chrome Web Store Dashboard
              </a>
            </li>
          
            <li class="footer-linkbox-list__item">
              <a href="//console.home.google.com/" class="footer-linkbox-list__link">
                Google Home Developer Console
              </a>
            </li>
          
        </ul>
      </li>
    </ul>
  </nav>
</div>
<div class="footer-utility__wrapper">
  <div>
    <nav class="footer-sites" aria-label="Other Google Developers websites">
      <a href="https://developers.google.com/" class="site-logo-link" data-label="Site logo">
        <img src="https://storage.googleapis.com/gweb-developer-goog-blog-cms-assets/site/20260731-000318/images/g-dev.svg" class="site-logo" alt="Google for Developers">
      </a>
      <ul class="footer-sites-list">
        <li class="footer-sites-item">
          <a href="//developer.android.com" class="footer-sites-link">
            Android
          </a>
        </li>
        <li class="footer-sites-item">
          <a href="//developer.chrome.com/home" class="footer-sites-link">
            Chrome
          </a>
        </li>
        <li class="footer-sites-item">
          <a href="//firebase.google.com" class="footer-sites-link">
            Firebase
          </a>
        </li>
        <li class="footer-sites-item">
          <a href="//cloud.google.com" class="footer-sites-link">
            Google Cloud Platform
          </a>
        </li>
        <li class="footer-sites-item">
          <a href="//developers.google.com/products" class="footer-sites-link">
            All products
          </a>
        </li>
        <li class="footer-sites-item">
          <button aria-hidden="true" class="glue-cookie-notification-bar-control footer-sites-link">
            Manage cookies
          </button>
        </li>
      </ul>
    </nav>
    <nav class="footer-utility-links">
      <ul class="footer-utility-list">
        <li class="footer-utility-item">
          <a href="//developers.google.com/terms/site-terms" class="footer-utility-link">
            Terms
          </a>
        </li>
        <li class="footer-utility-item">
          <a href="//policies.google.com/privacy" class="footer-utility-link">
            Privacy
          </a>
        </li>
      </ul>
    </nav>
  </div>
</div>


        
				

        
        <script nonce="Glb5I5IK697ZB8sm2v3WkA==" src="https://www.youtube.com/player_api"></script>
        <script nonce="Glb5I5IK697ZB8sm2v3WkA==" src="//www.gstatic.com/glue/v27_1/glue.min.js"></script>
        <script nonce="Glb5I5IK697ZB8sm2v3WkA==" type="text/javascript" src="https://storage.googleapis.com/gweb-developer-goog-blog-cms-assets/site/20260731-000318/js/dgc_blog.js"></script>

        <script nonce="Glb5I5IK697ZB8sm2v3WkA==" src="https://www.gstatic.com/glue/cookienotificationbar/cookienotificationbar.min.js"
            data-glue-cookie-notification-bar-category="2A"
            data-glue-cookie-notification-bar-site-id="developers.googleblog.com"></script>

        
  <script src="https://storage.googleapis.com/gweb-developer-goog-blog-cms-assets/site/20260731-000318/js/blog_detail.js" nonce="Glb5I5IK697ZB8sm2v3WkA=="></script>
  <script src="https://storage.googleapis.com/gweb-developer-goog-blog-cms-assets/site/20260731-000318/js/prism.js" nonce="Glb5I5IK697ZB8sm2v3WkA=="></script>

    </body>
</html>
