// Overlook: theme switch (SubScout's runtime) and a slow reveal of each card as it arrives.
import { theme, bindSeg } from "./runtime/js/subscout.js";

const q = new URLSearchParams(location.search).get("theme"); // ?theme=light|dark, for screenshots
if (q === "light" || q === "dark") theme.set(q);
// Light or Dark only: resolve "system" to what the reader sees now, so one of the two is always pressed
if (theme.get() === "system") theme.set(matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
bindSeg(document.getElementById("ctl-theme"), theme);

const items = [...document.querySelectorAll(".reveal")];
if ("IntersectionObserver" in window) {
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
  items.forEach((el) => io.observe(el));
} else {
  items.forEach((el) => el.classList.add("in"));
}
