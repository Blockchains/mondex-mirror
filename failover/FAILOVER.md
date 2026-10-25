# Failover: serve monaf.ai from this mirror (GitHub Pages)

Only do this if Grok Build hosting (A @ 216.150.1.1) is down for a long time. The mirror is
read-only: SSR HTML with no client JS. Wallet actions do not work. Turn it back as soon as Build recovers.

1. Pages custom domain (this activates `failover/CNAME.ready`):
   `gh api -X PUT repos/Blockchains/mondex-mirror/pages -f cname=monaf.ai`
   (or Settings → Pages → Custom domain = monaf.ai). With workflow (Actions) deployments, the
   custom domain comes from this setting, not from a CNAME file.
2. DNS at the registrar: delete `A @ 216.150.1.1` and add four records:
   `A @ 185.199.108.153`, `A @ 185.199.109.153`, `A @ 185.199.110.153`, `A @ 185.199.111.153`
   (optional AAAA 2606:50c0:8000::153 / 8001 / 8002 / 8003::153). Optional `CNAME www blockchains.github.io`.
3. Wait for the DNS check, then tick "Enforce HTTPS" (`gh api -X PUT repos/Blockchains/mondex-mirror/pages -F https_enforced=true`).
   Let's Encrypt issuance usually takes 15–60 min, so HTTPS may error until then.
4. Optional for SEO while you are failed over: the pages already canonicalise to https://monaf.ai. Remove the
   noindex step in scripts/postprocess.py only if the outage will last days.
5. Rollback: put `A @ 216.150.1.1` back, remove the extra A records, then
   `gh api -X DELETE repos/Blockchains/mondex-mirror/pages/cname` or clear the custom domain in Settings.
   The mirror keeps serving at https://blockchains.github.io/mondex-mirror/.
Note: if monaf.ai is down when the mirror job runs, wget fails and the job stops before deploying,
so the last good snapshot stays live. The `snapshots` branch of Blockchains/mondex holds a dated copy as well.
