(function () {
  "use strict";

  /* ---------- Tab switching (Sign in / Create account) ---------- */
  var tabs = document.querySelectorAll(".auth-tab");
  var tabsWrap = document.querySelector(".auth-tabs");
  var forms = {
    signin: document.getElementById("form-signin"),
    signup: document.getElementById("form-signup"),
  };

  function activateTab(name) {
    tabs.forEach(function (t) {
      var isActive = t.dataset.tab === name;
      t.classList.toggle("is-active", isActive);
      t.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    Object.keys(forms).forEach(function (key) {
      forms[key].classList.toggle("is-active", key === name);
    });
    if (tabsWrap) tabsWrap.setAttribute("data-active", name);
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      activateTab(tab.dataset.tab);
    });
  });

  document.querySelectorAll("[data-tab-trigger]").forEach(function (el) {
    el.addEventListener("click", function () {
      activateTab(el.getAttribute("data-tab-trigger"));
      document.querySelector(".auth-card").scrollIntoView({ behavior: "smooth", block: "center" });
    });
  });

  /* ---------- Password show/hide ---------- */
  document.querySelectorAll("[data-toggle-pw]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var input = document.getElementById(btn.getAttribute("data-toggle-pw"));
      if (!input) return;
      var showing = input.type === "text";
      input.type = showing ? "password" : "text";
      btn.setAttribute("aria-label", showing ? "Show password" : "Hide password");
      btn.classList.toggle("is-visible", !showing);
    });
  });

  /* ---------- Respect reduced motion: pause background video ---------- */
  var video = document.getElementById("bgVideo");
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  function applyMotionPreference() {
    if (!video) return;
    if (reduceMotion.matches) {
      video.pause();
      video.classList.add("is-hidden");
    } else {
      video.classList.remove("is-hidden");
      video.play().catch(function () {
        /* Autoplay can be blocked before user interaction; poster/image still shows. */
      });
    }
  }
  applyMotionPreference();
  if (reduceMotion.addEventListener) {
    reduceMotion.addEventListener("change", applyMotionPreference);
  }

  /* If the video fails to load for any reason, fall back to the static image. */
  if (video) {
    video.addEventListener("error", function () {
      video.classList.add("is-hidden");
    });
  }
})();
