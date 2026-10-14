/*
 * Cloudflare Web Analytics for jubairahammedtushar.github.io
 * Status: tracking enabled using the Cloudflare Web Analytics site token.
 * The site token is public configuration, NOT a Cloudflare API key.
 * Registration: Cloudflare dashboard -> Web Analytics -> Add a site.
 * More: https://developers.cloudflare.com/web-analytics/get-started/
 */
(function () {
  "use strict";

  // Set to the public Web Analytics site token supplied by Cloudflare.
  // The site token is public; this is NOT an API credential.
  const CLOUDFLARE_SITE_TOKEN = "31877450ec0e458abd862806710218dd";
  const token = CLOUDFLARE_SITE_TOKEN.trim();

  if (!/^[a-f0-9]{32}$/i.test(token)) return;

  const beacon = document.createElement("script");
  beacon.type = "module";
  beacon.src = "https://static.cloudflareinsights.com/beacon.min.js";
  beacon.setAttribute("data-cf-beacon", JSON.stringify({ token: token }));
  document.body.appendChild(beacon);
})();
