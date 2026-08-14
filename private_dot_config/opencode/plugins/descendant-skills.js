import { createHash } from "node:crypto";
import {
  lstat,
  mkdir,
  readdir,
  readlink,
  rmdir,
  stat,
  symlink,
  unlink,
} from "node:fs/promises";
import { join } from "node:path";

const prunedDirectories = new Set([
  ".git",
  ".hg",
  ".svn",
  "node_modules",
  ".venv",
  "venv",
  "vendor",
  "dist",
  "build",
  "target",
  ".terraform",
  ".cache",
  "__pycache__",
]);

const skillParents = new Set([".opencode", ".agents"]);
const skillDirectories = new Set(["skill", "skills"]);
const projectionDirectory = ".descendant-skills";

async function discoverSkillRoots(directory) {
  const roots = [];
  const rootDevice = (await stat(directory)).dev;

  async function walk(current, depth) {
    let entries;

    try {
      entries = await readdir(current, { withFileTypes: true });
    } catch {
      return;
    }

    for (const entry of entries) {
      if (!entry.isDirectory() || prunedDirectories.has(entry.name)) continue;

      const child = join(current, entry.name);
      let childStat;

      try {
        childStat = await stat(child);
      } catch {
        continue;
      }

      if (childStat.dev !== rootDevice) continue;

      if (depth > 0 && skillParents.has(entry.name)) {
        for (const skillDirectory of skillDirectories) {
          const skillRoot = join(child, skillDirectory);

          try {
            const skillRootStat = await stat(skillRoot);
            if (skillRootStat.dev === rootDevice && skillRootStat.isDirectory()) {
              roots.push(skillRoot);
            }
          } catch {
            // Missing or unreadable skill roots do not block other discovery.
          }
        }

        continue;
      }

      await walk(child, depth + 1);
    }
  }

  await walk(directory, 0);
  return roots.sort();
}

function projectionName(root) {
  return createHash("sha256").update(root).digest("hex").slice(0, 16);
}

async function projectSkillRoots(directory, roots) {
  const projected = join(
    directory,
    ".opencode",
    "skills",
    projectionDirectory,
  );

  if (roots.length === 0) {
    try {
      const entries = await readdir(projected, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.isSymbolicLink()) await unlink(join(projected, entry.name));
      }
      await rmdir(projected);
    } catch {
      // A missing, non-empty, or user-modified projection needs no cleanup.
    }
    return;
  }

  await mkdir(projected, { recursive: true });
  const expected = new Map(
    roots.map((root) => [projectionName(root), root]),
  );
  const entries = await readdir(projected, { withFileTypes: true });

  for (const entry of entries) {
    const path = join(projected, entry.name);
    const target = expected.get(entry.name);

    if (!entry.isSymbolicLink()) continue;

    if (!target || (await readlink(path)) !== target) {
      await unlink(path);
    } else {
      expected.delete(entry.name);
    }
  }

  for (const [name, root] of expected) {
    const path = join(projected, name);

    try {
      await lstat(path);
    } catch {
      await symlink(root, path, "dir");
    }
  }
}

export default async function descendantSkills({ directory }) {
  const discovered = await discoverSkillRoots(directory);
  await projectSkillRoots(directory, discovered);

  return {
    config: async (config) => {
      if (discovered.length === 0) return;

      config.skills ??= {};
      config.skills.paths = [
        ...new Set([...(config.skills.paths ?? []), ...discovered]),
      ];
    },
  };
}
