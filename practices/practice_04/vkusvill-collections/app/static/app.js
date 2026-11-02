const DASHBOARD_LIMIT = 10;
const SVG_NS = "http://www.w3.org/2000/svg";

const rub = new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB", maximumFractionDigits: 2 });
const num = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 1 });
const day = new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" });

const $ = (id) => document.getElementById(id);
const els = {
  categories: $("categories"), status: $("status"), grid: $("grid"), template: $("card-template"),
  hero: $("hero-receipt"),
  searchForm: $("search-form"), searchQuery: $("search-query"), searchClear: $("search-clear"),
  details: $("details"), title: $("details-title"), category: $("details-category"), meta: $("details-meta"),
  products: $("details-products"), total: $("details-total"), kcal: $("details-kcal"),
  macroBar: $("details-macro-bar"), macros: $("details-macros"), barcode: $("details-barcode"),
  open: $("details-open"), copy: $("details-copy"), copied: $("details-copied"),
};

let activeCategory = null;
let activeQuery = "";
let loadVersion = 0;
let currentCartUrl = "";
let heroPrinted = false;

// ---------- helpers ----------

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${response.status} ${url}`);
  return response.json();
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function svgEl(tag, attrs) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  return node;
}

function hash(text) {
  let h = 2166136261;
  for (const ch of text) h = Math.imul(h ^ ch.codePointAt(0), 16777619);
  return h >>> 0;
}

// Small deterministic PRNG, so a collection always gets the same picture.
function random(seed) {
  let a = seed;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function productWord(n) {
  const mod10 = n % 10, mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return "продукт";
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return "продукта";
  return "продуктов";
}

// ---------- generated art ----------

const PRODUCE = [
  { fill: "#E4572E", leaf: true },               // tomato
  { fill: "#F28C28", leaf: true },               // orange
  { fill: "#F4C430", squash: 0.78 },             // lemon
  { fill: "#7DB343", stem: true },               // green apple
  { fill: "#6B3E75", squash: 0.88 },             // plum
  { fill: "#9E2A4F", leaf: true },               // beet
  { fill: "#FFF4DC", squash: 0.8, stroke: "#E2D3B2" }, // egg
  { fill: "#C8E07A", stem: true },               // pear-ish
];

function drawCrate(svg, seedText, count) {
  svg.replaceChildren();
  const rnd = random(hash(seedText));
  const n = Math.max(2, Math.min(count, 7));
  const base = 40 - n * 2.6;
  const items = Array.from({ length: n }, (_, i) => ({
    kind: PRODUCE[Math.floor(rnd() * PRODUCE.length)],
    r: base * (0.8 + rnd() * 0.45),
    x: 34 + (172 * (i + 0.5)) / n + (rnd() - 0.5) * 14,
    tilt: (rnd() - 0.5) * 40,
  })).sort((a, b) => b.r - a.r);

  for (const item of items) {
    const ry = item.r * (item.kind.squash ?? 1);
    const cy = 96 - ry * 0.75 - rnd() * 8;
    const g = svgEl("g", { transform: `rotate(${item.tilt} ${item.x} ${cy})` });
    g.append(svgEl("ellipse", {
      cx: item.x, cy, rx: item.r, ry, fill: item.kind.fill,
      stroke: item.kind.stroke ?? "rgb(0 0 0 / 0.12)", "stroke-width": 1.5,
    }));
    g.append(svgEl("ellipse", {
      cx: item.x - item.r * 0.35, cy: cy - ry * 0.4, rx: item.r * 0.28, ry: ry * 0.18,
      fill: "#fff", opacity: 0.35, transform: `rotate(-30 ${item.x} ${cy})`,
    }));
    if (item.kind.leaf) {
      g.append(svgEl("path", {
        d: `M${item.x} ${cy - ry + 2} q 7 -12 18 -9 q -6 9 -18 9 z`, fill: "#3E8A3A",
      }));
    }
    if (item.kind.stem) {
      g.append(svgEl("path", {
        d: `M${item.x} ${cy - ry + 3} q 2 -8 6 -11`, stroke: "#5B3A1E", "stroke-width": 3,
        fill: "none", "stroke-linecap": "round",
      }));
    }
    svg.append(g);
  }

  // Crate front, drawn over the produce.
  svg.append(svgEl("rect", { x: 18, y: 88, width: 204, height: 44, rx: 4, fill: "var(--wood)" }));
  svg.append(svgEl("rect", { x: 18, y: 88, width: 204, height: 7, rx: 3, fill: "var(--wood-dark)" }));
  svg.append(svgEl("line", { x1: 22, y1: 111, x2: 218, y2: 111, stroke: "var(--wood-dark)", "stroke-width": 2 }));
  for (const x of [30, 210]) {
    svg.append(svgEl("circle", { cx: x, cy: 102, r: 2.2, fill: "var(--wood-dark)" }));
    svg.append(svgEl("circle", { cx: x, cy: 121, r: 2.2, fill: "var(--wood-dark)" }));
  }
}

function drawBarcode(svg, seedText) {
  svg.replaceChildren();
  const rnd = random(hash(seedText));
  let x = 0;
  for (let i = 0; i < 64; i++) {
    const width = 1 + Math.floor(rnd() * 3);
    if (i % 2 === 0) svg.append(svgEl("rect", { x, y: 0, width, height: 44 }));
    x += width;
  }
  svg.setAttribute("viewBox", `0 0 ${x} 44`);
  svg.setAttribute("preserveAspectRatio", "none");
}

function receiptLines(list, products) {
  list.replaceChildren(
    ...products.map((p) => {
      const li = el("li");
      li.append(
        el("span", "name", p.name),
        el("span", "dots"),
        el("span", "qty", `${p.quantity}×`),
        el("span", "price", rub.format(p.price * p.quantity)),
      );
      return li;
    }),
  );
}

// ---------- hero receipt ----------

function printHero(c) {
  const hero = els.hero;
  hero.replaceChildren();
  hero.append(
    el("p", "r-head", `Чек подборки № ${c.id}`),
    el("p", "r-title", c.title),
    el("p", "r-meta", `${c.category}, ${day.format(new Date(c.created_at))}`),
  );
  const list = el("ol", "r-lines");
  receiptLines(list, c.products.slice(0, 6));
  if (c.products.length > 6) list.append(el("li", "qty", `…и ещё ${c.products.length - 6}`));
  const total = el("div", "r-total");
  total.append(el("span", null, "Итого"), el("span", "tag tag-big", rub.format(c.totals.price)));
  const code = svgEl("svg", { class: "barcode", "aria-hidden": "true" });
  drawBarcode(code, c.cart_url);
  hero.append(list, total, code);
  hero.setAttribute("aria-label", `Последняя подборка: ${c.title}, ${rub.format(c.totals.price)}. Открыть`);
  hero.onclick = () => openDetails(c.id);
  hero.hidden = false;
  hero.classList.add("printing");
}

// ---------- catalogue ----------

function showStatus(text, { error = false, retry = null } = {}) {
  els.status.textContent = text;
  els.status.classList.toggle("error", error);
  if (retry) {
    const button = el("button", null, "Повторить");
    button.type = "button";
    button.addEventListener("click", retry);
    els.status.append(button);
  }
}

function renderCategories(categories) {
  const total = categories.reduce((sum, c) => sum + c.count, 0);
  els.categories.replaceChildren(
    ...[{ category: null, count: total }, ...categories].map((c) => {
      const chip = el("button", "chip", c.category ?? "Все");
      chip.type = "button";
      chip.setAttribute("aria-pressed", String(c.category === activeCategory));
      chip.append(el("span", "count", c.count));
      chip.addEventListener("click", () => {
        activeCategory = c.category;
        load();
      });
      return chip;
    }),
  );
}

function renderCards(collections) {
  els.grid.replaceChildren();
  for (const c of collections) {
    const item = els.template.content.cloneNode(true);
    const card = item.querySelector(".card");
    drawCrate(card.querySelector(".crate"), c.title, c.product_count);
    card.querySelector(".card-category").textContent = c.category;
    card.querySelector(".card-title").textContent = c.title;
    card.querySelector(".card-meta").textContent = `${c.product_count} ${productWord(c.product_count)}`;
    card.querySelector(".tag").textContent = rub.format(c.totals.price);
    card.addEventListener("click", () => openDetails(c.id));
    els.grid.append(item);
  }
}

async function load() {
  const version = ++loadVersion;
  const category = activeCategory;
  const search = activeQuery;
  els.grid.replaceChildren();
  els.grid.setAttribute("aria-busy", "true");
  showStatus("Загружаем подборки…");
  try {
    const query = new URLSearchParams({ limit: DASHBOARD_LIMIT });
    if (category !== null) query.set("category", category);
    if (search) query.set("q", search);
    const [categories, collections] = await Promise.all([
      getJson("/api/categories"),
      getJson(`/api/collections?${query}`),
    ]);
    if (version !== loadVersion) return;
    renderCategories(categories);
    renderCards(collections);
    showStatus(collections.length ? "" : search || category !== null
      ? "Ничего не найдено. Измените запрос или категорию."
      : "Подборок пока нет. Их добавляет оператор через агента.");
    if (!heroPrinted && collections.length) {
      const latest = await getJson(`/api/collections/${collections[0].id}`);
      if (version !== loadVersion) return;
      heroPrinted = true;
      printHero(latest);
    }
  } catch {
    if (version !== loadVersion) return;
    els.grid.replaceChildren();
    showStatus("Не удалось загрузить подборки. Проверьте, что сервер запущен.", { error: true, retry: load });
  } finally {
    if (version === loadVersion) els.grid.setAttribute("aria-busy", "false");
  }
}

els.searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  // HTML maxlength counts UTF-16 units; the API counts Unicode code points.
  if (Array.from(els.searchQuery.value).length > 120) {
    els.searchQuery.setCustomValidity("Введите не больше 120 символов.");
    els.searchQuery.reportValidity();
    return;
  }
  activeQuery = els.searchQuery.value.trim();
  load();
});

els.searchQuery.addEventListener("input", () => els.searchQuery.setCustomValidity(""));

els.searchClear.addEventListener("click", () => {
  els.searchQuery.value = "";
  els.searchQuery.setCustomValidity("");
  activeQuery = "";
  els.searchQuery.focus();
  load();
});

// ---------- details ----------

function renderMacros(totals) {
  const parts = [
    ["Белки", totals.protein, totals.protein * 4, "var(--protein)"],
    ["Жиры", totals.fat, totals.fat * 9, "var(--fat)"],
    ["Углеводы", totals.carbs, totals.carbs * 4, "var(--carbs)"],
  ];
  const energy = parts.reduce((sum, [, , kcal]) => sum + kcal, 0) || 1;
  els.kcal.textContent = num.format(totals.kcal);
  els.macroBar.replaceChildren(
    ...parts.map(([, , kcal, color]) => {
      const span = el("span");
      span.style.width = `${(kcal / energy) * 100}%`;
      span.style.background = color;
      return span;
    }),
  );
  els.macros.replaceChildren(
    ...parts.map(([label, grams, kcal, color]) => {
      const box = el("div");
      const dt = el("dt", null, label);
      dt.style.setProperty("--swatch", color);
      box.append(dt, el("dd", null, `${num.format(grams)} г · ${Math.round((kcal / energy) * 100)}%`));
      return box;
    }),
  );
}

async function openDetails(id) {
  let c;
  try {
    c = await getJson(`/api/collections/${id}`);
  } catch {
    showStatus("Эта подборка больше недоступна. Список обновлён.", { error: true });
    load();
    return;
  }
  els.category.textContent = `Чек подборки № ${c.id}, ${c.category}`;
  els.title.textContent = c.title;
  els.meta.textContent = `${day.format(new Date(c.created_at))}, ${c.products.length} ${productWord(c.products.length)}`;
  receiptLines(els.products, c.products);
  els.total.textContent = rub.format(c.totals.price);
  renderMacros(c.totals);
  drawBarcode(els.barcode, c.cart_url);
  currentCartUrl = c.cart_url;
  els.open.href = c.cart_url;
  els.copied.textContent = "";
  els.details.showModal();
}

els.copy.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(currentCartUrl);
    els.copied.textContent = "Ссылка на корзину скопирована.";
  } catch {
    els.copied.textContent = `Скопируйте вручную: ${currentCartUrl}`;
  }
});

$("details-close").addEventListener("click", () => els.details.close());
els.details.addEventListener("click", (event) => {
  if (event.target === els.details) els.details.close();
});

load();
