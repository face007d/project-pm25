const fs = require("node:fs");
const fsp = require("node:fs/promises");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

const START_DATE = "2020-06-13";
const END_DATE = "2026-06-12";
const AIR4THAI_PARAMS = ["PM25", "PM10", "O3", "CO", "NO2", "SO2", "WS", "WD", "TEMP", "RH", "BP", "RAIN"];
const WEATHER_PARAMS = [
  "temperature_2m",
  "relative_humidity_2m",
  "pressure_msl",
  "precipitation",
  "wind_speed_10m",
  "wind_direction_10m",
];
const OPEN_METEO_AQ_PARAMS = ["pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide", "ozone"];

const STATIONS = [
  {
    station_id: "88t",
    province: "นครพนม",
    station_name: "สถานีอุตุนิยมวิทยานครพนม ต.ในเมือง อ.เมือง, นครพนม",
    latitude: 17.412345,
    longitude: 104.7786123,
  },
  {
    station_id: "106t",
    province: "บึงกาฬ",
    station_name: "สวนสาธารณะหนองบึงกาฬ ต.บึงกาฬ อ.เมือง, จ.บึงกาฬ",
    latitude: 18.362008,
    longitude: 103.65977,
  },
  {
    station_id: "82t",
    province: "หนองคาย",
    station_name: "สวนสาธารณะหนองถิ่น ต.มีชัย อ.เมือง, หนองคาย",
    latitude: 17.87748,
    longitude: 102.728925,
  },
  {
    station_id: "83t",
    province: "อุบลราชธานี",
    station_name: "ศูนย์แสดงและจำหน่ายสินค้า OTOP จังหวัดอุบลราชธานี ต.ในเมือง อ.เมือง, อุบลราชธานี",
    latitude: 15.245413,
    longitude: 104.846219,
  },
  {
    station_id: "102t",
    province: "มุกดาหาร",
    station_name: "สนามกีฬากลางจังหวัดมุกดาหาร ต.มุกดาหาร อ.เมือง, มุกดาหาร",
    latitude: 16.54257,
    longitude: 104.7192,
  },
];

const OUTPUT_DIR = path.resolve("data", "processed");
const BUILD_DIR = path.join(OUTPUT_DIR, "_pm25_xlsx_build");
const OUTPUT_XLSX = path.join(OUTPUT_DIR, "pm25_training_dataset_5stations_2020-2026.xlsx");

const DATA_HEADERS = [
  "datetime",
  "province",
  "station_id",
  "station_name",
  "latitude",
  "longitude",
  "pm25",
  "pm10",
  "o3",
  "co",
  "no2",
  "so2",
  "wind_speed",
  "wind_direction",
  "temperature",
  "relative_humidity",
  "pressure",
  "precipitation",
  "airquality_source",
  "weather_source",
];

const QUALITY_HEADERS = [
  "station_id",
  "province",
  "station_name",
  "total_hours_in_6y_frame",
  "air4thai_train_ready_rows",
  "air4thai_pm25_count",
  "air4thai_pm25_coverage_pct",
  "openmeteo_pm25_count",
  "openmeteo_pm25_coverage_pct",
  "pm10_count",
  "o3_count",
  "co_count",
  "no2_count",
  "so2_count",
  "weather_rows",
  "weather_coverage_pct",
];

function dateOnly(date) {
  return date.toISOString().slice(0, 10);
}

function parseDate(dateText) {
  return new Date(`${dateText}T00:00:00+07:00`);
}

function addDays(date, days) {
  const copy = new Date(date.getTime());
  copy.setDate(copy.getDate() + days);
  return copy;
}

function monthChunks(startText, endText) {
  const chunks = [];
  let start = parseDate(startText);
  const end = parseDate(endText);
  while (start <= end) {
    const nextMonth = new Date(start.getTime());
    nextMonth.setMonth(nextMonth.getMonth() + 1, 1);
    const chunkEnd = addDays(nextMonth, -1) < end ? addDays(nextMonth, -1) : end;
    chunks.push([dateOnly(start), dateOnly(chunkEnd)]);
    start = addDays(chunkEnd, 1);
  }
  return chunks;
}

function normalizeDateTime(text) {
  return text.replace("T", " ").replace(/:00$/, ":00:00");
}

function numericOrBlank(value) {
  if (value === null || value === undefined || value === "") return null;
  const num = Number(value);
  if (!Number.isFinite(num)) return null;
  if (num === -1 || num === -999) return null;
  return num;
}

function xmlEscape(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function colName(index) {
  let name = "";
  let n = index + 1;
  while (n > 0) {
    const rem = (n - 1) % 26;
    name = String.fromCharCode(65 + rem) + name;
    n = Math.floor((n - 1) / 26);
  }
  return name;
}

function cell(value, row, col, style = 0) {
  if (value === null || value === undefined || value === "") return "";
  const ref = `${colName(col)}${row}`;
  const styleAttr = style ? ` s="${style}"` : "";
  if (typeof value === "number") {
    return `<c r="${ref}"${styleAttr}><v>${value}</v></c>`;
  }
  return `<c r="${ref}" t="inlineStr"${styleAttr}><is><t>${xmlEscape(value)}</t></is></c>`;
}

function rowXml(values, rowNumber, style = 0) {
  return `<row r="${rowNumber}">${values.map((value, index) => cell(value, rowNumber, index, style)).join("")}</row>\n`;
}

async function fetchJson(url, retries = 3) {
  let lastError;
  for (let attempt = 1; attempt <= retries; attempt += 1) {
    try {
      const response = await fetch(url, {
        headers: {
          "User-Agent": "Mozilla/5.0 dataset-builder",
          Accept: "application/json,text/plain,*/*",
        },
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const text = await response.text();
      return JSON.parse(text);
    } catch (error) {
      lastError = error;
      await new Promise((resolve) => setTimeout(resolve, 350 * attempt));
    }
  }
  throw lastError;
}

async function fetchAir4Thai(station) {
  const rows = new Map();
  const chunks = monthChunks(START_DATE, END_DATE);
  for (const [sdate, edate] of chunks) {
    const url =
      "http://air4thai.com/forweb/getHistoryData.php" +
      `?stationID=${station.station_id}` +
      `&param=${AIR4THAI_PARAMS.join(",")}` +
      "&type=hr" +
      `&sdate=${sdate}` +
      `&edate=${edate}` +
      "&stime=00&etime=23";
    const payload = await fetchJson(url);
    const stationPayload = payload?.stations?.[0];
    for (const item of stationPayload?.data || []) {
      rows.set(item.DATETIMEDATA, {
        pm25: numericOrBlank(item.PM25),
        pm10: numericOrBlank(item.PM10),
        o3: numericOrBlank(item.O3),
        co: numericOrBlank(item.CO),
        no2: numericOrBlank(item.NO2),
        so2: numericOrBlank(item.SO2),
      });
    }
    await new Promise((resolve) => setTimeout(resolve, 80));
  }
  return rows;
}

async function fetchWeather(station) {
  const query = new URLSearchParams({
    latitude: String(station.latitude),
    longitude: String(station.longitude),
    start_date: START_DATE,
    end_date: END_DATE,
    hourly: WEATHER_PARAMS.join(","),
    timezone: "Asia/Bangkok",
  });
  const url = `https://archive-api.open-meteo.com/v1/archive?${query.toString()}`;
  const payload = await fetchJson(url);
  const hourly = payload.hourly || {};
  const rows = new Map();
  const times = hourly.time || [];
  for (let i = 0; i < times.length; i += 1) {
    rows.set(normalizeDateTime(times[i]), {
      wind_speed: numericOrBlank(hourly.wind_speed_10m?.[i]),
      wind_direction: numericOrBlank(hourly.wind_direction_10m?.[i]),
      temperature: numericOrBlank(hourly.temperature_2m?.[i]),
      relative_humidity: numericOrBlank(hourly.relative_humidity_2m?.[i]),
      pressure: numericOrBlank(hourly.pressure_msl?.[i]),
      precipitation: numericOrBlank(hourly.precipitation?.[i]),
    });
  }
  return rows;
}

async function fetchOpenMeteoAirQuality(station) {
  const query = new URLSearchParams({
    latitude: String(station.latitude),
    longitude: String(station.longitude),
    start_date: START_DATE,
    end_date: END_DATE,
    hourly: OPEN_METEO_AQ_PARAMS.join(","),
    timezone: "Asia/Bangkok",
    domains: "cams_global",
  });
  const url = `https://air-quality-api.open-meteo.com/v1/air-quality?${query.toString()}`;
  const payload = await fetchJson(url);
  const hourly = payload.hourly || {};
  const rows = new Map();
  const times = hourly.time || [];
  for (let i = 0; i < times.length; i += 1) {
    rows.set(normalizeDateTime(times[i]), {
      pm25: numericOrBlank(hourly.pm2_5?.[i]),
      pm10: numericOrBlank(hourly.pm10?.[i]),
      o3: numericOrBlank(hourly.ozone?.[i]),
      co: numericOrBlank(hourly.carbon_monoxide?.[i]),
      no2: numericOrBlank(hourly.nitrogen_dioxide?.[i]),
      so2: numericOrBlank(hourly.sulphur_dioxide?.[i]),
    });
  }
  return rows;
}

function hourlyDateTimes() {
  const result = [];
  let current = parseDate(START_DATE);
  const end = parseDate(END_DATE);
  end.setHours(23, 0, 0, 0);
  while (current <= end) {
    const y = current.getFullYear();
    const m = String(current.getMonth() + 1).padStart(2, "0");
    const d = String(current.getDate()).padStart(2, "0");
    const h = String(current.getHours()).padStart(2, "0");
    result.push(`${y}-${m}-${d} ${h}:00:00`);
    current.setHours(current.getHours() + 1);
  }
  return result;
}

async function writeSheet(sheetPath, headers, rows, options = {}) {
  await fsp.mkdir(path.dirname(sheetPath), { recursive: true });
  const stream = fs.createWriteStream(sheetPath, { encoding: "utf8" });
  stream.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n');
  stream.write('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">\n');
  stream.write("<sheetViews><sheetView workbookViewId=\"0\"><pane ySplit=\"1\" topLeftCell=\"A2\" activePane=\"bottomLeft\" state=\"frozen\"/></sheetView></sheetViews>\n");
  if (options.widths) {
    stream.write("<cols>");
    options.widths.forEach((width, idx) => {
      stream.write(`<col min="${idx + 1}" max="${idx + 1}" width="${width}" customWidth="1"/>`);
    });
    stream.write("</cols>\n");
  }
  stream.write("<sheetData>\n");
  stream.write(rowXml(headers, 1, 1));
  let rowNumber = 2;
  for await (const values of rows) {
    stream.write(rowXml(values, rowNumber));
    rowNumber += 1;
  }
  stream.write("</sheetData>\n");
  const lastCol = colName(headers.length - 1);
  stream.write(`<autoFilter ref="A1:${lastCol}${Math.max(1, rowNumber - 1)}"/>\n`);
  stream.write("</worksheet>");
  await new Promise((resolve, reject) => {
    stream.end(resolve);
    stream.on("error", reject);
  });
  return rowNumber - 2;
}

async function* arrayRows(rows) {
  for (const row of rows) yield row;
}

function dataRow(station, datetime, air, weather, airSource = air ? "Air4Thai" : "") {
  return [
    datetime,
    station.province,
    station.station_id,
    station.station_name,
    station.latitude,
    station.longitude,
    air?.pm25 ?? null,
    air?.pm10 ?? null,
    air?.o3 ?? null,
    air?.co ?? null,
    air?.no2 ?? null,
    air?.so2 ?? null,
    weather?.wind_speed ?? null,
    weather?.wind_direction ?? null,
    weather?.temperature ?? null,
    weather?.relative_humidity ?? null,
    weather?.pressure ?? null,
    weather?.precipitation ?? null,
    airSource,
    weather ? "Open-Meteo" : "",
  ];
}

async function writeWorkbookParts(sheetRowCounts) {
  await fsp.mkdir(path.join(BUILD_DIR, "_rels"), { recursive: true });
  await fsp.mkdir(path.join(BUILD_DIR, "docProps"), { recursive: true });
  await fsp.mkdir(path.join(BUILD_DIR, "xl", "_rels"), { recursive: true });
  await fsp.mkdir(path.join(BUILD_DIR, "xl", "worksheets"), { recursive: true });

  const sheets = [
    ["train_ready_pm25", 1],
    ["model_ready_openmeteo_aq", 2],
    ["dataset_full_6y", 3],
    ["stations", 4],
    ["data_quality", 5],
    ["sources", 6],
  ];

  await fsp.writeFile(
    path.join(BUILD_DIR, "[Content_Types].xml"),
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  ${sheets.map(([, id]) => `<Override PartName="/xl/worksheets/sheet${id}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`).join("\n  ")}
</Types>`,
  );

  await fsp.writeFile(
    path.join(BUILD_DIR, "_rels", ".rels"),
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>`,
  );

  await fsp.writeFile(
    path.join(BUILD_DIR, "xl", "workbook.xml"),
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    ${sheets.map(([name, id]) => `<sheet name="${name}" sheetId="${id}" r:id="rId${id}"/>`).join("\n    ")}
  </sheets>
</workbook>`,
  );

  await fsp.writeFile(
    path.join(BUILD_DIR, "xl", "_rels", "workbook.xml.rels"),
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  ${sheets.map(([, id]) => `<Relationship Id="rId${id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${id}.xml"/>`).join("\n  ")}
  <Relationship Id="rId7" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>`,
  );

  await fsp.writeFile(
    path.join(BUILD_DIR, "xl", "styles.xml"),
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF0F766E"/><bgColor indexed="64"/></patternFill></fill></fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="1" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>`,
  );

  await fsp.writeFile(
    path.join(BUILD_DIR, "docProps", "core.xml"),
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>PM2.5 Training Dataset - 5 Stations</dc:title>
  <dc:creator>Codex</dc:creator>
  <dcterms:created xsi:type="dcterms:W3CDTF">${new Date().toISOString()}</dcterms:created>
</cp:coreProperties>`,
  );

  await fsp.writeFile(
    path.join(BUILD_DIR, "docProps", "app.xml"),
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex Dataset Builder</Application>
  <DocSecurity>0</DocSecurity>
  <ScaleCrop>false</ScaleCrop>
  <HeadingPairs><vt:vector size="2" baseType="variant"><vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant><vt:variant><vt:i4>6</vt:i4></vt:variant></vt:vector></HeadingPairs>
  <TitlesOfParts><vt:vector size="6" baseType="lpstr">${sheets.map(([name]) => `<vt:lpstr>${name}</vt:lpstr>`).join("")}</vt:vector></TitlesOfParts>
  <Company></Company>
</Properties>`,
  );
}

function zipWorkbook() {
  if (fs.existsSync(OUTPUT_XLSX)) fs.rmSync(OUTPUT_XLSX);
  const tempZip = `${OUTPUT_XLSX}.zip`;
  if (fs.existsSync(tempZip)) fs.rmSync(tempZip);
  const quote = (value) => `'${String(value).replace(/'/g, "''")}'`;
  const command = `
Add-Type -AssemblyName System.IO.Compression.FileSystem
$source = ${quote(BUILD_DIR)}
$destination = ${quote(tempZip)}
if (Test-Path -LiteralPath $destination) { Remove-Item -LiteralPath $destination -Force }
$zip = [System.IO.Compression.ZipFile]::Open($destination, [System.IO.Compression.ZipArchiveMode]::Create)
try {
  Get-ChildItem -LiteralPath $source -Recurse -File | ForEach-Object {
    $relative = [System.IO.Path]::GetRelativePath($source, $_.FullName).Replace([char]92, [char]47)
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $_.FullName, $relative, [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
  }
} finally {
  $zip.Dispose()
}
Move-Item -LiteralPath $destination -Destination ${quote(OUTPUT_XLSX)} -Force
`;
  execFileSync("powershell.exe", ["-NoProfile", "-Command", command], { stdio: "inherit" });
}

async function main() {
  await fsp.mkdir(OUTPUT_DIR, { recursive: true });
  await fsp.rm(BUILD_DIR, { recursive: true, force: true });
  await fsp.mkdir(path.join(BUILD_DIR, "xl", "worksheets"), { recursive: true });

  const allDateTimes = hourlyDateTimes();
  const stationData = new Map();

  for (const station of STATIONS) {
    console.log(`Downloading ${station.province} (${station.station_id})`);
    const [air, weather, modelAq] = await Promise.all([
      fetchAir4Thai(station),
      fetchWeather(station),
      fetchOpenMeteoAirQuality(station),
    ]);
    stationData.set(station.station_id, { air, weather, modelAq });
  }

  async function* fullRows() {
    for (const station of STATIONS) {
      const { air, weather } = stationData.get(station.station_id);
      for (const datetime of allDateTimes) {
        yield dataRow(station, datetime, air.get(datetime), weather.get(datetime));
      }
    }
  }

  async function* trainReadyRows() {
    for (const station of STATIONS) {
      const { air, weather } = stationData.get(station.station_id);
      const datetimes = Array.from(air.keys()).sort();
      for (const datetime of datetimes) {
        const airRow = air.get(datetime);
        if (airRow?.pm25 !== null && airRow?.pm25 !== undefined) {
          yield dataRow(station, datetime, airRow, weather.get(datetime));
        }
      }
    }
  }

  async function* modelReadyOpenMeteoRows() {
    for (const station of STATIONS) {
      const { modelAq, weather } = stationData.get(station.station_id);
      for (const datetime of allDateTimes) {
        const aqRow = modelAq.get(datetime);
        if (aqRow?.pm25 !== null && aqRow?.pm25 !== undefined) {
          yield dataRow(station, datetime, aqRow, weather.get(datetime), "Open-Meteo Air Quality");
        }
      }
    }
  }

  const stationRows = STATIONS.map((station) => [
    station.station_id,
    station.province,
    station.station_name,
    station.latitude,
    station.longitude,
  ]);

  const qualityRows = STATIONS.map((station) => {
    const { air, weather, modelAq } = stationData.get(station.station_id);
    const airRows = Array.from(air.values());
    const count = (key) => airRows.filter((row) => row[key] !== null && row[key] !== undefined).length;
    const pm25Count = count("pm25");
    const openMeteoPm25Count = Array.from(modelAq.values()).filter((row) => row.pm25 !== null && row.pm25 !== undefined).length;
    const weatherRows = allDateTimes.filter((datetime) => weather.has(datetime)).length;
    return [
      station.station_id,
      station.province,
      station.station_name,
      allDateTimes.length,
      pm25Count,
      pm25Count,
      Number(((pm25Count / allDateTimes.length) * 100).toFixed(2)),
      openMeteoPm25Count,
      Number(((openMeteoPm25Count / allDateTimes.length) * 100).toFixed(2)),
      count("pm10"),
      count("o3"),
      count("co"),
      count("no2"),
      count("so2"),
      weatherRows,
      Number(((weatherRows / allDateTimes.length) * 100).toFixed(2)),
    ];
  });

  const sourceRows = [
    ["date_range", `${START_DATE} 00:00:00 to ${END_DATE} 23:00:00`],
    ["air_quality_source", "Air4Thai: http://air4thai.com/forweb/getHistoryData.php"],
    ["model_air_quality_source", "Open-Meteo Air Quality API / CAMS global: https://air-quality-api.open-meteo.com/v1/air-quality"],
    ["weather_source", "Open-Meteo Historical Weather API: https://archive-api.open-meteo.com/v1/archive"],
    ["air_quality_note", "Pollutant columns are blank where Air4Thai did not return historical measurements for the station/time."],
    ["openmeteo_aq_note", "Open-Meteo CAMS global air quality is gridded model data, not station measurement. Global availability starts in August 2022, so older PM values can be blank."],
    ["weather_note", "Weather columns are from Open-Meteo hourly archive and cover the full 6-year frame where available."],
    ["train_ready_pm25", "Rows where Air4Thai station-measured pm25 is present. Use this when you need measured station data only."],
    ["model_ready_openmeteo_aq", "Rows where Open-Meteo model pm25 is present. Use this for a longer training set when gridded model pollutant data is acceptable."],
    ["dataset_full_6y", "Full hourly grid for the five stations; useful for merging, checking missingness, or future backfill."],
  ];

  const widths = [20, 14, 12, 55, 12, 12, 10, 10, 10, 10, 10, 10, 12, 14, 12, 18, 12, 14, 18, 16];
  const sheetRowCounts = {};
  sheetRowCounts.train = await writeSheet(path.join(BUILD_DIR, "xl", "worksheets", "sheet1.xml"), DATA_HEADERS, trainReadyRows(), { widths });
  sheetRowCounts.openmeteo_model = await writeSheet(path.join(BUILD_DIR, "xl", "worksheets", "sheet2.xml"), DATA_HEADERS, modelReadyOpenMeteoRows(), { widths });
  sheetRowCounts.full = await writeSheet(path.join(BUILD_DIR, "xl", "worksheets", "sheet3.xml"), DATA_HEADERS, fullRows(), { widths });
  sheetRowCounts.stations = await writeSheet(
    path.join(BUILD_DIR, "xl", "worksheets", "sheet4.xml"),
    ["station_id", "province", "station_name", "latitude", "longitude"],
    arrayRows(stationRows),
    { widths: [12, 14, 62, 12, 12] },
  );
  sheetRowCounts.quality = await writeSheet(path.join(BUILD_DIR, "xl", "worksheets", "sheet5.xml"), QUALITY_HEADERS, arrayRows(qualityRows), {
    widths: [12, 14, 62, 20, 22, 18, 22, 22, 24, 14, 12, 12, 12, 12, 14, 18],
  });
  sheetRowCounts.sources = await writeSheet(path.join(BUILD_DIR, "xl", "worksheets", "sheet6.xml"), ["item", "detail"], arrayRows(sourceRows), {
    widths: [24, 120],
  });

  await writeWorkbookParts(sheetRowCounts);
  zipWorkbook();
  await fsp.rm(BUILD_DIR, { recursive: true, force: true });

  console.log(`Saved ${OUTPUT_XLSX}`);
  console.log(JSON.stringify(sheetRowCounts, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
