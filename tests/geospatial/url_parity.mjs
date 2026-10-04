// Copyright (c) 2026 Push
// Prints JSON array of booleans (accepted?) for each vector, using the shipped JS safeUrl.
// Optional argv[2]: path to a JSON vector file (default url_vectors.json).
import { readFileSync } from "node:fs";
import { _test } from "../../integration/geospatial/map_ui.js";
const path = process.argv[2] || new URL("./url_vectors.json", import.meta.url);
const v = JSON.parse(readFileSync(path, "utf8"));
console.log(JSON.stringify(v.map((u) => _test.safeUrl(u) !== "")));
