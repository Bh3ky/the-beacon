import assert from "node:assert/strict";
import { test } from "node:test";

import { safeRedirectPath } from "./safe-redirect.ts";

test("keeps normal on-site paths, including query and hash", () => {
  assert.equal(safeRedirectPath("/post/1/hello?sort=new#c"), "/post/1/hello?sort=new#c");
  assert.equal(safeRedirectPath("/"), "/");
});

test("falls back to / when there is no value", () => {
  assert.equal(safeRedirectPath(undefined), "/");
  assert.equal(safeRedirectPath(null), "/");
  assert.equal(safeRedirectPath(""), "/");
});

test("rejects every way of leaving the site", () => {
  for (const evil of [
    "https://evil.com",
    "//evil.com",
    "/\\evil.com",
    "/\t/evil.com",
    "javascript:alert(1)",
    "evil.com",
  ]) {
    assert.equal(safeRedirectPath(evil), "/", `should reject ${JSON.stringify(evil)}`);
  }
});
