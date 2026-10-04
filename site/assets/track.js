/* GoatCounter events: install copies, reference opens, links out to GitHub.
   Pageviews stay with count.js itself. Event paths have no leading slash
   (GoatCounter refuses one) and carry the page only where the question is
   "from which page". Every call is guarded, so a blocked count.js costs
   nothing and throws nothing. */
(function () {
  var page = location.pathname.replace(/^\/gallop\//, "")
    .replace(/(^|\/)index\.html$/, "").replace(/\/$/, "") || "home";

  function count(path, title) {
    if (window.goatcounter && window.goatcounter.count)
      window.goatcounter.count({path: path, title: title, event: true});
  }

  // what a copy block holds, read off its command text; first match wins
  function kind(text) {
    if (/gallop\/skills\/\*/.test(text)) return ["clone-all", "Copy: all skills"];
    if (/gallop\/skills\/[\w-]+/.test(text)) return ["clone-skill", "Copy: one skill"];
    return ["code", "Copy: code block"];
  }

  // which GitHub link was followed; any other link sends nothing
  function out(href) {
    var m;
    if ((m = href.match(/\/gallop\/tree\/main\/skills\/([\w-]+)/)))
      return ["out/skill-source/" + m[1], "Out: skill source"];
    if (/^https:\/\/github\.com\/0trm\/gallop\/?$/.test(href))
      return ["out/repo", "Out: repository"];
    return null;
  }

  document.addEventListener("click", function (e) {
    var t = e.target.closest ? e.target : e.target.parentElement;
    if (!t) return;
    var b = t.closest(".snip .copy, .codecopy .copy");
    if (b) {
      var k = kind(b.closest(".snip, .codecopy").querySelector("pre").textContent);
      count("copy/" + k[0] + "@" + page, k[1]);
      return;
    }
    var a = t.closest('a[href^="https://github.com/0trm/gallop"]');
    var o = a && out(a.href);
    if (o) count(o[0], o[1]);
  });

  // toggle does not bubble, so listen in the capture phase; one count per
  // reference per page load
  var opened = {};
  document.addEventListener("toggle", function (e) {
    var d = e.target;
    if (!d.open || !d.matches || !d.matches("details.refdoc") || opened[d.id]) return;
    opened[d.id] = true;
    count("open/ref/" + page.replace(/^skills\//, "") + "/" + d.id.replace(/^ref-/, ""),
          "Open: reference file");
  }, true);
})();
