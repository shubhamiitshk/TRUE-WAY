# TrueWay Vision — State-of-the-Art Sources (verified 2026-10)

Companion to `docs/audit/VISION_DETECTION_AUDIT_AND_RECOMMENDATIONS.md` §7.
Every entry below was fetched and read during the research session. Entries marked
**prior knowledge** had their venue asserted but were not re-fetched — verify before quoting
numbers. Entries marked **DO NOT CITE** were searched for and could not be found.

---

## 1. Open-set recognition / rejection

| # | Title | Venue / year | URL | Used for |
|---|---|---|---|---|
| 1 | Open-Set Recognition in the Age of Vision-Language Models | ECCV 2024, arXiv:2403.16528 | https://arxiv.org/abs/2403.16528 | **Primary OSR reference.** Defines ψ_Cosine / ψ_Softmax / ψ_Entropy; finds relative scores beat raw cosine; reports <12 % TPR retained at 95 % precision; introduces AuPR / P@95R / R@95P |
| 2 | Managing the Unknown: a survey on Open Set Recognition | arXiv:2312.08785 (2024) | https://arxiv.org/abs/2312.08785 | OSR taxonomy (evidential / distance / EVT / prototype / generative); threshold selection & open-space risk as the two standing unsolved problems |
| 3 | Towards Open Set Deep Networks (OpenMax) | CVPR 2016, arXiv:1511.06233 | https://arxiv.org/abs/1511.06233 | Classical OSR baseline |
| 4 | Latent Space Energy-based Model for Fine-grained Open Set Recognition (FineOSR) | arXiv:2309.10711 | https://arxiv.org/abs/2309.10711 | Fine-grained OSR |
| 5 | DiT-Distill: Open-Set Fine-Grained Retrieval via Generative Curriculum Knowledge | CVPR 2026 | https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_DiT-Distill_Open-Set_Fine-Grained_Retrieval_via_Generative_Curriculum_Knowledge_CVPR_2026_paper.html | "Open-set **retrieval**" is now a first-class venue |
| 6 | DINO Eats CLIP: Adapting Beyond Knowns for Open-set 3D Object Retrieval | CVPR 2026 | https://openaccess.thecvf.com/content/CVPR2026/html/He_DINO_Eats_CLIP_Adapting_Beyond_Knowns_for_Open-set_3D_Object_Retrieval_CVPR_2026_paper.html | same |

**Prior knowledge (verify):** Duc et al., *Open Set Recognition Using Evidential Deep Learning*,
NeurIPS 2022 — canonical evidential OSR paper; arXiv ID / venue page **not verified** in session.
Zadrozny & Elkan (isotonic regression, ICML 2002); Guo et al. (temperature scaling, ICML 2017);
Clopper & Pearson, *Biometrika* 1934; Geifman & El-Yaniv, *Selective Classification for Deep Neural
Networks*, arXiv:1705.08500.

---

## 2. Landmarks / place retrieval benchmarks

| # | Title | Venue / year | URL | Note |
|---|---|---|---|---|
| 7 | Where We Are and What We're Looking At (introduces **GWS15k**) | CVPR 2023 | https://openaccess.thecvf.com/content/CVPR2023/html/Clark_Where_We_Are_and_What_Were_Looking_At_Query_Based_CVPR_2023_paper.html | GWS15k is a **geo-localization** set (15 k Street View images), *not* instance-level landmark retrieval |
| 8 | GT-Loc | ICCV 2025, arXiv:2507.10473 | https://arxiv.org/abs/2507.10473 | GWS15k SOTA = **0.88 % within 1 km** — a planet-scale task; **not** a proxy for "15 monuments in one district" |
| 9 | TransLocator | ECCV 2022, arXiv:2204.13861 | https://arxiv.org/abs/2204.13861 | Geo-localisation reference |
| 10 | Google Landmarks Dataset v2 | CVPR 2020, DOI 10.1109/cvpr42600.2020.00265 | OpenAlex record | The real instance-level landmark benchmark: 1.58 M train / ~200 k landmarks + 10 k "hard" test landmarks |
| 11 | Revisiting Oxford and Paris | CVPR 2018, arXiv:1803.11285 | https://arxiv.org/abs/1803.11285 | **The canonical retrieval protocol to copy**: 3 difficulty tiers, 15 hard queries, 100 k hard negatives; resolution 1024² > 512² > 256² |
| 12 | Benchmarking Image Retrieval for Visual Localization | 3DV 2020 (Pion, Humenberger, Csurka, Cabon, Sattler) | https://europe.naverlabs.com/research/publications/benchmarking-image-retrieval-for-visual-localization | Retrieval score does **not** reliably predict place-recognition performance |
| 13 | Where in the World, Part 1 (WITW) | IQT Labs, 7 Feb 2022 | https://www.iqt.org/library/where-in-the-world-part-1-a-new-dataset-for-cross-view-image-geolocalization | 164 455 Flickr↔satellite pairs, 11 AOIs, **not publicly released** |
| 14 | SPair-71k | ICCV 2019, arXiv:1908.10543 | https://arxiv.org/abs/1908.10543 | Same-object different-view |
| 15 | TIGeR: A Unified Framework for Time, Images and Geo-location Retrieval | CVPR 2026 | https://openaccess.thecvf.com/content/CVPR2026/html/Shatwell_TIGER_A_Unified_Framework_for_Time_Images_and_Geo-location_Retrieval_CVPR_2026_paper.html | Geo-time-aware retrieval; **"oracle GPS given"** variant; up to +14 % recall |
| 16 | MMLandmarks | CVPR 2026 | https://openaccess.thecvf.com/content/CVPR2026/html/Kristoffersen_MMLandmarks_a_Cross-View_Instance-Level_Benchmark_for_Geo-Spatial_Understanding_CVPR_2026_paper.html | 18 557 landmarks, cross-view instance-level |
| 17 | EfficientVPR | CVPR 2026 | https://openaccess.thecvf.com/content/CVPR2026/html/Tang_EfficientVPR_Toward_Efficient_Visual_Place_Recognition_via_Scene-Aware_Prompt_Tuning_and_Adaptive_Feature_Enhancement_CVPR_2026_paper.html | Efficient VPR |

**DO NOT CITE (searched, 0 hits):** "GWS25k" · "Where in the World (**Pikachu**)" as a dataset name ·
"Revisiting Image Retrieval Evaluation" · "Learning to Localize Using a GPS Prior" ·
"Alpha Query Expansion (α-QE)" · *Inverted Multi-Index for Fast, Accurate Place Recognition*.

---

## 3. Encoders

| # | Title | Venue / year | URL | Note |
|---|---|---|---|---|
| 18 | DINOv2 | arXiv:2304.07193 | https://arxiv.org/abs/2304.07193 | The documented kNN/instance-retrieval teacher (+41 % mAP Oxford-Hard over SSL). ViT-S/14: Oxford-M 68.8 / Oxford-H 43.2 / Met GAP 29.4. **Also: removes near-duplicates of every benchmark's test set from its pretraining pool** |
| 19 | DINOv3 | arXiv:2508.10104 | https://arxiv.org/abs/2508.10104 | ConvNeXt-Tiny 29 M / 5 GFLOPs@256 — best-documented on-device candidate |
| 20 | DINOv3 release blog | Meta AI, 2025 | https://ai.meta.com/blog/dinov3-self-supervised-vision-model | **Commercial licence**; "resource-constrained use cases" |
| 21 | SigLIP 2 | arXiv:2502.14786 | https://arxiv.org/abs/2502.14786 | Too large at So400M+; base/16 borderline |
| 22 | MobileCLIP2 | TMLR Aug 2025 (Featured), arXiv:2508.20691 | https://arxiv.org/abs/2508.20691 | **S0: 11.4 M / 1.5 ms / 71.5 % IN-1k** — identical params & latency to MobileCLIP-S0, better data |
| 23 | apple/ml-mobileclip README | GitHub, 2025 | https://github.com/apple/ml-mobileclip | Model table; MobileOne "reparameterize first" for export |
| 24 | MobileCLIP | CVPR 2024, arXiv:2311.17049 | https://arxiv.org/abs/2311.17049 | Original |
| 25 | Data Filtering Networks | arXiv:2309.17425 | https://arxiv.org/abs/2309.17425 | The DFN recipe behind MobileCLIP2/EVA |
| 26 | EVA-CLIP-18B | arXiv:2402.04252 | https://arxiv.org/abs/2402.04252 | Teacher only |
| 27 | EdgeNeXt | ECCVW 2022 (Oral), arXiv:2206.10589 | https://arxiv.org/abs/2206.10589 | Mobile CNN-Transformer |
| 28 | EfficientViT (CGA / MSLA) | CVPR'23 arXiv:2305.07027 / ICCV'23 arXiv:2205.14756 | https://arxiv.org/abs/2305.07027 | On-device candidates |
| 29 | SAM 2 | arXiv:2408.00714 | https://arxiv.org/abs/2408.00714 | Dense features; research-grade for global instance retrieval |
| 30 | What Matters for Grocery Product Retrieval with Open Source VLMs | ICPR 2026, arXiv:2605.18029 | https://arxiv.org/abs/2605.18029 | 190 VLMs on a fine-grained instance task: **data quality > scale (+16.6 %)**; efficient models can beat larger ones; **R@1 sits 17.5 pts below R@5** |
| 31 | What Do Scan-Derived Class Prototypes Add? | arXiv:2609.04381 (2026) | https://arxiv.org/abs/2609.04381 | Real vs **permuted** prototypes ≤1 pt; matched logistic regression matched/beat the fused system; **query protocol moved accuracy by 43.3 pts** |

---

## 4. Quantization

| # | Title | Venue / year | URL | Note |
|---|---|---|---|---|
| 32 | LiteRT 8-bit quantization specification | Google AI Edge | https://developers.google.com/edge/litert/conversion/tensorflow/quantization/quantization_spec | Per-axis weights; *"This has large improvements to accuracy"*; signed int8, zero-point 0 |
| 33 | LiteRT post-training quantization | Google AI Edge | https://developers.google.com/edge/litert/conversion/tensorflow/quantization/post_training_quantization | Dynamic-range: 4× smaller, **2–3× speedup, no calibration set**; full-int: 4× smaller, 3×+, needs 100–500 calib samples; FP16: 2× + GPU |
| 34 | AdaRound | ICML 2020, arXiv:2004.10568 | https://arxiv.org/abs/2004.10568 | PTQ rounding |
| 35 | BRECQ | ICCV 2021, arXiv:2102.05426 | https://arxiv.org/abs/2102.05426 | Block reconstruction |
| 36 | PTQ4ViT | arXiv:2111.12293 | https://arxiv.org/abs/2111.12293 | ViT PTQ |
| 37 | RepQ-ViT | ICCV 2023, arXiv:2212.08254 | https://arxiv.org/abs/2212.08254 | Scale re-parameterisation for PTQ |
| 38 | SmoothQuant | ICML 2023, arXiv:2211.10438 | https://arxiv.org/abs/2211.10438 | Activation-outlier migration, W8A8 |
| 39 | Q-HyViT | IEEE IoT-J, arXiv:2303.12557 | https://arxiv.org/abs/2303.12557 | Hybrid ViT PTQ for IoT |
| 40 | Can Less Precise Be More Reliable? (quantisation's impact on CLIP) | arXiv:2509.21173 | https://arxiv.org/abs/2509.21173 | **Quantised CLIP can be 4× SLOWER** than FP32 (B/32: 19.6 ms → 81.1 ms) |
| 41 | Detecting Unreliable Classifications from Quantized Models | arXiv:2610.18575 | https://arxiv.org/abs/2610.18575 | FP32-vs-INT8 output-agreement cosine; **< 0.8 ⇒ below FP32 baseline** → use as a CI gate |

**Prior knowledge (verify):** Jacob et al., *Quantization and Training of Neural Networks for Efficient
Integer-Arithmetic-Only Inference*, CVPR 2018 — bias correction for train/serve skew;
Bondarenko, Chiaro & Nagel, LR-QAT (2024).

---

## 5. Calibration

| # | Title | Venue / year | URL | Note |
|---|---|---|---|---|
| 42 | Improving Calibration in Deep Metric Learning With Cross-Example Softmax | arXiv:2011.08824 | https://arxiv.org/abs/2011.08824 | Metric-learning calibration |
| 43 | Calibrated Similarity for Reliable Geometric Analysis of Embedding Spaces | arXiv:2601.16907 (2026) | https://arxiv.org/abs/2601.16907 | Calibrated similarity for embeddings |
| 44 | Semantic Alignment with Calibrated Similarity for Multilingual Sentence Embedding | Findings of EMNLP 2021 | — | Calibrated-similarity family |

**Prior knowledge (verify):** Zadrozny & Elkan ICML 2002 (isotonic); Guo et al. ICML 2017
(temperature); Clopper & Pearson, *Biometrika* 1934 (exact binomial); Geifman & El-Yaniv
arXiv:1705.08500 (risk–coverage).

---

## 6. Test-time augmentation & multi-view

| # | Title | Venue / year | URL | Note |
|---|---|---|---|---|
| 45 | Learning Test-time Augmentation for Content-based Image Retrieval | CVIU 2022, arXiv:2002.01642 | https://arxiv.org/abs/2002.01642 | Learned TTA ensemble; cites multi-crop + resolution findings |
| 46 | MeTTA — Mean Embeddings with Test-time Data Augmentation | NeurIPS 2021, arXiv:2106.08038 | https://arxiv.org/abs/2106.08038 | **Global features of different augmentations are directly averageable**; +0.9–1.7 pts ImageNet linear |
| 47 | Embedding Expansion: Augmentation in Embedding Space for Deep Metric Learning | CVPR 2020, arXiv:2003.02546 | https://arxiv.org/abs/2003.02546 | Buy gallery diversity without new photos |

**Prior knowledge (verify):** Chum et al., *Query Expansion with Local and Global Features*,
BMVC 2011 (AQE).

---

## 7. Geo prior

| # | Title | Venue / year | URL | Note |
|---|---|---|---|---|
| 48 | Geographically Local Representation Learning with a Spatial Prior for Visual Localization | ECCV 2020, DOI 10.1007/978-3-030-66096-3_38 | OpenAlex record | Explicit spatial-prior learning for VPR |
| 49 | Spotter: Efficient Urban Visual Localization in GPS-Degraded Environments | arXiv:2608.23290 (2026) | https://arxiv.org/abs/2608.23290 | GPS multipath / degraded priors, edge execution |
| 50 | MMS-VPR | arXiv:2505.12254 | https://arxiv.org/abs/2505.12254 | Fine-grained street-level VPR |

---

## 8. Copy detection / near-duplicate leakage

| # | Title | Venue / year | URL | Note |
|---|---|---|---|---|
| 51 | A Benchmark and Asymmetrical-Similarity Learning for Practical Image Copy Detection (NDEC) | AAAI 2023, arXiv:2205.12358 | https://arxiv.org/abs/2205.12358 | **100 000 train / 24 252 test hard-negative pairs** — the scale of "hard negatives" we are missing by 3–4 orders of magnitude |
| 52 | Bag of Tricks and A Strong baseline for Image Copy Detection | arXiv:2111.08004 | https://arxiv.org/abs/2111.08004 | Baseline recipe |
| 53 | A Self-Supervised Descriptor for Image Copy Detection | arXiv:2202.10261 | https://arxiv.org/abs/2202.10261 | Descriptor |
| 54 | Image Copy Detection for Diffusion Models | NeurIPS 2024, arXiv:2409.19952 | https://arxiv.org/abs/2409.19952 | 40 k replica pairs, 6 replication levels |
| 55 | DISC21 / Image Similarity Challenge | Meta AI, 2021–22 | https://ai.meta.com/datasets/disc21-dataset · https://ai.meta.com/blog/detecting-manipulated-images-the-image-similarity-challenge-results-and-winners | 1 M refs / 50 k dev / 50 k test; SSN++ production system |
| 56 | Benchmarking Pretrained Vision Embeddings for Near- and Duplicate Detection | arXiv:2312.07273 | https://arxiv.org/abs/2312.07273 | DINOv1/v2 + LSH/HNSW, top-1 AUC 0.98–0.99 → **our P1-6 recipe** |
| 57 | The Inverted Multi-Index | CVPR 2012, DOI 10.1109/cvpr.2012.6248038 | OpenAlex record | Canonical near-dup index |
| 58 | Packing and Padding: Coupled Multi-index for Accurate Image Retrieval | CVPR 2014, DOI 10.1109/cvpr.2014.250 | OpenAlex record | Companion |
| 59 | Photo Tourism | ACM TOG 2006, DOI 10.1145/1141911.1141964 | OpenAlex record | Original "visit a place again" formulation |

---

## 9. On-device runtime

| # | Title | Venue / year | URL | Note |
|---|---|---|---|---|
| 60 | LiteRT v2 README | GitHub, 2026 | https://github.com/google-ai-edge/LiteRT | **Compiled Model API is mandated**; XNNPACK CPU, ML Drift GPU, TPU/NPU; TFLite Interpreter in maintenance mode |
| 61 | GPU delegates for LiteRT | Google AI Edge | https://ai.google.dev/edge/litert/performance/gpu | Delegate guidance |
| 62 | Unlocking Peak Performance on Qualcomm NPU with LiteRT | Google Developers Blog, 24 Nov 2025 | https://developers.googleblog.com/unlocking-peak-performance-on-qualcomm-npu-with-litert | **QNN accelerator replaces the TFLite QNN delegate**; AOT compile; up to 100× vs CPU, 10× vs GPU; 56/72 models <5 ms on 8 Elite Gen 5; **INT8 weights required for HTP**; custom int16 activation kernels for transformers |
| 63 | QNN hardware acceleration on Android | Edge Impulse Docs | https://docs.edgeimpulse.com/tutorials/topics/android/qnn-acceleration | YOLOv5s INT8 5.7 → 0.5 ms (11.4×) on RB3 Gen 2; Tensor-G Pixel phones unsupported |
| 64 | Image Embedder overview + Android guide | Google AI Edge / MediaPipe | https://ai.google.dev/edge/mediapipe/solutions/vision/image_embedder | `l2_normalize` option (default **false**); `quantize` option; **GPU slower than CPU for MobileNet-V3-small on Pixel 6 (7.83 vs 3.94 ms)**; delegate selection is app-side |
| 65 | Performance issues with TFLite quantized models on ARM Cortex-A73 | Google AI Developers Forum | https://discuss.ai.google.dev/t/performance-issues-with-tflite-quantized-models-on-arm-cortex-a73-cpu/31906 | **A55 has DOTPROD, A73 does not** → int8 can be slower on older cores |
