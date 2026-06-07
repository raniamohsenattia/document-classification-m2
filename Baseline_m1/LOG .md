# Development Log — Document Image Classification Using Lightweight CNNs

---

## Week 1 — Dataset and Pipeline Setup

**Dates:** May 1–7, 2026  
**Contributors:** Rania Attia (data), Nourhan Salem (pipeline setup)

### What we did

Started by downloading the RVL-CDIP dataset. The full dataset is around 40GB which was more than expected, so we decided early on to work with a sampled subset — up to 500 images per class across 10 classes, giving us roughly 5,000 images total. This felt like a reasonable size to iterate quickly without hitting memory issues on our machines.

Rania wrote the split creation script (70% train, 15% val, 15% test, stratified by class, seed fixed at 42). We also ran a quality inspection pass across the training split to catch obvious problems before training. Found a small number of near-blank images (white pixel ratio above 98%) and some noticeably skewed scans. Both were handled — blanks removed, skew corrected using projection-profile deskewing.

Nourhan set up the basic PyTorch pipeline in parallel: ImageFolder loading, transforms, DataLoader. Nothing trained yet this week, just making sure the data flows through without errors.

### Key decisions

We initially considered using Tobacco3482 as the main dataset since it is smaller and faster to experiment with. Changed our minds after realizing it is too small to fine-tune a CNN reliably, and the image quality is poor enough that OCR results would dominate any comparison. Decided to use RVL-CDIP as the main dataset and keep Tobacco3482 only as a preliminary pilot for the OCR pipeline. This also makes the final CNN vs. OCR comparison fair, since both methods will be evaluated on the same data.

Chose 10 classes out of 16 available. Selection criterion was class frequency — picked the 10 most populated categories to avoid severe imbalance. The remaining 6 are reserved for the planned Week 4 expansion.

### Issues

The RVL-CDIP download kept timing out. Ended up using a mirror and downloading in parts overnight. Not a technical issue exactly, just slow.

One class folder (Note) had a handful of .tiff files that PIL was reading as RGBA instead of grayscale. Added a convert('L') call in the loader to normalize everything to single-channel before the 3-channel replication step.

---

## Week 2 — CNN Training, OCR Baseline, Midterm Report

**Dates:** May 8–14, 2026  
**Contributors:** Rania Attia (preprocessing notebook, report), Nourhan Salem (CNN), Mariam Youssef (OCR baseline)

### What we did

**CNN (Nourhan).** Implemented MobileNetV2 fine-tuning using the pretrained ImageNet weights from torchvision. Replaced the original classifier head with a two-layer head: Dropout(0.3) -> FC(1280, 256) -> ReLU -> Dropout(0.2) -> FC(256, 10). Trained end-to-end with Adam (lr=1e-3, weight decay=1e-4), StepLR scheduler (step=4, gamma=0.5), batch size 32, 10 epochs. Best checkpoint selected by validation accuracy. Final test accuracy: 81.07%, macro F1: 0.811.

**OCR baseline (Mariam).** Set up Tesseract (PSM 3, OEM 3) on the same RVL-CDIP subset to allow a direct comparison with the CNN. Text extraction followed by cleaning (lowercase, remove single characters, strip non-alphanumeric), TF-IDF vectorization (unigrams + bigrams, max 30,000 features, min_df=2, sublinear_tf=True), then a three-layer PyTorch MLP (input -> 1024 -> 256 -> 10, BatchNorm + Dropout). OCR+MLP reached approximately 70% on the same test set.

**Preprocessing notebook (Rania).** Finalized the quality inspection and preprocessing pipeline as a standalone Colab notebook. Documents the full pipeline with outputs at each stage.

**Midterm report (Rania).** Written and submitted. All results are from RVL-CDIP to keep comparisons fair.

### Key decisions

Decided to fine-tune the full MobileNetV2 rather than freezing early layers. An earlier experiment with layers 0-14 frozen gave about 2 percentage points lower validation accuracy and converged more slowly. Since document images are quite different from natural images — mostly grayscale, text-heavy, no color semantics — freezing low-level filters does not help as much as it would for, say, a natural scene dataset.

The OCR pipeline for the main comparison was deliberately kept simpler than the Tobacco3482 experiments. No multi-pass OCR, no class-specific preprocessing. The goal is a fair single-configuration baseline, not the maximum OCR accuracy we could squeeze out with extra engineering.

### Issues

**Overfitting in the MLP.** Training accuracy reached ~99% within 10 epochs while validation accuracy stayed around 64-70%. Tried increasing dropout to 0.4 and 0.5, adding a third hidden layer, reducing learning rate. None of these fully resolved it. The fundamental issue seems to be that 30,000-dimensional TF-IDF features give the model too many degrees of freedom relative to the training set size, and many visually-oriented classes produce very short OCR output. Reported honestly in the midterm.

**Scheduler mismatch between report draft and code.** An early draft of the midterm described ReduceLROnPlateau, which was used during initial experiments but replaced by StepLR in the final training run. Caught during a consistency review and corrected before submission.

**Parameter count discrepancy.** An early version of the report stated approximately 2.5 million trainable parameters based on an experiment where layers 0-14 were frozen. After switching to full fine-tuning the actual count is approximately 3.4 million. Updated in the report.

---

## Planned — Week 3

**Dates:** May 15–21, 2026

### What we intend to do

Rania will build the robustness evaluation harness — systematic testing under rotation (0 to 90 degrees in 15-degree steps), Gaussian noise (sigma 0.01 to 0.30), Gaussian blur (kernel 1 to 15), and combinations. Preliminary manual tests already suggest accuracy drops sharply at 45-degree rotation and moderate noise, so this needs proper measurement.

Nourhan will run the robustness experiments and start on the 14-class expansion (adding 4 more RVL-CDIP categories with supplementary training samples).

Mariam will implement and evaluate the two fusion strategies: score-level fusion (weighted average of CNN and OCR softmax outputs) and feature-level fusion (concatenate MobileNetV2 penultimate embedding with TF-IDF vector, train a joint classifier).

### Known risks going into Week 3

The score-level fusion weight is a hyperparameter that needs tuning on the validation set. If the OCR pipeline is too noisy on certain classes it might actually hurt the fused model relative to the CNN alone — we will report whatever the results are rather than cherry-picking the fusion weight.

Feature-level fusion concatenates a 1280-dim CNN embedding with a 30,000-dim TF-IDF vector. The dimensionality imbalance could cause the TF-IDF features to dominate. May need PCA or dimensionality reduction on the TF-IDF side before concatenation.

---

## Planned — Week 4

**Dates:** May 22–28, 2026

### What we intend to do

Finalize 14-class experiments. Apply class-weighted cross-entropy loss (weight proportional to 1/frequency and 1/F1) to target the two weak classes identified in Week 2 — ADVE (F1=0.63) and Report (F1=0.65). Run an ablation study isolating the contribution of ImageNet pretraining, data augmentation, and the two-layer head. Write and submit the final report.
