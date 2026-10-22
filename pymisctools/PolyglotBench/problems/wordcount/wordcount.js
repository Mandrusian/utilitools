const s = require("fs").readFileSync(0, "utf-8");
console.log(s.trim().split(/\s+/).filter(Boolean).length);
