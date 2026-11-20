# Instagram-and-TikTok-MyGroom-Automation
## TikTok photo posts: JPEG only
TikTok rejects PNG photos ("'image/png' type is not allowed"). The carousel, cost-carousel and meme tools now write a `.jpg`
next to every feed `.png`. **Always use the `.jpg` URLs for TikTok photo posts in Metricool** (PNG is fine for Instagram).
Also keep the TikTok **photo-post title (`tiktokData.title`) to 90 characters or fewer**, or TikTok returns "post info is empty or incorrect (400)". Put hashtags and the longer copy in `text` (the description).
