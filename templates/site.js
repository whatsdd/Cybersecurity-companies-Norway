/* Progressive enhancement only: with this file missing the page is still two
   complete, readable, ranked tables. Everything here sorts, filters, re-colours
   or reveals what is already in the DOM. */
(function () {
  "use strict";

  var groups = [];
  Array.prototype.forEach.call(document.querySelectorAll("table.companies"), function (table) {
    var tbody = table.tBodies[0];
    if (!tbody) return;
    groups.push({
      table: table,
      tbody: tbody,
      section: table.closest("[id^='tier-']"),
      rows: Array.prototype.slice.call(tbody.querySelectorAll("tr.data-row"))
    });
  });
  if (!groups.length) return;

  var allRows = [];
  groups.forEach(function (group) { allRows = allRows.concat(group.rows); });

  var countEl = document.getElementById("result-count");
  var emptyEl = document.getElementById("empty");
  var searchEl = document.getElementById("search");
  var capabilityEl = document.getElementById("capability");
  var verificationEl = document.getElementById("verification");
  var resetEl = document.getElementById("reset");
  var emptyReset = document.getElementById("empty-reset");
  var total = allRows.length;

  /* Default state is the ranked order written into the HTML by the build, which
     is why the initial sort key is the row's rank rather than a column. */
  var state = {
    category: "", office: "", staff: "", delivery: "", headcount: "",
    q: "", capability: "", verification: "",
    sortKey: "rank", sortDir: "asc"
  };

  function cellValues(row) {
    return {
      rank: parseFloat(row.dataset.rank || "0"),
      name: (row.dataset.name || ""),
      staff: row.dataset.staff === "" ? -1 : parseFloat(row.dataset.staff),
      employees: row.dataset.employees === "" ? -1 : parseFloat(row.dataset.employees),
      office: row.dataset.office === "true" ? 1 : 0,
      delivery: (row.dataset.delivery || "zz"),
      capabilities: parseFloat(row.dataset.capabilityCount || "0"),
      org: (row.dataset.org || ""),
      verified: (row.dataset.verified || "")
    };
  }

  function compare(a, b) {
    var av = cellValues(a)[state.sortKey];
    var bv = cellValues(b)[state.sortKey];
    if (typeof av === "string" || typeof bv === "string") {
      return String(av).localeCompare(String(bv), "nb");
    }
    return av - bv;
  }

  function applySort() {
    groups.forEach(function (group) {
      var sorted = group.rows.slice().sort(compare);
      if (state.sortDir === "desc") sorted.reverse();
      sorted.forEach(function (row) {
        group.tbody.appendChild(row);
        var detail = document.getElementById(row.dataset.detailId);
        if (detail) group.tbody.appendChild(detail);
      });
    });
    Array.prototype.forEach.call(document.querySelectorAll("thead th"), function (th) {
      if (th.dataset.key === state.sortKey) {
        th.setAttribute("aria-sort", state.sortDir === "asc" ? "ascending" : "descending");
      } else {
        th.removeAttribute("aria-sort");
      }
    });
  }

  /* A staff count only counts as confirmed when somebody can be held to it: the
     company published it, or a named person vouched for it. An estimate is still
     useful, and it is still not confirmed, so it lives in its own filter. */
  function staffMatches(row) {
    var has = row.dataset.hasStaff === "true";
    var basis = row.dataset.staffBasis || "";
    if (state.staff === "confirmed") return has && (basis === "company-site" || basis === "attestation");
    if (state.staff === "estimated") return has && basis === "estimate";
    if (state.staff === "known") return has;
    if (state.staff === "unknown") return !has;
    return true;
  }

  function deliveryMatches(row) {
    var value = row.dataset.delivery || "";
    if (state.delivery === "in-house") return value === "in-house";
    if (state.delivery === "partner") return value === "mixed" || value === "partner-network";
    return true;
  }

  function matches(row) {
    if (state.category && row.dataset.category !== state.category) return false;
    if (state.office && row.dataset.office !== state.office) return false;
    if (state.headcount && row.dataset.hasEmployees !== "true") return false;
    if (!staffMatches(row)) return false;
    if (!deliveryMatches(row)) return false;
    if (state.verification && row.dataset.verification !== state.verification) return false;
    if (state.capability && (row.dataset.capabilities || "").split(" ").indexOf(state.capability) === -1) return false;
    if (state.q) {
      var haystack = row.dataset.search || "";
      var terms = state.q.toLowerCase().split(/\s+/).filter(Boolean);
      for (var i = 0; i < terms.length; i++) {
        if (haystack.indexOf(terms[i]) === -1) return false;
      }
    }
    return true;
  }

  function apply() {
    var shown = 0;
    allRows.forEach(function (row) { if (matches(row)) shown++; });

    groups.forEach(function (group) {
      var visibleInGroup = 0;
      group.rows.forEach(function (row) {
        var visible = matches(row);
        row.classList.toggle("is-hidden", !visible);
        if (visible) visibleInGroup++;
        var detail = document.getElementById(row.dataset.detailId);
        if (detail) {
          var button = row.querySelector(".expand");
          var open = button && button.getAttribute("aria-expanded") === "true";
          detail.classList.toggle("is-hidden", !(visible && open));
        }
      });
      /* A whole tier can be filtered away; say so rather than showing an
         empty table with its heading still up. */
      if (group.section) group.section.classList.toggle("is-hidden", visibleInGroup === 0);
    });

    if (countEl) countEl.textContent = "showing " + shown + " of " + total + " companies";
    if (emptyEl) emptyEl.hidden = shown !== 0;
  }

  Array.prototype.forEach.call(document.querySelectorAll(".chip-filter"), function (chip) {
    chip.addEventListener("click", function () {
      var filter = chip.dataset.filter;
      var value = chip.dataset.value;
      state[filter] = state[filter] === value ? "" : value;
      Array.prototype.forEach.call(document.querySelectorAll('.chip-filter[data-filter="' + filter + '"]'), function (other) {
        other.classList.toggle("is-active", state[filter] !== "" && other.dataset.value === state[filter]);
      });
      apply();
    });
  });

  Array.prototype.forEach.call(document.querySelectorAll("thead th"), function (th) {
    var button = th.querySelector("button.sort");
    if (!button) return;
    button.addEventListener("click", function () {
      var key = th.dataset.key;
      if (state.sortKey === key) {
        state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      } else {
        state.sortKey = key;
        state.sortDir = (key === "staff" || key === "employees" || key === "capabilities") ? "desc" : "asc";
      }
      applySort();
      apply();
    });
  });

  allRows.forEach(function (row) {
    var button = row.querySelector(".expand");
    if (!button) return;
    button.addEventListener("click", function () {
      var open = button.getAttribute("aria-expanded") === "true";
      button.setAttribute("aria-expanded", open ? "false" : "true");
      var detail = document.getElementById(row.dataset.detailId);
      if (detail) detail.classList.toggle("is-hidden", open);
    });
  });

  if (searchEl) {
    var debounce;
    searchEl.addEventListener("input", function () {
      clearTimeout(debounce);
      debounce = setTimeout(function () {
        state.q = searchEl.value.trim();
        apply();
      }, 120);
    });
  }
  if (capabilityEl) capabilityEl.addEventListener("change", function () { state.capability = capabilityEl.value; apply(); });
  if (verificationEl) verificationEl.addEventListener("change", function () { state.verification = verificationEl.value; apply(); });

  function reset() {
    state.category = state.office = state.staff = state.delivery = state.headcount = "";
    state.q = state.capability = state.verification = "";
    state.sortKey = "rank";
    state.sortDir = "asc";
    if (searchEl) searchEl.value = "";
    if (capabilityEl) capabilityEl.value = "";
    if (verificationEl) verificationEl.value = "";
    Array.prototype.forEach.call(document.querySelectorAll(".chip-filter"), function (chip) {
      chip.classList.toggle("is-active", chip.dataset.value === "");
    });
    applySort();
    apply();
  }
  if (resetEl) resetEl.addEventListener("click", reset);
  if (emptyReset) emptyReset.addEventListener("click", reset);

  /* Palettes: paper is the default, because this page gets shared on screens and
     printed into procurement packs, with three CRT phosphors one click away. */
  var PALETTES = ["paper", "phosphor", "amber", "ice"];
  var paletteButton = document.getElementById("palette-toggle");
  var palette = "paper";
  try {
    var stored = localStorage.getItem("palette");
    if (stored && PALETTES.indexOf(stored) !== -1) palette = stored;
  } catch (e) { /* private mode */ }

  function applyPalette() {
    document.documentElement.setAttribute("data-palette", palette);
    if (paletteButton) paletteButton.textContent = "palette: " + palette;
  }
  if (paletteButton) {
    paletteButton.addEventListener("click", function () {
      palette = PALETTES[(PALETTES.indexOf(palette) + 1) % PALETTES.length];
      try { localStorage.setItem("palette", palette); } catch (e) { /* ignore */ }
      applyPalette();
    });
  }
  applyPalette();

  applySort();
  apply();
})();
