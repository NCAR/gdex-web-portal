---
name: project-test-homepage-scope
description: Integration work is scoped to TestHomePage and test classes only — production HomePage must not be touched
metadata:
  type: project
---

All new webpage integration work is scoped to `TestHomePage` and its related test classes (`TestHomePageFeaturedCard`, `TestHomePageSearchSuggestion`) in `home/models.py`.

**Why:** There is a single shared production database used even for testing. Touching `HomePage` or production models risks breaking the live site.

**How to apply:** Never modify `HomePage`, `FeaturedCard`, or `HomePageSearchSuggestion` when working on the new design integration. All model changes, template changes, and view changes go to the `TestHomePage` equivalents only.
