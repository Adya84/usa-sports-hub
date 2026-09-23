# USA Sports Hub 0.0.1 Design

## Purpose

Create a standalone, fan-facing USA Sports Hub by copying and adapting the current Home Assistant Football Hub integration at `C:\Users\adria\Documents\Codex\2026-09-13\ca\work\football-hub`. It must retain the existing frontend panel, style system, responsive behavior, Home Assistant integration structure, and information architecture, then replace football-specific branding, content, navigation, and data services with a USA Sports Hub identity and major-US-sports coverage.

## Scope

0.0.1 provides one responsive Home Assistant dashboard with league navigation for NFL, NBA, MLB, NHL, MLS, and More Sports. Every league is a view within the same product shell rather than a separate application. The copied provider/coordinator layer becomes the dedicated boundary for new API adapters; providers and credentials will be selected and configured in a follow-up API-integration phase rather than guessed or embedded now.

## Brand and Visual Direction

The interface uses a dark navy base, white surfaces and copy, and restrained red/blue accents. A subtle star-and-stripe-inspired texture may appear in the background but must never impair text contrast. The visual voice is confident, modern, editorial, and distinctly American without using league trademarks.

A bespoke, USA-inspired SVG logo is included in 0.0.1. It combines an abstract shield or badge silhouette, stars, and red/white/blue detailing, remains readable at 24px, and appears in the header. It is a project-owned asset, not a copied sports-league logo.

## Information Architecture

The persistent shell contains the logo and product name, primary navigation, a visual search placeholder, and a profile placeholder. The league selector contains NFL, NBA, MLB, NHL, MLS, and More Sports.

Each league route or tab has the same information order:

1. League hero area with title, current-season label, and a featured matchup.
2. Score rail for live, upcoming, and recently completed games.
3. Standings snapshot.
4. Trending league news.
5. Team spotlight cards.
6. Upcoming schedule.

More Sports is a deliberate placeholder overview for later NCAA, F1, UFC, and other additions. It uses the shared page pattern and explains that additional sports are coming soon; it must not imply data that does not exist.

## Architecture

Use the existing Home Assistant custom integration architecture: `custom_components/usa_sports_hub` provides manifest, configuration, registration, API adapters, coordinator, data helpers, services, translations, and a static frontend panel. Adapt the existing JavaScript custom element and its Shadow DOM stylesheet in-place; do not introduce React, Vite, or a second frontend framework. Rename all domain names, frontend local-storage keys, panel registration identifiers, asset names, and user-facing copy from Football Hub to USA Sports Hub.

The copied frontend retains the current CSS system and responsive layouts. Only theme tokens, background art, logo, and football-specific labels are changed. New logos and backgrounds live with the integration's brand/frontend assets.

## Responsive Behavior

Desktop presents the dashboard in an editorial grid with score rail and content columns. Tablet collapses secondary columns before reducing primary content. Mobile uses a horizontally scrollable league selector, stacked content, touch-sized targets, and preserves critical game status and score information without horizontal page overflow.

## Accessibility and Quality

All interactive tabs use semantic buttons, display an obvious selected state, and support keyboard navigation. Decorative visual elements are hidden from assistive technologies. Text and state colors maintain readable contrast against their surfaces. The app must render without console errors, pass its production build, and remain usable at narrow mobile widths.

## Deferred Work

Live data providers, API keys, authentication, user profiles, push notifications, league-specific deep analytics, and production deployment configuration are outside 0.0.1. A README records the intended boundaries and names the data layer as the replacement point for future APIs.

## Acceptance Criteria

- A standalone Home Assistant integration named USA Sports Hub is ready for a new GitHub repository named `usa-sports-hub`.
- NFL, NBA, MLB, NHL, MLS, and More Sports are available from the shared navigation.
- Selecting a league changes the copied dashboard’s content and visual accent through the USA Sports Hub data boundary.
- All sport dashboards follow the defined Football Hub-style information order.
- A custom USA-inspired SVG logo is visible in the header.
- The copied frontend remains responsive and keyboard-operable, and the Python integration imports successfully.
- The repository includes a clear README for Home Assistant setup, scope, and future provider integration.
