import { existsSync } from 'node:fs'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { homedir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { type GlobalConfig, GlobalConfigSchema, parseArk } from './schema/index.js'

export function getGlobalConfigPath() {
  const override =
    process.env.CLAWHUB_CONFIG_PATH?.trim() ?? process.env.CLAWDHUB_CONFIG_PATH?.trim()
  if (override) return resolve(override)
  const home = homedir()
  if (process.platform === 'darwin') {
    const clawhubPath = join(home, 'Library', 'Application Support', 'clawhub', 'config.json')
    const clawdhubPath = join(home, 'Library', 'Application Support', 'clawdhub', 'config.json')
    if (existsSync(clawhubPath)) return clawhubPath
    if (existsSync(clawdhubPath)) return clawdhubPath
    return clawhubPath
  }
  const xdg = process.env.XDG_CONFIG_HOME
  if (xdg) {
    const clawhubPath = join(xdg, 'clawhub', 'config.json')
    const clawdhubPath = join(xdg, 'clawdhub', 'config.json')
    if (existsSync(clawhubPath)) return clawhubPath
    if (existsSync(clawdhubPath)) return clawdhubPath
    return clawhubPath
  }
  if (process.platform === 'win32') {
    const appData = process.env.APPDATA
    if (appData) {
      const clawhubPath = join(appData, 'clawhub', 'config.json')
      const clawdhubPath = join(appData, 'clawdhub', 'config.json')
      if (existsSync(clawhubPath)) return clawhubPath
      if (existsSync(clawdhubPath)) return clawdhubPath
      return clawhubPath
    }
  }
  const clawhubPath = join(home, '.config', 'clawhub', 'config.json')
  const clawdhubPath = join(home, '.config', 'clawdhub', 'config.json')
  if (existsSync(clawhubPath)) return clawhubPath
  if (existsSync(clawdhubPath)) return clawdhubPath
  return clawhubPath
}

export async function readGlobalConfig(): Promise<GlobalConfig | null> {
  try {
    const raw = await readFile(getGlobalConfigPath(), 'utf8')
    const parsed = JSON.parse(raw) as unknown
    return parseArk(GlobalConfigSchema, parsed, 'Global config')
  } catch {
    return null
  }
}

export async function writeGlobalConfig(config: GlobalConfig) {
  const path = getGlobalConfigPath()
  await mkdir(dirname(path), { recursive: true })
  await writeFile(path, `${JSON.stringify(config, null, 2)}\n`, 'utf8')
}
