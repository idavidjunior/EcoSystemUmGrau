---
tags: [padrao, androidpuresdk]
aliases: [aapt + javac + d8 + apksigner]
date: 2026-07-27
---

# aapt + javac + d8 + apksigner

**Fonte:** android_pure_sdk

Pipeline manual Android sem Gradle: aapt package (R.java) -> javac -> jar -> d8 -> aapt package (APK) -> aapt add (dex) -> zipalign -> apksigner
