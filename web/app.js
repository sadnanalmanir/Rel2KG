const graphsEl = document.getElementById("graphs");
const peopleEl = document.getElementById("people");
const questionsEl = document.getElementById("questions");
const healthEl = document.getElementById("health");
const oxLink = document.getElementById("oxigraph-link");
const bannerEl = document.getElementById("banner");
const viewPerson = document.getElementById("view-person");
const viewQuery = document.getElementById("view-query");
const viewMap = document.getElementById("view-map");
const graphNote = document.getElementById("graph-note");
const graphDetail = document.getElementById("graph-detail");
const graphToggles = document.getElementById("graph-toggles");

let focusEmail = "ada@campus.example";
let activeView = "person";
let enabledGraphs = new Set(["hr", "library", "registrar", "identity"]);
let graphMap = null;

function showBanner(text) {
  bannerEl.textContent = text;
  bannerEl.classList.toggle("hidden", !text);
}

async function getJson(url) {
  const res = await fetch(url);
  const body = await res.json().catch(() => ({}));
  if (!res.ok && !body.error) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  return body;
}

function chipRow(sources) {
  return ["hr", "library", "registrar"]
    .map((name) => `<span class="chip ${sources.includes(name) ? name : ""}">${name}</span>`)
    .join("");
}

function dl(entries) {
  return `<dl>${entries
    .filter(([, value]) => value)
    .map(([key, value]) => `<dt>${key}</dt><dd>${value}</dd>`)
    .join("")}</dl>`;
}

function renderPeople(people) {
  peopleEl.innerHTML = people
    .map(
      (person) => `
      <li>
        <button type="button" data-email="${person.email}" class="${person.email === focusEmail ? "active" : ""}">
          <span>${person.email}</span>
          <div class="chips">${chipRow(person.sources)}</div>
        </button>
      </li>`
    )
    .join("");
}

function renderQuestions(queries) {
  questionsEl.innerHTML = queries
    .map(
      (q) => `
      <button type="button" data-query="${q.name}">
        ${q.title}
      </button>`
    )
    .join("");
}

function showView(name) {
  activeView = name;
  viewPerson.classList.toggle("hidden", name !== "person");
  viewQuery.classList.toggle("hidden", name !== "query");
  viewMap.classList.toggle("hidden", name !== "map");
  for (const btn of document.querySelectorAll(".views [data-view]")) {
    btn.classList.toggle("active", btn.dataset.view === (name === "query" ? "person" : name));
  }
  if (name === "map") loadMap();
}

function renderPerson(card) {
  showView("person");
  document.getElementById("person-name").textContent = card.display;
  const aliases = (card.aliases || []).join(", ");
  document.getElementById("person-email").textContent = aliases
    ? `${card.email} · sameAs ${aliases}`
    : card.email;
  const flag = document.getElementById("person-flag");
  if (aliases) {
    flag.textContent = "Two IRIs · owl:sameAs";
    flag.className = "flag good";
  } else {
    flag.textContent = card.integrated
      ? "One person · three sources"
      : `Sources: ${card.sources.join(", ") || "none"}`;
    flag.className = `flag ${card.integrated ? "good" : "warn"}`;
  }

  const hr = card.hr.present
    ? dl([
        ["Given name", card.hr.given],
        ["Family name", card.hr.family],
        ["Department", card.hr.department],
        ["Code", card.hr.code],
        ["Hired", card.hr.hired_on],
      ])
    : `<p class="empty">Not in campus HR.</p>`;

  const loans = (card.library.loans || [])
    .map((loan) => {
      const back = loan.returnedOn ? `, returned ${loan.returnedOn}` : ", still out";
      return `<li>${loan.title} (${loan.loanedOn}${back})</li>`;
    })
    .join("");
  const authored = (card.library.authored || [])
    .map((book) => `<li>${book.title}</li>`)
    .join("");
  const libraryBits = [
    card.library.name ? dl([["Author name", card.library.name]]) : "",
    authored ? `<p class="hint">Authored</p><ul>${authored}</ul>` : "",
    loans ? `<p class="hint">Loans</p><ul>${loans}</ul>` : "",
  ].join("");
  const library = card.library.present
    ? libraryBits || `<p class="empty">No library facts.</p>`
    : `<p class="empty">Not in the library.</p>`;

  const enrollments = (card.registrar.enrollments || [])
    .map((row) => `<li>${row.code} ${row.title} · ${row.term}${row.grade ? ` · ${row.grade}` : ""}</li>`)
    .join("");
  const registrar = card.registrar.present
    ? enrollments
      ? `<ul>${enrollments}</ul>`
      : `<p class="empty">No enrollments.</p>`
    : `<p class="empty">Not in the registrar.</p>`;

  document.getElementById("sources").innerHTML = `
    <article class="col hr"><h3>HR · PostgreSQL</h3>${hr}</article>
    <article class="col library"><h3>Library · MySQL</h3>${library}</article>
    <article class="col registrar"><h3>Registrar · SQLite</h3>${registrar}</article>
  `;
}

function tableHtml(vars, rows) {
  if (!rows.length) return `<p class="empty">No rows.</p>`;
  const headers = vars && vars.length ? vars : Object.keys(rows[0]);
  return `<table><thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead>
    <tbody>${rows
      .map((row) => `<tr>${headers.map((h) => `<td>${row[h] ?? ""}</td>`).join("")}</tr>`)
      .join("")}</tbody></table>`;
}

function renderQuery(payload, meta) {
  showView("query");
  document.getElementById("query-name").textContent = meta.title;
  document.getElementById("sparql").textContent = payload.sparql;
  const flag = document.getElementById("query-flag");
  const result = document.getElementById("query-result");
  if (payload.kind === "ask") {
    const expected = meta.expected_ask;
    const ok = expected === undefined || payload.boolean === expected;
    flag.textContent = payload.boolean ? "ASK true" : "ASK false";
    flag.className = `flag ${ok ? "good" : "warn"}`;
    document.getElementById("query-meta").textContent = ok
      ? "Matches the expected boolean."
      : `Expected ${expected}.`;
    result.innerHTML = `<p class="flag ${payload.boolean ? "good" : "warn"}">${payload.boolean}</p>`;
    return;
  }
  const n = payload.rows.length;
  const expected = meta.expected_rows;
  const ok = expected === undefined || n === expected;
  flag.textContent = `${n} row${n === 1 ? "" : "s"}`;
  flag.className = `flag ${ok ? "good" : "warn"}`;
  document.getElementById("query-meta").textContent =
    expected === undefined ? "" : ok ? `Expected ${expected}.` : `Expected ${expected}, got ${n}.`;
  result.innerHTML = tableHtml(payload.vars, payload.rows);
}

async function openPerson(email) {
  focusEmail = email;
  for (const btn of peopleEl.querySelectorAll("button")) {
    btn.classList.toggle("active", btn.dataset.email === email);
  }
  for (const btn of questionsEl.querySelectorAll("button")) btn.classList.remove("active");
  const card = await getJson(`/api/person?email=${encodeURIComponent(email)}`);
  if (!card.ok && card.error) {
    showBanner(card.error);
    return;
  }
  renderPerson(card);
}

async function openQuery(name, meta) {
  for (const btn of questionsEl.querySelectorAll("button")) {
    btn.classList.toggle("active", btn.dataset.query === name);
  }
  for (const btn of peopleEl.querySelectorAll("button")) btn.classList.remove("active");
  const payload = await getJson(`/api/query/${name}`);
  if (!payload.ok && payload.error) {
    showBanner(payload.error);
    return;
  }
  renderQuery(payload, meta);
}

function describeNode(node) {
  if (!node) {
    graphDetail.innerHTML = `<p class="empty">Click a node. Drag to pan, scroll to zoom.</p>`;
    return;
  }
  const graphs = (node.graphs || []).join(", ") || "—";
  graphDetail.innerHTML = `
    <p class="kicker">${node.kind}</p>
    <h3>${node.label || node.id}</h3>
    ${node.email ? `<p class="mono">${node.email}</p>` : ""}
    <p class="hint">Graphs: ${graphs}</p>
    ${node.kind === "person" && node.email ? `<p class="hint">Opens the person card.</p>` : ""}
  `;
}

async function loadMap() {
  const graphs = ["hr", "library", "registrar", "identity"].filter((name) =>
    enabledGraphs.has(name)
  );
  if (!graphs.length) {
    enabledGraphs.add("hr");
    graphs.push("hr");
  }
  if (graphToggles) {
    for (const btn of graphToggles.querySelectorAll("button")) {
      btn.classList.toggle("active", enabledGraphs.has(btn.dataset.graph));
    }
  }
  const payload = await getJson(`/api/graph?graphs=${graphs.join(",")}`);
  if (!payload.ok && payload.error) {
    showBanner(payload.error);
    return;
  }
  if (!graphMap) {
    const canvas = document.getElementById("graph-canvas");
    graphMap = window.createNamedGraphMap(canvas, {
      onSelect(node) {
        describeNode(node);
        if (node && node.kind === "person" && node.email) openPerson(node.email);
      },
    });
  }
  graphMap.setData(payload);
  graphNote.textContent = `${payload.nodes.length} nodes · ${payload.edges.length} edges · ${graphs.join(", ")}`;
}

peopleEl.addEventListener("click", (event) => {
  const btn = event.target.closest("button[data-email]");
  if (btn) openPerson(btn.dataset.email);
});

document.querySelector(".views").addEventListener("click", (event) => {
  const btn = event.target.closest("button[data-view]");
  if (btn) showView(btn.dataset.view);
});

if (graphToggles) {
  graphToggles.innerHTML = ["hr", "library", "registrar", "identity"]
    .map((name) => `<button type="button" class="${name} active" data-graph="${name}">${name}</button>`)
    .join("");
  graphToggles.addEventListener("click", (event) => {
    const btn = event.target.closest("button[data-graph]");
    if (!btn) return;
    const name = btn.dataset.graph;
    if (enabledGraphs.has(name)) {
      if (enabledGraphs.size === 1) return;
      enabledGraphs.delete(name);
    } else {
      enabledGraphs.add(name);
    }
    if (activeView === "map") loadMap();
  });
}

async function boot() {
  const health = await getJson("/api/health");
  healthEl.textContent = health.ok ? `store · ${health.triples} triples` : "store down";
  healthEl.className = `pill ${health.ok && !health.empty ? "ok" : "bad"}`;
  if (health.oxigraph) oxLink.href = `${health.oxigraph.replace(/\/$/, "")}/`;
  focusEmail = health.focus_email || focusEmail;
  if (graphsEl) {
    graphsEl.innerHTML = (health.graphs || [])
      .map((g) => `<li class="${g.name}"><span>${g.name}</span><span>${g.triples}</span></li>`)
      .join("");
  }
  if (!health.ok || health.empty) {
    showBanner("Oxigraph has no graph yet. Run `make load` (after `make materialize`), then refresh.");
  }

  const people = health.ok ? await getJson("/api/people") : { people: [] };
  renderPeople(people.people || []);

  const catalog = await getJson("/api/queries");
  const queries = catalog.queries || [];
  renderQuestions(queries);
  questionsEl.addEventListener("click", (event) => {
    const btn = event.target.closest("button[data-query]");
    if (!btn) return;
    const meta = queries.find((q) => q.name === btn.dataset.query);
    openQuery(btn.dataset.query, meta || { title: btn.dataset.query });
  });

  if ((people.people || []).some((p) => p.email === focusEmail)) {
    await openPerson(focusEmail);
  }
}

boot().catch((err) => showBanner(err.message));
