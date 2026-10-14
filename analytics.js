/*
 * Cloudflare Web Analytics for jubairahammedtushar.github.io
 * Status: not collecting data until a Web Analytics *site token* is configured.
 * The site token is public configuration, NOT a Cloudflare API key.
 * Registration: Cloudflare dashboard -> Web Analytics -> Add a site.
 * More: https://developers.cloudflare.com/web-analytics/get-started/
 */
(function () {
  "use strict";

  // Set to the public Web Analytics site token supplied by Cloudflare.
  // Leave blank to disable all analytics requests (default).
  const CLOUDFLARE_SITE_TOKEN = "";
  const token = CLOUDFLARE_SITE_TOKEN.trim();

  if (!/^[a-f0-9]{32}$/i.test(token)) return;

  const beacon = document.createElement("script");
  beacon.type = "module";
  beacon.src = "https://static.cloudflareinsights.com/beacon.min.js";
  beacon.setAttribute("data-cf-beacon", JSON.stringify({ token: token }));
  document.body.appendChild(beacon);
})();
