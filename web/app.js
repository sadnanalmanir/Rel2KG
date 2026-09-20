const peopleEl = document.getElementById("people");
const questionsEl = document.getElementById("questions");
const healthEl = document.getElementById("health");
const oxLink = document.getElementById("oxigraph-link");
const bannerEl = document.getElementById("banner");
const viewPerson = document.getElementById("view-person");
const viewQuery = document.getElementById("view-query");

let focusEmail = "ada@campus.example";

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

function renderPerson(card) {
  viewQuery.classList.add("hidden");
  viewPerson.classList.remove("hidden");
  document.getElementById("person-name").textContent = card.display;
  document.getElementById("person-email").textContent = card.email;
  const flag = document.getElementById("person-flag");
  flag.textContent = card.integrated
    ? "One person · three sources"
    : `Sources: ${card.sources.join(", ") || "none"}`;
  flag.className = `flag ${card.integrated ? "good" : "warn"}`;

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
  const library = card.library.present
    ? `${dl([["Author name", card.library.name]])}${loans ? `<p class="hint">Loans</p><ul>${loans}</ul>` : "<p class='empty'>No loans.</p>"}`
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
  viewPerson.classList.add("hidden");
  viewQuery.classList.remove("hidden");
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

peopleEl.addEventListener("click", (event) => {
  const btn = event.target.closest("button[data-email]");
  if (btn) openPerson(btn.dataset.email);
});

async function boot() {
  const health = await getJson("/api/health");
  healthEl.textContent = health.ok ? `store · ${health.triples} triples` : "store down";
  healthEl.className = `pill ${health.ok && !health.empty ? "ok" : "bad"}`;
  if (health.oxigraph) oxLink.href = `${health.oxigraph.replace(/\/$/, "")}/`;
  focusEmail = health.focus_email || focusEmail;
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
