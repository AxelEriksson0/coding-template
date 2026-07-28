import { execFileSync } from "node:child_process"
import { fileURLToPath } from "node:url"

type DependencyMap = Record<string, string>

const projectRoot = fileURLToPath(new URL("..", import.meta.url))

const run = (command: string, arguments_: string[]): string =>
  execFileSync(command, arguments_, {
    cwd: projectRoot,
    encoding: "utf8",
  })

const runInherited = (command: string, arguments_: string[]): void => {
  execFileSync(command, arguments_, {
    cwd: projectRoot,
    stdio: "inherit",
  })
}

const parseDependencyMap = (value: string, name: string): DependencyMap => {
  const parsed = JSON.parse(value) as unknown

  if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new TypeError(`${name} must be a JSON object`)
  }

  const dependencyMap: DependencyMap = {}

  for (const [dependency, range] of Object.entries(parsed as Record<string, unknown>)) {
    if (typeof range !== "string") {
      throw new TypeError(`${name} entry "${dependency}" must be a string`)
    }

    dependencyMap[dependency] = range
  }

  return dependencyMap
}

const catalog = parseDependencyMap(
  run("yarn", ["config", "get", "catalog", "--json"]),
  "Yarn catalog",
)

if (Object.keys(catalog).length === 0) {
  throw new Error("Yarn catalog must not be empty")
}

const upgrades = parseDependencyMap(
  run("npx", [
    "--yes",
    "npm-check-updates",
    "--packageData",
    JSON.stringify({ dependencies: catalog }),
    "--jsonUpgraded",
    "--packageManager",
    "yarn",
  ]),
  "npm-check-updates output",
)

for (const dependency of Object.keys(upgrades)) {
  if (!(dependency in catalog)) {
    throw new Error(`Unexpected dependency returned: "${dependency}"`)
  }
}

const updatedCatalog = Object.fromEntries(
  Object.entries({ ...catalog, ...upgrades }).sort(([left], [right]) => left.localeCompare(right)),
)

if (Object.keys(upgrades).length === 0) {
  process.stdout.write("Catalog dependencies are already up to date.\n")
} else {
  runInherited("yarn", ["config", "set", "catalog", "--json", JSON.stringify(updatedCatalog)])
}
