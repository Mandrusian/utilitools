const n = parseInt(require("fs").readFileSync(0, "utf-8").trim(), 10);
let a = 0, b = 1;
for (let i = 0; i < n; i++) { const t = a; a = b; b = t + b; }
console.log(a);
