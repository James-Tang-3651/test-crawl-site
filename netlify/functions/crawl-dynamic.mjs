function htmlPage(title, body, options = {}) {
  const head = options.head ?? "";
  const script = options.script ?? "";
  const lang = options.lang ? ` lang="${options.lang}"` : "";

  return `<!doctype html>
<html${lang}>
  <head>
    <meta charset="utf-8" />
    <title>${title}</title>
    ${head}
  </head>
  <body>
    <header>
      <h1>${title}</h1>
    </header>
    <main>
      ${body}
    </main>
${script}
  </body>
</html>`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function htmlResponse(title, body, init = {}) {
  return new Response(htmlPage(title, body, init), {
    status: init.status ?? 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      ...(init.headers ?? {}),
    },
  });
}

function wait(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

const transientLoadFailures = 5;
const transientLoadCounts = new Map();
const intermittentFailCount = 3;
let intermittentErrorCount = 0;

const weatherImages = {
  sunny: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 160"><rect width="240" height="160" fill="#e7f5ff"/><circle cx="120" cy="78" r="34" fill="#ffd43b"/><g stroke="#f08c00" stroke-width="8" stroke-linecap="round"><path d="M120 18v18"/><path d="M120 120v18"/><path d="M60 78H42"/><path d="M198 78h-18"/><path d="m77 35 13 13"/><path d="m163 121-13-13"/><path d="m77 121 13-13"/><path d="m163 35-13 13"/></g></svg>',
  cloudy: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 160"><rect width="240" height="160" fill="#edf2ff"/><path fill="#adb5bd" d="M74 112c-21 0-38-15-38-34 0-18 15-32 34-34 10-21 32-34 57-34 34 0 62 24 65 55 16 5 27 18 27 34 0 19-17 34-38 34H74Z"/><path fill="#dee2e6" d="M66 124c-18 0-33-13-33-30 0-15 12-28 29-30 9-18 28-29 50-29 30 0 54 21 57 48 14 4 24 16 24 30 0 17-15 30-33 30H66Z"/></svg>',
  rainy: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 160"><rect width="240" height="160" fill="#e3fafc"/><path fill="#868e96" d="M74 92c-19 0-34-13-34-30 0-16 13-29 31-30 9-18 29-30 52-30 31 0 57 22 59 50 15 4 26 17 26 31 0 17-15 30-34 30H74Z"/><g stroke="#228be6" stroke-width="8" stroke-linecap="round"><path d="m76 126-10 20"/><path d="m118 126-10 20"/><path d="m160 126-10 20"/></g></svg>',
};

const defaultWeatherCity = "vancouver";
const weatherLocations = {
  vancouver: {name: "Vancouver, BC", sentenceName: "Vancouver BC"},
  surrey: {name: "Surrey, BC", sentenceName: "Surrey BC"},
  burnaby: {name: "Burnaby, BC", sentenceName: "Burnaby BC"},
  richmond: {name: "Richmond, BC", sentenceName: "Richmond BC"},
  toronto: {name: "Toronto, ON", sentenceName: "Toronto ON"},
};
for (const location of Object.values(weatherLocations)) {
  location.sourceUrl = `https://weather.gc.ca/city/jump_e.html?city=${encodeURIComponent(location.name)}`;
  location.sourceSentence = "Weather source: Environment and Climate Change Canada / weather.gc.ca.";
}

function vancouverToday() {
  const parts = new Intl.DateTimeFormat("en-US", {
    day: "2-digit",
    month: "2-digit",
    timeZone: "America/Vancouver",
    year: "numeric",
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.month}/${values.day}/${values.year}`;
}

function weatherImageKind(summary) {
  const normalized = summary.toLowerCase();
  if (["rain", "shower", "drizzle"].some((term) => normalized.includes(term))) {
    return "rainy";
  }
  if (["sun", "clear", "fair"].some((term) => normalized.includes(term))) {
    return "sunny";
  }
  return "cloudy";
}

function weatherImageSrc(kind) {
  return `data:image/svg+xml,${encodeURIComponent(weatherImages[kind])}`;
}

function weatherCityKey(city) {
  const normalized = String(city || defaultWeatherCity).trim().toLowerCase();
  return weatherLocations[normalized] ? normalized : defaultWeatherCity;
}

function parseWeather(html) {
  const conditionMatch = html.match(/Condition:\s*<\/[^>]+>\s*<[^>]+>\s*([^<]+)/i);
  const text = html.replace(/<[^>]+>/g, " ");
  const fallbackConditionMatch = conditionMatch
    ? null
    : text.match(
      /Condition:\s*([A-Za-z][A-Za-z ]+?)(?=\s+(Pressure|Temperature|Dew point|Humidity|Wind|Visibility):)/i,
    );
  const temperatureMatch = text.match(/Temperature:\s*(-?\d+(?:\.\d+)?)\s*°?\s*C/i);
  const summary = (conditionMatch?.[1] || fallbackConditionMatch?.[1] || "unavailable").trim().replace(/\s+/g, " ");
  const temperature = temperatureMatch?.[1] ? `${temperatureMatch[1]}°C` : "unavailable";
  return {summary: summary || "unavailable", temperature};
}

async function fetchWeather(city) {
  const cityKey = weatherCityKey(city);
  try {
    const response = await fetch(weatherLocations[cityKey].sourceUrl, {
      headers: {"user-agent": "crawl-test-site/1.0"},
      signal: AbortSignal.timeout(5000),
    });
    if (!response.ok) {
      return {summary: "unavailable", temperature: "unavailable"};
    }
    const html = await response.text();
    return parseWeather(html);
  } catch {
    return {summary: "unavailable", temperature: "unavailable"};
  }
}

async function weatherPayload(city = defaultWeatherCity) {
  const cityKey = weatherCityKey(city);
  const location = weatherLocations[cityKey];
  const weather = await fetchWeather(cityKey);
  const weatherKind = weatherImageKind(weather.summary);
  const imageAlt = `Generic ${weatherKind} weather image`;
  const today = vancouverToday();
  return {
    city: cityKey,
    location: location.name,
    sentence_location: location.sentenceName,
    date: today,
    summary: weather.summary,
    temperature: weather.temperature,
    sentence: `Today's date is ${today}, the weather in ${location.sentenceName} is ${weather.summary}.`,
    temperature_sentence: `The temperature in ${location.sentenceName} today is ${weather.temperature}.`,
    source_sentence: location.sourceSentence,
    image: {
      kind: weatherKind,
      src: weatherImageSrc(weatherKind),
      alt: imageAlt,
    },
  };
}

function queryPage(url) {
  const params = {};
  for (const [key, value] of url.searchParams.entries()) {
    params[key] = value;
  }

  const sortedParams = Object.fromEntries(
    Object.entries(params).sort(([left], [right]) => left.localeCompare(right)),
  );
  const content = JSON.stringify(sortedParams);
  const values = Object.values(sortedParams);
  const title = values.length ? `Query Page - ${values.join(", ")}` : "Query Page";
  return htmlResponse(escapeHtml(title), `<p>Query page content: ${escapeHtml(content)}</p>`);
}

function hasCookie(request, name, expectedValue) {
  const cookieHeader = request.headers.get("cookie") ?? "";
  return cookieHeader
    .split(";")
    .map((part) => part.trim())
    .some((part) => {
      const [cookieName, ...valueParts] = part.split("=");
      return cookieName === name && valueParts.join("=") === expectedValue;
    });
}

function acceptsFrench(request) {
  if (hasCookie(request, "site_language", "fr")) {
    return true;
  }

  const acceptLanguage = request.headers.get("accept-language") ?? "";
  return acceptLanguage
    .split(",")
    .some((part) => part.trim().toLowerCase().startsWith("fr"));
}

function aboutPage(request) {
  const commonHead = `
    <link rel="alternate" hreflang="en" href="/about" />
    <link rel="alternate" hreflang="fr" href="/fr/about" />
    <link rel="canonical" href="/about" />
    `;

  if (acceptsFrench(request)) {
    const body = `
    <article>
      <p>Ceci est une page rendue cote serveur avec du contenu ordinaire et deux pages enfants.</p>
      <a href="/absolute">Enfant absolu</a>
      <a href="/query-page/?sort=price">Page de tri par requete</a>
    </article>
    `;
    const headers = hasCookie(request, "site_language", "fr")
      ? {"set-cookie": "site_language=; Max-Age=0; Path=/; SameSite=Lax"}
      : {};

    return htmlResponse("Page A Propos", body, {
      head: `<meta http-equiv="Content-Language" content="fr" />${commonHead}`,
      headers,
      lang: "fr",
    });
  }

  const body = `
    <article>
      <p>This is a server-rendered page with ordinary content and two child pages.</p>
      <a href="/absolute">Absolute child</a>
      <a href="/query-page/?sort=price">Query sort page</a>
    </article>
    `;

  return htmlResponse("About Page", body, {
    head: `<meta http-equiv="Content-Language" content="en" />${commonHead}`,
    lang: "en",
  });
}

function localhostLink(url) {
  const localhostBase = url.port ? `http://localhost:${url.port}` : "http://localhost";
  const loopbackBase = url.port ? `http://127.0.0.1:${url.port}` : "http://127.0.0.1";
  const body = `
    <p>This page exposes absolute localhost and loopback links for crawler URL normalization tests.</p>
    <ul>
      <li><a href="${localhostBase}/about">Localhost About link</a></li>
      <li><a href="${loopbackBase}/about">127.0.0.1 About link</a></li>
      <li><a href="${localhostBase}/query-page/?from=localhost-link">Localhost query link</a></li>
    </ul>
    `;

  return htmlResponse("Localhost Links", body);
}

async function slowPage() {
  await wait(2500);
  return htmlResponse(
    "Slow Page",
    '<p>Slow page finished after a delay.</p><a href="/query-page/?ref=slow">Query from slow page</a>',
  );
}

function intermittentErrorPage() {
  const count = ++intermittentErrorCount;
  const cycleLen = 1 + intermittentFailCount;
  const position = (count - 1) % cycleLen;
  if (position > 0) {
    const remainingFails = cycleLen - position;
    return new Response(
      `Intermittent error (request ${count}, position ${position + 1} of ${cycleLen} in cycle). ` +
        `This page fails ${intermittentFailCount} times after each success. ` +
        `${remainingFails} more failure(s) before the next success.`,
      {
        status: 503,
        headers: {
          "content-type": "text/plain; charset=utf-8",
          "retry-after": "1",
        },
      },
    );
  }
  const successesSOFar = Math.floor((count - 1) / cycleLen) + 1;
  const body = `
    <p>This page simulates intermittent failures on a request cycle: it succeeds once, then
       fails the next ${intermittentFailCount} requests, then succeeds again, repeating indefinitely.</p>
    <p>Request ${count} — success #${successesSOFar}. The next ${intermittentFailCount} requests will return 503.</p>
    <a href="/query-page/?from=intermittent-error">Intermittent error child link</a>
    `;
  return htmlResponse("Intermittent Error Page", body);
}

function transientLoadPage(url) {
  const key = url.searchParams.get("key") || "default";
  const count = (transientLoadCounts.get(key) || 0) + 1;
  transientLoadCounts.set(key, count);

  // Netlify may recycle function instances, so Render/FastAPI remains the
  // authoritative host for deterministic transient-load testing.
  if (count <= transientLoadFailures) {
    return new Response(
      `Transient load attempt ${count} failed. Attempt ${transientLoadFailures + 1} will succeed.`,
      {
        status: 503,
        headers: {
          "content-type": "text/plain; charset=utf-8",
          "retry-after": "1",
        },
      },
    );
  }

  return htmlResponse(
    "Transient Load Succeeded",
    `
    <p>Transient load succeeded for key <code>${escapeHtml(key)}</code> after ${count} attempts.</p>
    <p>Retry count: ${count - transientLoadFailures - 1}, you may access this properly now.</p>
    <p>Failed access count before success: ${transientLoadFailures}.</p>
    <p>This route simulates a site migration or update that fails temporarily before becoming crawlable.</p>
    <a href="/transient-load-child">Transient load child page</a>
    `,
  );
}

function transientLoadReset(url) {
  const key = url.searchParams.get("key") || "default";
  transientLoadCounts.delete(key);
  return new Response(JSON.stringify({key, reset: true, failure_count_before_success: transientLoadFailures}), {
    headers: {"content-type": "application/json; charset=utf-8"},
  });
}

function transientLoadStatus(url) {
  const key = url.searchParams.get("key") || "default";
  const count = transientLoadCounts.get(key) || 0;
  return new Response(JSON.stringify({
    key,
    access_count: count,
    failed_access_count: Math.min(count, transientLoadFailures),
    failure_count_before_success: transientLoadFailures,
    retry_count: Math.max(0, count - transientLoadFailures - 1),
    can_access_now: count >= transientLoadFailures,
  }), {
    headers: {"content-type": "application/json; charset=utf-8"},
  });
}

async function status504Page() {
  return new Response("Gateway timeout test page", {
    status: 504,
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "retry-after": "3",
    },
  });
}

async function vancouverDailyWeatherReport() {
  const weather = await weatherPayload(defaultWeatherCity);
  const options = Object.entries(weatherLocations)
    .map(([cityKey, location]) => {
      const selected = cityKey === weather.city ? " selected" : "";
      return `<option value="${escapeHtml(cityKey)}"${selected}>${escapeHtml(location.name)}</option>`;
    })
    .join("");
  const body = `
    <article>
      <label for="weather-city">Weather city</label>
      <select id="weather-city">${options}</select>
      <p id="weather-date-sentence">Today's date is ${escapeHtml(weather.date)}, the weather in ${escapeHtml(weather.sentence_location)} is ${escapeHtml(weather.summary)}.</p>
      <p id="weather-temperature-sentence">The temperature in ${escapeHtml(weather.sentence_location)} today is ${escapeHtml(weather.temperature)}.</p>
      <img id="weather-image" src="${escapeHtml(weather.image.src)}" alt="${escapeHtml(weather.image.alt)}" width="240" height="160" />
      <p>This daily weather report updates by Vancouver local date at 00:00 America/Vancouver.</p>
      <p id="weather-source-sentence">${escapeHtml(weather.source_sentence)}</p>
    </article>
    <script>
      const weatherCitySelect = document.querySelector("#weather-city");
      const weatherDateSentence = document.querySelector("#weather-date-sentence");
      const weatherTemperatureSentence = document.querySelector("#weather-temperature-sentence");
      const weatherSourceSentence = document.querySelector("#weather-source-sentence");
      const weatherImage = document.querySelector("#weather-image");

      async function updateWeatherCity() {
        const response = await fetch(\`/weather/vancouver-daily-report/data.json?city=\${encodeURIComponent(weatherCitySelect.value)}\`);
        const payload = await response.json();
        weatherDateSentence.textContent = payload.sentence;
        weatherTemperatureSentence.textContent = payload.temperature_sentence;
        weatherSourceSentence.textContent = payload.source_sentence;
        weatherImage.src = payload.image.src;
        weatherImage.alt = payload.image.alt;
      }

      weatherCitySelect.addEventListener("change", updateWeatherCity);
    </script>
    `;

  return htmlResponse("Vancouver daily weather report", body);
}

async function vancouverDailyWeatherReportData(url) {
  const payload = await weatherPayload(url.searchParams.get("city") || defaultWeatherCity);
  return new Response(JSON.stringify(payload), {
    headers: {"content-type": "application/json; charset=utf-8"},
  });
}

const vancouverLatitude = 49.2827;
const vancouverLongitude = -123.1207;
const forecastApiUrl =
  `https://api.open-meteo.com/v1/forecast?latitude=${vancouverLatitude}&longitude=${vancouverLongitude}` +
  "&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=America%2FVancouver&forecast_days=7";
const forecastSourceSentence = "Weather source: Open-Meteo / open-meteo.com.";

// WMO weather interpretation codes returned by Open-Meteo's "weathercode" field.
const wmoWeatherSummaries = {
  0: "Clear sky",
  1: "Mainly clear",
  2: "Partly cloudy",
  3: "Overcast",
  45: "Fog",
  48: "Depositing rime fog",
  51: "Light drizzle",
  53: "Moderate drizzle",
  55: "Dense drizzle",
  56: "Light freezing drizzle",
  57: "Dense freezing drizzle",
  61: "Slight rain",
  63: "Moderate rain",
  65: "Heavy rain",
  66: "Light freezing rain",
  67: "Heavy freezing rain",
  71: "Slight snow",
  73: "Moderate snow",
  75: "Heavy snow",
  77: "Snow grains",
  80: "Slight rain showers",
  81: "Moderate rain showers",
  82: "Violent rain showers",
  85: "Slight snow showers",
  86: "Heavy snow showers",
  95: "Thunderstorm",
  96: "Thunderstorm with slight hail",
  99: "Thunderstorm with heavy hail",
};

function wmoSummary(code) {
  return wmoWeatherSummaries[code] ?? "unavailable";
}

function formatForecastTemp(value) {
  return typeof value === "number" ? `${Math.round(value)}°C` : "unavailable";
}

function formatForecastDay(iso) {
  const names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  const [year, month, day] = String(iso).split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  const mm = String(month).padStart(2, "0");
  const dd = String(day).padStart(2, "0");
  return {name: names[date.getUTCDay()], date: `${mm}/${dd}/${year}`};
}

async function fetchVancouverForecast() {
  try {
    const response = await fetch(forecastApiUrl, {
      headers: {"user-agent": "crawl-test-site/1.0"},
      signal: AbortSignal.timeout(5000),
    });
    if (!response.ok) {
      return [];
    }
    const data = await response.json();
    const daily = data.daily || {};
    const times = daily.time || [];
    const codes = daily.weathercode || [];
    const highs = daily.temperature_2m_max || [];
    const lows = daily.temperature_2m_min || [];
    return times.map((iso, index) => {
      const {name, date} = formatForecastDay(iso);
      return {
        name,
        date,
        summary: wmoSummary(codes[index]),
        high: formatForecastTemp(highs[index]),
        low: formatForecastTemp(lows[index]),
      };
    });
  } catch {
    return [];
  }
}

async function vancouverWeeklyWeatherReport() {
  const location = weatherLocations[defaultWeatherCity];
  const forecast = await fetchVancouverForecast();

  if (forecast.length === 0) {
    const body = `
    <article>
      <p id="weather-week-range">Weekly weather forecast for ${escapeHtml(location.sentenceName)} is unavailable right now.</p>
      <p id="weather-source-sentence">${escapeHtml(forecastSourceSentence)}</p>
    </article>
    `;
    return htmlResponse("Vancouver weekly weather report", body);
  }

  const weekStart = forecast[0].date;
  const weekEnd = forecast[forecast.length - 1].date;
  const imageKind = weatherImageKind(forecast[0].summary);
  const imageSrc = weatherImageSrc(imageKind);
  const rows = forecast
    .map(
      (day) =>
        `<tr><th scope="row">${escapeHtml(day.name)}</th><td>${escapeHtml(day.date)}</td>` +
        `<td>${escapeHtml(day.summary)}</td><td>${escapeHtml(day.high)}</td><td>${escapeHtml(day.low)}</td></tr>`,
    )
    .join("");
  const body = `
    <article>
      <p id="weather-week-range">Weekly weather forecast for ${escapeHtml(location.sentenceName)}, ${escapeHtml(weekStart)} to ${escapeHtml(weekEnd)}.</p>
      <img id="weather-image" src="${escapeHtml(imageSrc)}" alt="Generic ${escapeHtml(imageKind)} weather image" width="240" height="160" />
      <table class="weekly-weather">
        <thead>
          <tr><th scope="col">Day</th><th scope="col">Date</th><th scope="col">Outlook</th><th scope="col">High</th><th scope="col">Low</th></tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
      <p>This weekly weather forecast updates by Vancouver local date each Monday at 00:00 America/Vancouver.</p>
      <p id="weather-source-sentence">${escapeHtml(forecastSourceSentence)}</p>
    </article>
    `;

  return htmlResponse("Vancouver weekly weather report", body);
}

export default async function handler(request) {
  const url = new URL(request.url);

  // Site links place a slash right before the query string (/path/?query),
  // so treat /path/ and /path as the same route.
  if (url.pathname.length > 1 && url.pathname.endsWith("/")) {
    url.pathname = url.pathname.slice(0, -1);
  }

  if (url.pathname === "/redirect-middle") {
    return Response.redirect(new URL("/redirect-target", url), 307);
  }

  if (url.pathname === "/accept-consent") {
    return new Response(null, {
      status: 302,
      headers: {
        location: "/consent",
        "set-cookie": "site_consent=accepted; Max-Age=3600; Path=/; SameSite=Lax",
      },
    });
  }

  if (url.pathname === "/about") {
    return aboutPage(request);
  }

  if (url.pathname === "/query-page") {
    return queryPage(url);
  }

  if (url.pathname === "/localhost-link") {
    return localhostLink(url);
  }

  if (url.pathname === "/slow") {
    return slowPage();
  }

  if (url.pathname === "/status/504") {
    return status504Page();
  }

  if (url.pathname === "/intermittent-error") {
    return intermittentErrorPage();
  }

  if (url.pathname === "/transient-load") {
    return transientLoadPage(url);
  }

  if (url.pathname === "/transient-load/reset") {
    return transientLoadReset(url);
  }

  if (url.pathname === "/transient-load/status") {
    return transientLoadStatus(url);
  }

  if (url.pathname === "/weather/vancouver-daily-report") {
    return vancouverDailyWeatherReport();
  }

  if (url.pathname === "/weather/vancouver-daily-report/data.json") {
    return vancouverDailyWeatherReportData(url);
  }

  if (url.pathname === "/weather/vancouver-weekly-report") {
    return vancouverWeeklyWeatherReport();
  }

  return new Response("Not found", {
    status: 404,
    headers: {"content-type": "text/plain; charset=utf-8"},
  });
}

export const config = {
  path: [
    "/accept-consent",
    "/about",
    "/about/",
    "/intermittent-error",
    "/localhost-link",
    "/localhost-link/",
    "/query-page",
    "/query-page/",
    "/redirect-middle",
    "/slow",
    "/slow/",
    "/status/504",
    "/transient-load",
    "/transient-load/",
    "/transient-load/reset",
    "/transient-load/status",
    "/weather/vancouver-daily-report",
    "/weather/vancouver-daily-report/",
    "/weather/vancouver-daily-report/data.json",
    "/weather/vancouver-weekly-report",
  ],
};
