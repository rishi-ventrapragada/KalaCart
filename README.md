# KalaCart

A mobile app that helps marginalized Indian artisans list, price, and sell their handmade products online — without needing a camera, a copywriter, or a market research team.

## Why we built this

Most e-commerce platforms assume a seller who can photograph products well, write compelling descriptions, and price competitively. Artisans in rural and marginalized communities often can't do any of that, not because their craft isn't valuable, but because the tools to present it online were never built for them. Meanwhile, buyers who want authentic, traceable handmade goods have no easy way to find them.

KalaCart closes that gap with on-device AI: point your phone at a product, and the app handles the photo, the listing, and the price.

## Who it's for

Built for **artisans** — the people making the craft — as the primary users of this app. A companion website lets **buyers** discover verified artisans and their work, and lets a **ministry reviewer** approve new sellers and listings before they go live, so every purchase can be traced back to a real, reviewed maker.

Built for Smart India Hackathon 2026, addressing a problem statement from the Ministry of Social Justice & Empowerment on market access for marginalized artisans.

## How it works

The app and the website share one live database. An artisan publishes a product here; it's reviewed on the website; once approved, it's visible to buyers, in this same app. AI does the work a professional seller would otherwise need to hire out.

## Tech stack

- **Flutter** — the mobile app (Android)
- **FastAPI** — backend API, handling AI processing and business logic
- **Supabase** — database, authentication, and file storage
- Free-tier AI models power photo enhancement, multilingual voice cataloging, and price suggestions

## Features

- 📸 **Snap and enhance** — take a product photo; AI removes the background and corrects lighting automatically
- 🎙️ **Speak your listing** — describe your product by voice, in your own language; AI writes a polished title and description
- 💰 **Fair pricing assistant** — get a price suggestion based on your craft category and materials
- 🗂️ **Manage your catalog** — track your submitted products and their status
- ✅ **Verified by design** — every product goes through review before reaching buyers, so trust is built in, not assumed
