# Weekly Metricool analysis (run FIRST every Monday, before choosing next week's posts)

Brand blogId 7648163, timezone Europe/London. Analyse Instagram AND TikTok, compared.
Period: the last 7 days (Mon–Sun just finished) as the main view, with the last 30 days for context.
Use getAnalyticsDataByMetrics (from/to ISO 8601 with UK offset). Metric IDs:

Instagram account (evolution): IGEV01 followers (LAST), IGEV05 views, IGEV06 reach, IGEV22 reels, IGEV23 reel views,
  IGEV25 reel interactions, IGEV28 reel comments, IGEV29 reel saves, IGEV39 reel shares, IGEV04 feed posts,
  IGEV12 feed views, IGEV09 feed interactions, IGEV15 feed saves, IGEV16 stories, IGEV18 stories reach, IGEV42 accounts engaged.
Instagram reels (per post): IGRE02 date, IGRE03 caption, IGRE06 url, IGRE23 views, IGRE11 reach, IGRE10 likes, IGRE07 comments,
  IGRE12 saves, IGRE21 shares, IGRE24 avg watch time (s), IGRE28 view rate %, IGRE30 skip rate %.
Instagram feed posts/carousels: IGPO02, IGPO03, IGPO06, IGPO07 type, IGPO28 views, IGPO14 reach, IGPO13 likes, IGPO08 comments,
  IGPO15 saves, IGPO27 shares, IGPO29 follows.
Instagram stories: IGST02, IGST03, IGST10 reach, IGST11 replies, IGST13 taps forward, IGST08 exits.
TikTok account (evolution): TKEV07 followers (LAST), TKEV08 new followers, TKEV01 videos, TKEV02 views, TKEV03 likes,
  TKEV04 comments, TKEV05 shares, TKEV09 profile views.
TikTok posts: TKPO02 date, TKPO05 description, TKPO03 url, TKPO07 views, TKPO08 likes, TKPO09 comments, TKPO10 shares,
  TKPO06 duration, TKPO15 avg time watched, TKPO13 full-watch rate, TKPO16 For You %, TKPO21 search %, TKPO22 type.
Evolution rows are per day: SUM the daily values (followers: take the latest non-empty value). Never invent numbers;
if a metric comes back empty, say "not available".

Write analytics/<YYYY>-W<ww>.md with, per network:
1. Headline numbers for the 7 days vs the previous 7 days: followers (and change), views, posts published,
   likes+comments+shares+saves, and the key quality signal (IG reels: avg watch time, view rate, skip rate;
   TikTok: views per post, shares, full-watch rate if available).
2. Top 3 posts by views AND the top post by interactions per view, each with link, format, hook (first line) and why it worked.
3. Bottom 2 posts and the likely reason (e.g. high skip rate, slow text-heavy opening, generic hook).
4. ONE practical recommendation for next week, stated as a concrete rule the week's content must follow
   (e.g. "open every reel with a first-person line and the app screen within 1 second"). Then APPLY it in this run's
   hooks, formats and topics, and say in the weekly message how it was applied.
Also add the week's numbers as a row to analytics/history.csv (date, network, followers, views, posts, interactions).
